from typing import Any, Dict, List

from src.sheets_db import GoogleSheetsDB
from src.drive_service import GoogleDriveService
from src.email_gateway import EmailGateway


WEB_UI_URL = "https://rockspec-ocr.fly.dev/"


class UndoService:
    """Business Logic Service สำหรับคืนชื่อไฟล์เดิมบน Google Drive (Undo Operation)

    ใช้สิทธิ์ของ Service Account กลาง (ตัวเดียวกับที่ batch pipeline ใช้เปลี่ยนชื่อไฟล์)
    ไม่ต้องพึ่ง OAuth Refresh Token ของผู้ใช้แต่ละคน เพราะระบบ login ใช้ OTP เท่านั้น
    ไม่มีขั้นตอนขอสิทธิ์ Google Drive จากผู้ใช้เลย

    การ Undo ทำงานเป็น Batch ต่อการกด 1 ครั้ง (เลือก 1 วันที่) ย้อนคืนไฟล์ที่เข้าเงื่อนไขทั้งหมด
    บันทึกสถานะ UNDONE ลง Log ของทุกไฟล์ที่ทำสำเร็จ และส่งอีเมลสรุปผลให้ผู้ใช้เพียงฉบับเดียวต่อการทำงาน 1 ครั้ง
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

    def undo_batch_by_date(
        self,
        requesting_user_email: str,
        undo_date: str,
        transactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        ย้อนคืนชื่อไฟล์ทั้งหมดของผู้ใช้ที่ทำรายการไว้ในวันที่ undo_date (ทำเป็น Batch เดียว)

        :param requesting_user_email: อีเมลของผู้ใช้ที่ส่งคำสั่ง (ใช้ระบุผู้รับอีเมลสรุปผลด้วย)
        :param undo_date: วันที่ต้องการย้อนคืน (รูปแบบเดียวกับที่ตัดมาจาก Timestamp เช่น "2026-10-13")
        :param transactions: ประวัติ Transaction ทั้งหมดของผู้ใช้ (ยังไม่กรองวันที่/สถานะ)
            ปกติมาจาก GoogleSheetsDB.get_user_transactions(email) ซึ่งกรอง User_Email ให้แล้ว
        :return: สรุปผล {success_count, failed_count, total, subfolder_stats}
        """
        target_txs = self._filter_pending_by_date(transactions, undo_date)

        if not target_txs:
            return {"success_count": 0, "failed_count": 0, "total": 0, "subfolder_stats": {}}

        success_count = 0
        failed_count = 0
        subfolder_stats: Dict[str, Dict[str, int]] = {}

        for tx in target_txs:
            file_id = tx.get("Drive_File_ID")
            original_name = tx.get("Original_Name")
            subfolder = tx.get("Subfolder_Name") or "ทั่วไป"
            subfolder_stats.setdefault(subfolder, {"success": 0, "failed": 0})

            # สั่งเปลี่ยนชื่อกลับเป็น Original_Name บน Google Drive ด้วยสิทธิ์ Service Account
            rename_ok = self.drive_service.rename_file(file_id=file_id, new_name=original_name)

            if rename_ok:
                # บันทึก Log ของไฟล์นี้ว่าถูก Undo แล้ว (ทำทุกไฟล์ที่สำเร็จ ไม่ข้ามแม้จะรวมอีเมลเป็นก้อนเดียว)
                self.db.update_transaction_status(file_id=file_id, new_status="UNDONE")
                success_count += 1
                subfolder_stats[subfolder]["success"] += 1
            else:
                failed_count += 1
                subfolder_stats[subfolder]["failed"] += 1

        self._send_batch_undo_email(
            owner_email=requesting_user_email,
            undo_date=undo_date,
            success_count=success_count,
            failed_count=failed_count,
            subfolder_stats=subfolder_stats,
        )

        return {
            "success_count": success_count,
            "failed_count": failed_count,
            "total": len(target_txs),
            "subfolder_stats": subfolder_stats,
        }

    @staticmethod
    def _filter_pending_by_date(transactions: List[Dict[str, Any]], undo_date: str) -> List[Dict[str, Any]]:
        """กรองเฉพาะ Transaction ของวันที่ที่เลือก ที่มี Drive_File_ID และยังไม่เคยถูก Undo ไปก่อน"""
        result = []
        for tx in transactions:
            if str(tx.get("Status", "")).upper() == "UNDONE":
                continue
            ts = str(tx.get("Timestamp", ""))
            date_part = ts.split(" ")[0] if " " in ts else ts
            if date_part == undo_date and tx.get("Drive_File_ID"):
                result.append(tx)
        return result

    def _send_batch_undo_email(
        self,
        owner_email: str,
        undo_date: str,
        success_count: int,
        failed_count: int,
        subfolder_stats: Dict[str, Dict[str, int]],
    ) -> None:
        subfolder_html_list = [
            f"<li><b>โฟลเดอร์ {name}:</b> ย้อนคืนสำเร็จ <span style='color:green;'>{stats['success']}</span> รายการ, "
            f"ไม่สำเร็จ <span style='color:red;'>{stats['failed']}</span> รายการ</li>"
            for name, stats in subfolder_stats.items()
            if (stats["success"] + stats["failed"]) > 0
        ]
        subfolder_details_html = "".join(subfolder_html_list)

        html_body = f"""
        <h3>🔙 RockSpec OCR: รายงานการย้อนคืนชื่อไฟล์ (Undo Report)</h3>
        <p>เรียนผู้ใช้งาน {owner_email},</p>
        <p>ระบบได้ทำการย้อนคืนชื่อไฟล์ของวันที่ <b>{undo_date}</b> เรียบร้อยแล้ว รายละเอียดสรุปมีดังนี้:</p>
        <ul>
            <li><b>ย้อนคืนสำเร็จทั้งหมด:</b> <span style="color:green;">{success_count}</span> รายการ</li>
            <li><b>ไม่สำเร็จทั้งหมด:</b> <span style="color:red;">{failed_count}</span> รายการ</li>
        </ul>
        <h4>📂 รายละเอียดแยกตามโฟลเดอร์ย่อย:</h4>
        <ul>
            {subfolder_details_html}
        </ul>
        <p>🔗 ท่านสามารถตรวจสอบประวัติและรายละเอียดเพิ่มเติมได้ที่หน้าเว็บ UI: <a href="{WEB_UI_URL}">RockSpec OCR Web Application</a></p>
        <hr>
        <p><small>RockSpec OCR Automated System - Undo Operation</small></p>
        """
        self.email_gw.send_email(
            owner_email,
            f"RockSpec OCR: รายงานการย้อนคืนชื่อไฟล์ ({undo_date})",
            html_body,
        )
