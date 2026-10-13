from typing import Tuple

from src.sheets_db import GoogleSheetsDB
from src.drive_service import GoogleDriveService
from src.email_gateway import EmailGateway


class UndoService:
    """Business Logic Service สำหรับคืนชื่อไฟล์เดิมบน Google Drive (Undo Operation)

    ใช้สิทธิ์ของ Service Account กลาง (ตัวเดียวกับที่ batch pipeline ใช้เปลี่ยนชื่อไฟล์)
    ไม่ต้องพึ่ง OAuth Refresh Token ของผู้ใช้แต่ละคน เพราะระบบ login ใช้ OTP เท่านั้น
    ไม่มีขั้นตอนขอสิทธิ์ Google Drive จากผู้ใช้เลย
    """

    def __init__(
        self,
        sheets_db: GoogleSheetsDB,
        drive_service: GoogleDriveService,
        email_gateway: EmailGateway,
    ):
        self.db = sheets_db
        self.drive_service = drive_service
        self.email_gw = email_gateway

    def undo_file_rename(self, file_id: str, requesting_user_email: str) -> Tuple[bool, str]:
        """
        ย้อนคืนชื่อไฟล์เดิมบน Google Drive
        
        :param file_id: Drive_File_ID ของไฟล์ภาพที่ต้องการ Undo
        :param requesting_user_email: อีเมลของผู้ใช้ที่ส่งคำสั่ง
        :return: (Status Boolean, Message)
        """
        # 1. ค้นหาข้อมูล Transaction Log จาก DB
        tx = self.db.get_transaction_by_file_id(file_id)
        if not tx:
            return False, "ไม่พบประวัติการเปลี่ยนชื่อของไฟล์นี้ในระบบ"

        owner_email = str(tx.get("User_Email")).strip().lower()
        if owner_email != requesting_user_email.strip().lower():
            return False, "คุณไม่มีสิทธิ์ในการจัดการไฟล์ของผู้ใช้อื่น"

        if str(tx.get("Status")).upper() == "UNDONE":
            return False, "ไฟล์นี้ได้รับการย้อนคืนชื่อเดิม (Undo) ไปแล้ว"

        original_name = tx.get("Original_Name")
        current_new_name = tx.get("New_Name")

        # 2. สั่งเปลี่ยนชื่อกลับเป็น Original_Name บน Google Drive ด้วยสิทธิ์ Service Account
        rename_ok = self.drive_service.rename_file(file_id=file_id, new_name=original_name)
        if not rename_ok:
            return False, "ไม่สามารถเปลี่ยนชื่อไฟล์กลับบน Google Drive ได้ (อาจเนื่องมาจากไฟล์ถูกลบไปแล้ว)"

        # 3. อัปเดตสถานะใน Log เป็น UNDONE
        self.db.update_transaction_status(file_id=file_id, new_status="UNDONE")

        # 4. ส่งอีเมลแจ้งเตือนการ Undo
        html_body = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>🔙 รายงานการคืนชื่อไฟล์เดิม (Undo Successful)</h2>
            <p>เรียนผู้ใช้งาน {owner_email},</p>
            <p>ระบบได้ทำการเปลี่ยนชื่อไฟล์ของคุณกลับเป็นชื่อเดิมเรียบร้อยแล้ว:</p>
            <ul>
                <li><b>ชื่อเดิมที่คืนค่า:</b> <span style="color: green;">{original_name}</span></li>
                <li><b>ชื่อที่เคยเปลี่ยน:</b> <del style="color: red;">{current_new_name}</del></li>
                <li><b>File ID:</b> {file_id}</li>
            </ul>
        </div>
        """
        self.email_gw.send_email(owner_email, f"RockSpec OCR: แจ้งการย้อนคืนชื่อไฟล์ {original_name}", html_body)

        return True, f"คืนชื่อไฟล์เป็น '{original_name}' เรียบร้อยแล้ว"