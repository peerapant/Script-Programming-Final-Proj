import os
import random
import re
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from google_auth_oauthlib.flow import Flow

from src.sheets_db import GoogleSheetsDB
from src.email_gateway import EmailGateway
from src.security import SecurityEngine


class AuthService:
    """Business Logic Service สำหรับตรวจสอบสิทธิ์ผู้ใช้, OTP และ Google OAuth 2.0 Flow"""

    def __init__(
        self, 
        sheets_db: GoogleSheetsDB, 
        email_gateway: EmailGateway, 
        security_engine: SecurityEngine,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None
    ):
        self.db = sheets_db
        self.email_gw = email_gateway
        self.security = security_engine
        self.client_id = client_id or os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")
        
        self.scopes = [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ]

    # ==========================================
    # EMAIL & OTP LOGIC
    # ==========================================

    @staticmethod
    def validate_email(email: str) -> bool:
        """ตรวจสอบรูปแบบอีเมลว่าถูกต้องหรือไม่ (รองรับทุกโดเมน)"""
        if not email:
            return False
        # Regex ตรวจสอบโครงสร้างอีเมลทั่วไปมาตรฐาน [username]@[domain].[tld]
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email.strip().lower()))

    def generate_and_send_otp(self, email: str) -> Tuple[bool, str]:
        """สุ่มรหัส OTP 6 หลัก บันทึกลง Sheets DB และส่งไปยังอีเมลผู้ใช้"""
        if not self.validate_email(email):
            return False, "รูปแบบอีเมลไม่ถูกต้อง กรุณาตรวจสอบอีเมลอีกครั้ง"

        otp_code = f"{random.randint(100000, 999999)}"
        thailand_tz = timezone(timedelta(hours=7))
        expires_at = (datetime.now(thailand_tz) + timedelta(minutes=5)).isoformat()

        # 1. บันทึกลง Tab OTP_Store
        if not self.db.save_otp(email, otp_code, expires_at):
            return False, "ไม่สามารถบันทึกข้อมูล OTP ลงในระบบได้"

        # 2. ส่ง OTP ผ่าน EmailGateway
        html_body = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>รหัสยืนยันเข้าสู่ระบบ RockSpec OCR</h2>
            <p>เรียนผู้ใช้งาน {email},</p>
            <p>รหัส OTP สำหรับเข้าสู่ระบบของคุณคือ:</p>
            <h1 style="color: #2b5797; letter-spacing: 5px;">{otp_code}</h1>
            <p><small>* รหัสนี้จะมีอายุการใช้งาน 5 นาที กรุณาอย่าเปิดเผยรหัสนี้แก่ผู้อื่น</small></p>
        </div>
        """
        success = self.email_gw.send_email(email, "RockSpec OCR - Login OTP Verification", html_body)
        
        if success:
            return True, "ส่งรหัส OTP ไปยังอีเมลของคุณเรียบร้อยแล้ว"
        return False, "ไม่สามารถส่งอีเมล OTP ได้ กรุณาตรวจสอบการตั้งค่า SMTP"

    def verify_otp(self, email: str, otp_code: str) -> bool:
        """ตรวจสอบ OTP ยืนยันตัวตน"""
        return self.db.verify_otp(email, otp_code)

    # ==========================================
    # GOOGLE OAUTH 2.0 LOGIC
    # ==========================================

    def get_google_oauth_url(self, user_email: str) -> str:
        """สร้าง URL สำหรับให้ผู้ใช้กดเพื่อมอบสิทธิ์ (Consent Screen) Reading/Writing Google Drive"""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=user_email
        )
        return authorization_url

    def process_oauth_callback(self, auth_code: str, user_email: str) -> Tuple[bool, str]:
        """นำ Authorization Code ไปแลก Refresh Token และบันทึกเข้ารหัสลง Sheets DB"""
        try:
            client_config = {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            }
            flow = Flow.from_client_config(
                client_config,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials

            if not credentials.refresh_token:
                return False, "ไม่ได้รับ Refresh Token จาก Google กรุณาลบสิทธิ์แอปใน Google Account แล้วลองใหม่อีกครั้ง"

            # เข้ารหัส Refresh Token ผ่าน SecurityEngine
            encrypted_token = self.security.encrypt_token(credentials.refresh_token)

            # ดึง Config เดิมมาอัปเดต
            existing_user = self.db.get_user_by_email(user_email)
            folder_id = existing_user.get("drive_folder_id", "") if existing_user else ""
            sheet_id = existing_user.get("mapping_excel_id", "") if existing_user else ""

            # บันทึกลง Sheets DB
            save_ok = self.db.upsert_user_config(
                email=user_email,
                drive_folder_id=folder_id,
                mapping_excel_id=sheet_id,
                encrypted_refresh_token=encrypted_token,
                status="active"
            )

            if save_ok:
                return True, "เชื่อมต่อสิทธิ์ Google Drive เรียบร้อยแล้ว"
            return False, "เกิดข้อผิดพลาดในการบันทึก Token ลงใน Database"

        except Exception as e:
            return False, f"เกิดข้อผิดพลาดระหว่างแลกเปลี่ยน Token: {e}"