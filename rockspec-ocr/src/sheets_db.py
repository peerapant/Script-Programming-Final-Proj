import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsDB:
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    def __init__(self, spreadsheet_id: str, service_account_info: Dict[str, Any]):
        creds = Credentials.from_service_account_info(service_account_info, scopes=self.SCOPES)
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(spreadsheet_id)
        self._init_tabs()

    def _init_tabs(self):
        """ตรวจสอบและสร้าง Tab พื้นฐานหากยังไม่มี"""
        existing_tabs = [sheet.title for sheet in self.spreadsheet.worksheets()]
        
        if "Users" not in existing_tabs:
            ws = self.spreadsheet.add_worksheet(title="Users", rows=100, cols=10)
            ws.append_row(["email", "encrypted_refresh_token", "drive_folder_id", "mapping_excel_id", "status"])
            
        if "Transactions_Log" not in existing_tabs:
            ws = self.spreadsheet.add_worksheet(title="Transactions_Log", rows=1000, cols=10)
            ws.append_row(["Timestamp", "User_Email", "Subfolder_Name", "Drive_File_ID", "Original_Name", "New_Name", "Magnification", "Status"])
            
        if "OTP_Store" not in existing_tabs:
            ws = self.spreadsheet.add_worksheet(title="OTP_Store", rows=100, cols=5)
            ws.append_row(["email", "otp_code", "expired_at", "is_used"])

    # ==========================================
    # USER MANAGEMENT METHODS
    # ==========================================

    def get_users(self) -> List[Dict[str, Any]]:
        """ดึงข้อมูลผู้ใช้ทั้งหมดแบบ Batch"""
        ws = self.spreadsheet.worksheet("Users")
        return ws.get_all_records()

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """ดึงข้อมูลผู้ใช้เฉพาะรายบุคคลผ่าน Email"""
        users = self.get_users()
        for user in users:
            if str(user.get("email")).strip().lower() == email.strip().lower():
                return user
        return None

    def upsert_user_config(
        self, 
        email: str, 
        drive_folder_id: str, 
        mapping_excel_id: str, 
        encrypted_refresh_token: Optional[str] = None, 
        status: str = "active"
    ) -> bool:
        """อัปเดต หรือ เพิ่มข้อมูลการตั้งค่าของผู้ใช้ลงใน Tab Users"""
        try:
            ws = self.spreadsheet.worksheet("Users")
            records = ws.get_all_records()
            email_clean = email.strip().lower()
            
            row_index = None
            existing_token = ""

            for i, record in enumerate(records, start=2):  # start=2 เพราะแถว 1 คือ Header
                if str(record.get("email")).strip().lower() == email_clean:
                    row_index = i
                    existing_token = record.get("encrypted_refresh_token", "")
                    break

            token_to_save = encrypted_refresh_token if encrypted_refresh_token is not None else existing_token

            if row_index:
                # Update existing user row
                ws.update_cell(row_index, 1, email_clean)
                ws.update_cell(row_index, 2, token_to_save)
                ws.update_cell(row_index, 3, drive_folder_id)
                ws.update_cell(row_index, 4, mapping_excel_id)
                ws.update_cell(row_index, 5, status)
            else:
                # Append new user row
                ws.append_row([email_clean, token_to_save, drive_folder_id, mapping_excel_id, status])
            return True
        except Exception as e:
            print(f"[ERROR] ไม่สามารถบันทึกข้อมูล User Config ได้: {e}")
            return False

    # ==========================================
    # OTP MANAGEMENT METHODS
    # ==========================================

    def save_otp(self, email: str, otp_code: str, expires_at_iso: str) -> bool:
        """บันทึกรหัส OTP ใหม่ลงใน Tab OTP_Store"""
        try:
            ws = self.spreadsheet.worksheet("OTP_Store")
            ws.append_row([email.strip().lower(), str(otp_code), expires_at_iso, False])
            return True
        except Exception as e:
            print(f"[ERROR] ไม่สามารถบันทึก OTP ได้: {e}")
            return False

    def verify_otp(self, email: str, otp_code: str) -> bool:
        """ตรวจสอบความถูกต้องและหมดอายุของ OTP"""
        try:
            ws = self.spreadsheet.worksheet("OTP_Store")
            records = ws.get_all_records()
            email_clean = email.strip().lower()
            thailand_tz = timezone(timedelta(hours=7))
            now_iso = datetime.now(thailand_tz).isoformat()

            for i, record in enumerate(records, start=2):
                rec_email = str(record.get("email")).strip().lower()
                rec_code = str(record.get("otp_code")).strip()
                is_used = str(record.get("is_used")).upper() in ["TRUE", "1"]
                expired_at = str(record.get("expired_at"))

                if rec_email == email_clean and rec_code == str(otp_code).strip() and not is_used:
                    if expired_at > now_iso:
                        # มาร์กสถานะเป็นใช้แล้ว (is_used = True)
                        ws.update_cell(i, 4, True)
                        return True
            return False
        except Exception as e:
            print(f"[ERROR] เกิดข้อผิดพลาดในการตรวจสอบ OTP: {e}")
            return False

    # ==========================================
    # TRANSACTION LOG & UNDO METHODS
    # ==========================================

    def get_transaction_logs(self) -> List[Dict[str, Any]]:
        """ดึง Transaction Logs ทั้งหมดเพื่อนำมาทำ Dual-Key Lookup"""
        ws = self.spreadsheet.worksheet("Transactions_Log")
        return ws.get_all_records()

    def get_user_transactions(self, email: str) -> List[Dict[str, Any]]:
        """ดึงประวัติ Transactions เฉพาะของผู้ใช้งานรายบุคคล"""
        all_logs = self.get_transaction_logs()
        email_clean = email.strip().lower()
        return [log for log in all_logs if str(log.get("User_Email")).strip().lower() == email_clean]

    def get_transaction_by_file_id(self, file_id: str) -> Optional[Dict[str, Any]]:
        """ค้นหารายการ Transaction ล่าสุดด้วย Drive_File_ID"""
        all_logs = self.get_transaction_logs()
        matching_logs = [log for log in all_logs if str(log.get("Drive_File_ID")) == str(file_id)]
        return matching_logs[-1] if matching_logs else None

    def update_transaction_status(self, file_id: str, new_status: str) -> bool:
        """อัปเดตสถานะ Status ของ Transaction ผ่าน Drive_File_ID (ใช้สำหรับ Undo Engine)"""
        try:
            ws = self.spreadsheet.worksheet("Transactions_Log")
            records = ws.get_all_records()
            
            target_row = None
            for i, record in enumerate(records, start=2):
                if str(record.get("Drive_File_ID")) == str(file_id):
                    target_row = i  # เลือกแถวล่าสุดที่พบ

            if target_row:
                # Column 8 คือ 'Status'
                ws.update_cell(target_row, 8, new_status)
                return True
            return False
        except Exception as e:
            print(f"[ERROR] ไม่สามารถอัปเดตสถานะ Transaction ได้: {e}")
            return False

    def append_transaction_logs_batch(self, logs: List[Dict[str, Any]]):
        """บันทึก Log แบบ Batch (append_rows) ป้องกัน Rate Limit"""
        thailand_tz = timezone(timedelta(hours=7))
        if not logs:
            return
        ws = self.spreadsheet.worksheet("Transactions_Log")
        rows_to_insert = [
            [
                log.get("Timestamp", datetime.now(thailand_tz).strftime("%Y-%m-%d %H:%M:%S")),
                log.get("User_Email", ""),
                log.get("Subfolder_Name", ""),
                log.get("Drive_File_ID", ""),
                log.get("Original_Name", ""),
                log.get("New_Name", ""),
                log.get("Magnification", ""),
                log.get("Status", "SUCCESS")
            ]
            for log in logs
        ]
        ws.append_rows(rows_to_insert)

    def flag_external_renamed(self, file_id: str, subfolder_name: str, current_drive_name: str, email: str):
        """บันทึก Flag เมื่อพบว่าชื่อบน Drive ไม่ตรงกับ Log ล่าสุด"""
        thailand_tz = timezone(timedelta(hours=7))
        log = [{
            "Timestamp": datetime.now(thailand_tz).strftime("%Y-%m-%d %H:%M:%S"),
            "User_Email": email,
            "Subfolder_Name": subfolder_name,
            "Drive_File_ID": file_id,
            "Original_Name": current_drive_name,
            "New_Name": current_drive_name,
            "Magnification": "N/A",
            "Status": "EXTERNAL_RENAMED"
        }]
        self.append_transaction_logs_batch(log)