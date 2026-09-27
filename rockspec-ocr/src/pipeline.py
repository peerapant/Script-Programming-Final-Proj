import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

from src.drive_service import GoogleDriveService
from src.sheets_db import GoogleSheetsDB
from src.ocr_processor import ImageOCRProcessor
from src.repository import ExcelMappingRepository
from src.renamer_service import ImageRenamerService
from src.notifier import WebhookNotifier
from src.email_gateway import EmailGateway


class RockSpecCloudPipeline:
    def __init__(
        self, 
        sheets_db: GoogleSheetsDB, 
        drive_service: GoogleDriveService, 
        email_gateway: EmailGateway,
        webhook_url: Optional[str] = None
    ):
        self.sheets_db = sheets_db
        self.drive_service = drive_service
        self.email_gateway = email_gateway
        self.ocr_processor = ImageOCRProcessor()
        self.repo = ExcelMappingRepository()
        self.renamer_service = ImageRenamerService()
        self.notifier = WebhookNotifier(webhook_url)

    def process_user(self, user_info: Dict[str, Any], dry_run: bool = False) -> int:
        email = user_info.get("email")
        base_folder_id = user_info.get("drive_folder_id")
        mapping_excel_id = user_info.get("mapping_excel_id")

        print(f"\n🚀 [PROCESSING USER] {email}")
        print(f"Folder ID: {base_folder_id} | Mapping File ID: {mapping_excel_id}")

        # 1. โหลด Mapping File จาก Drive เข้า Memory
        # Excel Mapping file จะต้องมีคอลัมน์: 
        # วันที่       บันทึกเป็น dd/mm/yyyy      ปีต้องเป็น ค.ศ. หรือ พ.ศ. สื่อถึงชื่อโฟลเดอร์ย่อย (โฟลเดอร์ย่อยจะมีชื่อเป็น ddmmyy)
        # ID        บันทึกเป็น int 1 - 10      ID จะสื่อถึงชื่อไฟล์ภาพตัวอย่างในโฟลเดอร์ย่อย เช่น 1.tif, 1_001.tif, 1_002.tif
        # ชื่อตัวอย่าง  บันทึกเป็น NP1, PK5, PW1   ชื่อตัวอย่างจะถูกใช้ในการตั้งชื่อไฟล์ใหม่ โดยจะมองหาไฟล์ภาพที่มีชื่อขึ้นต้นด้วย ID ในแถวเดียวกัน แล้ววนไปเรื่อยๆ ตามลำดับชื่อไฟล์ เช่น 1.tif, 1_001.tif, 1_002.tif 

        excel_stream = self.drive_service.download_file_to_memory(mapping_excel_id)
        try:
            df = pd.read_excel(excel_stream, engine='openpyxl')
        except Exception:
            excel_stream.seek(0)
            df = pd.read_csv(excel_stream)

        excel_mapping = self.repo.parse_mapping_dataframe(df)

        # 2. โหลด Log ล่าสุดจาก Sheets DB สำหรับ Dual-Key Check
        logs_records = self.sheets_db.get_transaction_logs()
        # สร้าง map: {Drive_File_ID: New_Name}
        logged_file_map = {row["Drive_File_ID"]: row["New_Name"] for row in logs_records if row.get("Drive_File_ID")}

        # เรียง 1.tif, 1_001.tif, 1_002.tif, 2.tif ตามลำดับ
        def natural_sort_key(s: str):
            return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

        # 3. สแกนโฟลเดอร์ย่อยบน Drive
        # ภายในโฟลเดอร์หลักจะมีโฟลเดอร์ย่อยที่มีชื่อเป็น ddmmyy เช่น 010124, 020124, 030124
        # แต่ละโฟลเดอร์ย่อยจะมีไฟล์ภาพที่ต้องการประมวลผล เช่น 1.tif, 1_001.tif, 1_002.tif

        date_folders = self.drive_service.list_subfolders(base_folder_id)
        total_processed = 0
        total_failed = 0
        new_audit_logs = []

        for folder in date_folders:
            folder_name = folder['name']
            folder_id = folder['id']
            folder_norm_date = self.repo.normalize_date(folder_name)

            image_files = self.drive_service.list_image_files(folder_id)
            if not image_files:
                continue

            # เรียงลำดับชื่อไฟล์ภาพตามลำดับธรรมชาติ
            image_files.sort(key=lambda x: natural_sort_key(x['name']))

            # แสดงผลการเริ่มประมวลผลแยกตามโฟลเดอร์ย่อย
            print(f"\n>>> Folder : {folder_name}")

            # ตัวแปรสำหรับติดตามจุด (Point) และการซูม (Zoom) ประจำโฟลเดอร์ย่อย
            sample_point_counts: Dict[str, int] = {}  # เก็บจำนวนจุดสะสมของแต่ละชื่อตัวอย่าง เช่น {"PK5": 2, "PW1": 1}
            current_rock_id = None
            zoom_num = 1
            prev_mag_val = None

            for file_item in image_files:
                file_id = file_item['id']
                filename = file_item['name']

                # --- Dual-Key Logic Check ---
                is_external_renamed, _ = self.renamer_service.check_dual_key_status(
                    file_id, filename, logged_file_map
                )
                if is_external_renamed:
                    print(f"⚠️ [DUAL-KEY DETECTED] พบไฟล์เปลี่ยนชื่อภายนอก: {filename} (ID: {file_id})")
                    self.sheets_db.flag_external_renamed(file_id, filename, email)

                # ดึงตัวเลข Rock ID จากเลขขึ้นต้นของชื่อไฟล์
                temp_filename = filename[len(folder_name):] if filename.startswith(folder_name) else filename
                clean_temp = temp_filename.lstrip('_- ')
                match = re.search(r'^(\d+)', clean_temp) or re.search(r'(\d+)', temp_filename) or re.search(r'(\d+)', filename)

                if not match:
                    continue

                rock_id = self.repo.clean_id(match.group(1))
                rock_name = excel_mapping.get((folder_norm_date, rock_id))

                if not rock_name:
                    print(f"  ⚠️ [SKIP] ไม่พบข้อมูล Mapping ของตัวอย่าง ID: {rock_id} \tสำหรับ {filename:<15} (วันที่ {folder_norm_date})")
                    total_failed += 1
                    continue

                # ดาวน์โหลดรูปภาพเข้า Memory Stream เพื่อรัน OCR
                img_stream = self.drive_service.download_file_to_memory(file_id)
                mag = self.ocr_processor.extract_magnification(img_stream)

                # แปลงค่ากำลังขยายเป็นตัวเลขเพื่อใช้เปรียบเทียบการลดลงของกำลังขยาย
                try:
                    current_mag_val = float(re.sub(r'[^0-9.]', '', str(mag)))
                except (ValueError, TypeError):
                    current_mag_val = 0.0

                # --- ลอจิกคำนวณลำดับจุด (Point) และการซูม (Zoom) ---
                # 1. หากเปลี่ยน ID ใหม่ -> นับเป็นจุดใหม่ถัดไปของตัวอย่างนั้น (สืบต่อจาก ID อื่นที่ชื่อเดียวกันก่อนหน้า)
                # 2. หากยังเป็น ID เดิม แต่กำลังขยายลดลง -> ถือว่าเปลี่ยนไปถ่ายจุดใหม่
                is_new_id = (rock_id != current_rock_id)
                is_mag_dropped = (
                    not is_new_id 
                    and prev_mag_val is not None 
                    and current_mag_val < prev_mag_val
                )

                if is_new_id or is_mag_dropped:
                    # เพิ่มลำดับจุดของชื่อตัวอย่างนี้
                    sample_point_counts[rock_name] = sample_point_counts.get(rock_name, 0) + 1
                    point_num = sample_point_counts[rock_name]
                    zoom_num = 1
                else:
                    # ถ่ายจุดเดิม แต่นับลำดับการซูมเพิ่มขึ้น
                    point_num = sample_point_counts[rock_name]
                    zoom_num += 1

                # อัปเดตสถานะสำหรับเปรียบเทียบในรอบถัดไป
                current_rock_id = rock_id
                prev_mag_val = current_mag_val

                ext = os.path.splitext(filename)[1]

                new_filename = self.renamer_service.generate_new_filename(
                    rock_name, point_num, zoom_num, mag, ext
                )

                # ทำการ Rename บน Google Drive ถ้าไม่ใช่ Dry Run
                if not dry_run and new_filename != filename:
                    success = self.drive_service.rename_file(file_id, new_filename)
                    status_str = "SUCCESS" if success else "FAILED"
                    print(f"  ✏️ [{status_str:<7}] {filename:<15} ➡️   {new_filename:<20} (Mag: {mag}x)")
                else:
                    status_str = "DRY-RUN"
                    print(f"  🔍 [{status_str:<7}] {filename:<15} ➡️   {new_filename:<20} (Mag: {mag}x)")

                total_processed += 1
                new_audit_logs.append({
                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "User_Email": email,
                    "Drive_File_ID": file_id,
                    "Original_Name": filename,
                    "New_Name": new_filename,
                    "Magnification": f"{mag}x",
                    "Status": status_str
                })

        # 5. บันทึก Transaction Log และส่งการแจ้งเตือน
        if not dry_run and new_audit_logs:
            self.sheets_db.append_transaction_logs_batch(new_audit_logs)
            
            summary_msg = f"ประมวลผลเปลี่ยนชื่อไฟล์สำเร็จ **{total_processed}** รายการ ให้แก่ {email}"
            self.notifier.send_notification(title="Batch Processing Completed", summary=summary_msg)
            
            html_body = f"""
            <h3>🗿 RockSpec OCR Processing Report</h3>
            <p>เรียนผู้ใช้งาน {email},</p>
            <p>ระบบได้ประมวลผลเปลี่ยนชื่อไฟล์บน Google Drive ของคุณเรียบร้อยแล้ว จำนวนทั้งหมด <b>{total_processed}</b> รายการ</p>
            <hr>
            <p><small>RockSpec OCR Automated System - GitHub Actions Execution</small></p>
            """
            self.email_gateway.send_email(email, "RockSpec OCR: รายงานสรุปการเปลี่ยนชื่อไฟล์", html_body)

        print(f"\n✅ ประมวลผลสำหรับ {email} สำเร็จทั้งหมด {total_processed} รายการ ไม่สำเร็จ {total_failed} รายการ")
        return total_processed