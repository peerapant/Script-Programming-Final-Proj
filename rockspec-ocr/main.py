import argparse
import json
import os
import sys
import warnings

# ปิดข้อความ Warning ทั้งหมด
warnings.filterwarnings("ignore")
os.environ["PYTHONWARNINGS"] = "ignore"

# 2. โหลด Environment Variables จากไฟล์ .env
from dotenv import load_dotenv

load_dotenv()

# 3. Local Application Imports (โมดูลในโปรเจกต์นี้)
from src.drive_service import GoogleDriveService
from src.email_gateway import EmailGateway
from src.notifier import WebhookNotifier
from src.pipeline import RockSpecCloudPipeline
from src.sheets_db import GoogleSheetsDB

def main():
    parser = argparse.ArgumentParser(description="RockSpec OCR Cloud Execution Entrypoint")
    parser.add_argument("--user_email", type=str, help="Email ผู้ใช้งานที่ต้องการประมวลผลเฉพาะรายบุคคล")
    parser.add_argument("--all_users", action="store_true", help="ประมวลผลผู้ใช้งานทั้งหมดใน DB")
    parser.add_argument("--dry_run", action="store_true", help="จำลองการทำงานโดยไม่เปลี่ยนชื่อไฟล์จริง")
    args = parser.parse_args()

    # ดึงค่า Secrets จาก Environment Variables
    gcp_key_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not gcp_key_json or not spreadsheet_id:
        print("[CRITICAL ERROR] ไม่พบ GCP_SERVICE_ACCOUNT_KEY หรือ SPREADSHEET_ID ใน Environment Variables")
        sys.exit(1)

    try:
        service_account_info = json.loads(gcp_key_json)
    except Exception as e:
        print(f"[CRITICAL ERROR] GCP Service Account JSON Format ไม่ถูกต้อง: {e}")
        sys.exit(1)

    # Initialize Adapters
    sheets_db = GoogleSheetsDB(spreadsheet_id, service_account_info)
    drive_service = GoogleDriveService(service_account_info)
    email_gateway = EmailGateway(smtp_user, smtp_password)

    pipeline = RockSpecCloudPipeline(
        sheets_db=sheets_db,
        drive_service=drive_service,
        email_gateway=email_gateway,
        webhook_url=discord_webhook
    )

    users = sheets_db.get_users()
    if not users:
        print("ไม่พบผู้ใช้งานในระบบ")
        return

    if args.user_email:
        target_users = [u for u in users if u.get("email") == args.user_email and str(u.get("status")).lower() == "active"]
    elif args.all_users:
        target_users = [u for u in users if str(u.get("status")).lower() == "active"]
    else:
        print("กรุณาระบุ --user_email <email> หรือ --all_users")
        return

    print(f"พบผู้ใช้งานที่จะประมวลผลทั้งหมด: {len(target_users)} รายการ")
    
    # เก็บผลสรุปเฉพาะผู้ใช้ที่มีไฟล์เข้ากระบวนการประมวลผลจริง
    active_user_results = []
    for user in target_users:
        summary = pipeline.process_user(user, dry_run=args.dry_run)
        if summary and summary.get("active_folders_count", 0) > 0:
            active_user_results.append(summary)

    # ส่งการแจ้งเตือนสรุปภาพรวมทั้งหมดไปยัง Discord
    if discord_webhook:
        notifier = WebhookNotifier(discord_webhook)
        if active_user_results:
            lines = [f"ประมวลผลผู้ใช้ {len(active_user_results)} บัญชี"]
            for idx, res in enumerate(active_user_results, 1):
                lines.append(f"{idx}. บัญชีผู้ใช้ {res['email']}")
                lines.append(
                    f"ประมวลผล {res['active_folders_count']} โฟลเดอร์ "
                    f"สำเร็จ {res['success_count']} รายการ "
                    f"ไม่สำเร็จ {res['failed_count']} รายการ"
                )
            summary_msg = "\n".join(lines)
            notifier.send_notification(title="Batch Processing Summary", summary=summary_msg)
        else:
            summary_msg = "ไม่พบไฟล์ใหม่ที่ต้องประมวลผลสำหรับผู้ใช้งานทุกบัญชี (ทุกโฟลเดอร์เปลี่ยนชื่อเสร็จสิ้นแล้ว)"
            notifier.send_notification(title="Batch Processing Skipped", summary=summary_msg)


if __name__ == "__main__":
    main()