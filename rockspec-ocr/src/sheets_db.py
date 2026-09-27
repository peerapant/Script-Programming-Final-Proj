import json
from datetime import datetime
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
            ws.append_row(["Timestamp", "User_Email", "Drive_File_ID", "Original_Name", "New_Name", "Magnification", "Status"])
            
        if "OTP_Store" not in existing_tabs:
            ws = self.spreadsheet.add_worksheet(title="OTP_Store", rows=100, cols=5)
            ws.append_row(["email", "otp_code", "expired_at", "is_used"])

    def get_users(self) -> List[Dict[str, Any]]:
        """ดึงข้อมูลผู้ใช้ทั้งหมดแบบ Batch"""
        ws = self.spreadsheet.worksheet("Users")
        return ws.get_all_records()

    def get_transaction_logs(self) -> List[Dict[str, Any]]:
        """ดึง Transaction Logs ทั้งหมดเพื่อนำมาทำ Dual-Key Lookup"""
        ws = self.spreadsheet.worksheet("Transactions_Log")
        return ws.get_all_records()

    def append_transaction_logs_batch(self, logs: List[Dict[str, Any]]):
        """บันทึก Log แบบ Batch (append_rows) ป้องกัน Rate Limit"""
        if not logs:
            return
        ws = self.spreadsheet.worksheet("Transactions_Log")
        rows_to_insert = [
            [
                log.get("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                log.get("User_Email", ""),
                log.get("Drive_File_ID", ""),
                log.get("Original_Name", ""),
                log.get("New_Name", ""),
                log.get("Magnification", ""),
                log.get("Status", "Success")
            ]
            for log in logs
        ]
        ws.append_rows(rows_to_insert)

    def flag_external_renamed(self, file_id: str, current_drive_name: str, email: str):
        """บันทึก Flag เมื่อพบว่าชื่อบน Drive ไม่ตรงกับ Log ล่าสุด"""
        log = [{
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "User_Email": email,
            "Drive_File_ID": file_id,
            "Original_Name": current_drive_name,
            "New_Name": current_drive_name,
            "Magnification": "N/A",
            "Status": "EXTERNAL_RENAMED"
        }]
        self.append_transaction_logs_batch(log)