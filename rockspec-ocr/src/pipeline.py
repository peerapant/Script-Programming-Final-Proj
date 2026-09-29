import os
import re
from datetime import datetime, timedelta, timezone
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

    def process_user(self, user_info: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
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
        
        # แสดงผลใน CLI ว่าพบโฟลเดอร์ย่อยกี่รายการ อะไรบ้าง
        folder_names = [f['name'] for f in date_folders]
        print(f"📁 พบโฟลเดอร์ย่อยทั้งหมด {len(date_folders)} รายการ: {folder_names}")

        total_processed = 0
        total_failed = 0
        new_audit_logs = []
        folder_stats = []
        active_folders_count = 0  # นับเฉพาะจำนวนโฟลเดอร์ย่อยที่มีไฟล์ที่ยังไม่ได้ประมวลผล

        thailand_tz = timezone(timedelta(hours=7))

        for folder in date_folders:
            folder_name = folder['name']
            folder_id = folder['id']
            folder_norm_date = self.repo.normalize_date(folder_name)

            image_files = self.drive_service.list_image_files(folder_id)
            if not image_files:
                continue

            # กรองเฉพาะไฟล์ภาพที่ชื่อไฟล์ (ไม่รวมสกุลไฟล์) ประกอบด้วยตัวเลขและ/หรือ underscore เท่านั้น
            # เช่น 1.tif, 1_001.tif, 1_002.tif, 2.tif
            processable_files = []
            for file_item in image_files:
                fname_no_ext, _ = os.path.splitext(file_item['name'])
                if re.match(r'^\d+(_\d+)*$', fname_no_ext):
                    processable_files.append(file_item)

            # หากไม่พบไฟล์ที่ต้องประมวลผล (เปลี่ยนชื่อเสร็จสิ้นหมดแล้ว หรือไม่มีไฟล์ภาพรูปแบบตัวเลข) ให้ข้ามโฟลเดอร์ย่อยนี้
            if not processable_files:
                print(f"⏩ [SKIP FOLDER] {folder_name} (เปลี่ยนชื่อเสร็จสิ้นแล้ว หรือไม่มีไฟล์ใหม่ที่ต้องประมวลผล)")
                continue

            # นับเฉพาะโฟลเดอร์ที่มีไฟล์เข้ากระบวนการประมวลผล
            active_folders_count += 1

            # เรียงลำดับชื่อไฟล์ภาพตามลำดับธรรมชาติ
            processable_files.sort(key=lambda x: natural_sort_key(x['name']))

            # แสดงผลการเริ่มประมวลผลแยกตามโฟลเดอร์ย่อย
            print(f"\n>>> Folder : {folder_name}")

            # ตัวแปรสำหรับติดตามจุด (Point) และการซูม (Zoom) ประจำโฟลเดอร์ย่อย
            sample_point_counts: Dict[str, int] = {}  # เก็บจำนวนจุดสะสมของแต่ละชื่อตัวอย่าง เช่น {"PK5": 2, "PW1": 1}
            current_rock_id = None
            zoom_num = 1
            prev_mag_val = None

            folder_success_count = 0
            folder_failed_count = 0

            for file_item in processable_files:
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
                fname_no_ext, ext = os.path.splitext(filename)
                match = re.match(r'^(\d+)', fname_no_ext)

                if not match:
                    folder_failed_count += 1
                    total_failed += 1
                    # บันทึกลง Log แม้ว่าจะดึง Rock ID ไม่ได้
                    new_audit_logs.append({
                        "Timestamp": datetime.now(thailand_tz).strftime("%Y-%m-%d %H:%M:%S"),
                        "User_Email": email,
                        "Subfolder_Name": folder_name,
                        "Drive_File_ID": file_id,
                        "Original_Name": filename,
                        "New_Name": filename,
                        "Magnification": "-",
                        "Status": "FAILED"
                    })
                    continue

                rock_id = self.repo.clean_id(match.group(1))
                rock_name = excel_mapping.get((folder_norm_date, rock_id))

                if not rock_name:
                    print(f"  ⚠️ [SKIP] ไม่พบข้อมูล Mapping ของตัวอย่าง ID: {rock_id} \tสำหรับ {filename:<15} (วันที่ {folder_norm_date})")
                    folder_failed_count += 1
                    total_failed += 1
                    # บันทึกลง Log แม้ว่าจะไม่พบข้อมูล Mapping
                    new_audit_logs.append({
                        "Timestamp": datetime.now(thailand_tz).strftime("%Y-%m-%d %H:%M:%S"),
                        "User_Email": email,
                        "Subfolder_Name": folder_name,
                        "Drive_File_ID": file_id,
                        "Original_Name": filename,
                        "New_Name": filename,
                        "Magnification": "-",
                        "Status": "FAILED"
                    })
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

                new_filename = self.renamer_service.generate_new_filename(
                    rock_name, point_num, zoom_num, mag, ext
                )

                # ทำการ Rename บน Google Drive ถ้าไม่ใช่ Dry Run
                if not dry_run and new_filename != filename:
                    success = self.drive_service.rename_file(file_id, new_filename)
                    status_str = "SUCCESS" if success else "FAILED"
                    print(f"  ✏️ [{status_str:<7}] {filename:<15} ➡️   {new_filename:<20} (Mag: {mag}x)")
                    if success:
                        folder_success_count += 1
                        total_processed += 1
                    else:
                        folder_failed_count += 1
                        total_failed += 1
                else:
                    status_str = "DRY-RUN"
                    print(f"  🔍 [{status_str:<7}] {filename:<15} ➡️   {new_filename:<20} (Mag: {mag}x)")
                    folder_success_count += 1
                    total_processed += 1

                new_audit_logs.append({
                    "Timestamp": datetime.now(thailand_tz).strftime("%Y-%m-%d %H:%M:%S"),
                    "User_Email": email,
                    "Subfolder_Name": folder_name,
                    "Drive_File_ID": file_id,
                    "Original_Name": filename,
                    "New_Name": new_filename,
                    "Magnification": f"{mag}x",
                    "Status": status_str
                })

            folder_stats.append({
                "folder_name": folder_name,
                "success": folder_success_count,
                "failed": folder_failed_count
            })

        # หากไม่มีไฟล์ที่ถูกนำมาประมวลผลเลย
        if active_folders_count == 0 or len(new_audit_logs) == 0:
            print(f"\n✨ ทุกโฟลเดอร์สำหรับ {email} ประมวลผลเสร็จสิ้นแล้ว ไม่พบไฟล์ที่ต้องประมวลผลใหม่")
            return {
                "email": email,
                "active_folders_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "total_files": 0
            }

        # 5. บันทึก Transaction Log และส่ง Email แจ้งเตือนเมื่อมีไฟล์ถูกดึงมาประมวลผล
        if not dry_run and new_audit_logs:
            self.sheets_db.append_transaction_logs_batch(new_audit_logs)
            
            folder_html_list = [
                f"<li><b>โฟลเดอร์ {fs['folder_name']}:</b> สำเร็จ <span style='color:green;'>{fs['success']}</span> รายการ, ไม่สำเร็จ <span style='color:red;'>{fs['failed']}</span> รายการ</li>"
                for fs in folder_stats if (fs['success'] + fs['failed']) > 0
            ]
            folder_details_html = "".join(folder_html_list)

            # ส่ง Email ทุกครั้งที่มีการประมวลผลไฟล์ (แม้จะไม่สำเร็จเลยก็ตาม)
            html_body = f"""
            <h3>RockSpec OCR Processing Report</h3>
            <p>เรียนผู้ใช้งาน {email},</p>
            <p>ระบบได้ประมวลผลเปลี่ยนชื่อไฟล์บน Google Drive ของคุณเรียบร้อยแล้ว รายละเอียดสรุปมีดังนี้:</p>
            <ul>
                <li><b>สำเร็จทั้งหมด:</b> <span style="color:green;">{total_processed}</span> รายการ</li>
                <li><b>ไม่สำเร็จทั้งหมด:</b> <span style="color:red;">{total_failed}</span> รายการ</li>
            </ul>
            <h4>📂 รายละเอียดแยกตามโฟลเดอร์ย่อย:</h4>
            <ul>
                {folder_details_html}
            </ul>
            <p>🔗 ท่านสามารถตรวจสอบประวัติและรายละเอียดเพิ่มเติมได้ที่หน้าเว็บ UI: <a href="https://rockspec-ocr.streamlit.app">RockSpec OCR Web Application</a></p>
            <hr>
            <p><small>RockSpec OCR Automated System - GitHub Actions Execution</small></p>
            """
            self.email_gateway.send_email(email, "RockSpec OCR: รายงานสรุปการเปลี่ยนชื่อไฟล์", html_body)

        print(f"\n✅ ประมวลผลสำหรับ {email} สำเร็จทั้งหมด {total_processed} รายการ ไม่สำเร็จ {total_failed} รายการ")

        return {
            "email": email,
            "active_folders_count": active_folders_count,
            "success_count": total_processed,
            "failed_count": total_failed,
            "total_files": len(new_audit_logs)
        }