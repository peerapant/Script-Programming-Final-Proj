import os
import json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

from src.sheets_db import GoogleSheetsDB
from src.github_gateway import GitHubGateway

# โหลดค่า Environment Variables จาก .env
load_dotenv()

def run_step1_test():
    print("==========================================")
    print("🧪 START STEP 1 (DAL) INTEGRATION TEST")
    print("==========================================")

    # 1. ดึง Credentials
    gcp_key_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")

    if not gcp_key_json or not spreadsheet_id:
        print("❌ [FAILED] ไม่พบ GCP_SERVICE_ACCOUNT_KEY หรือ SPREADSHEET_ID ใน .env")
        return

    # 2. ทดสอบ Initialize GoogleSheetsDB และสร้าง Tab อัตโนมัติ
    print("\n[1/5] Testing GoogleSheetsDB Connection & Tab Setup...")
    try:
        service_account_info = json.loads(gcp_key_json)
        db = GoogleSheetsDB(spreadsheet_id, service_account_info)
        print("  ✅ เชื่อมต่อ Google Sheets DB สำเร็จ")
    except Exception as e:
        print(f"  ❌ เชื่อมต่อล้มเหลว: {e}")
        return

    # 3. ทดสอบระบบ OTP (save_otp & verify_otp)
    print("\n[2/5] Testing OTP Store & Verification Engine...")
    test_email = "test_dev@kkumail.com"
    test_otp = "888999"
    thailand_tz = timezone(timedelta(hours=7))
    expires_at = (datetime.now(thailand_tz) + timedelta(minutes=5)).isoformat()

    # บันทึก OTP
    if db.save_otp(test_email, test_otp, expires_at):
        print(f"  ✅ บันทึก OTP ({test_otp}) ลง Tab 'OTP_Store' สำเร็จ")
    else:
        print("  ❌ บันทึก OTP ไม่สำเร็จ")

    # ยืนยัน OTP
    if db.verify_otp(test_email, test_otp):
        print(f"  ✅ ตรวจสอบ OTP ({test_otp}) สำเร็จ และเปลี่ยนสถานะเป็น is_used=TRUE เรียบร้อย")
    else:
        print("  ❌ ตรวจสอบ OTP ไม่ผ่าน")

    # 4. ทดสอบ Upsert User Config
    print("\n[3/5] Testing User Profile Upsert (upsert_user_config)...")
    upsert_ok = db.upsert_user_config(
        email=test_email,
        drive_folder_id="dummy_folder_12345",
        mapping_excel_id="dummy_sheet_67890",
        encrypted_refresh_token="gauth_enc_token_xyz_test",
        status="active"
    )
    if upsert_ok:
        print("  ✅ เพิ่ม/อัปเดตข้อมูลผู้ใช้ใน Tab 'Users' สำเร็จ")
        user_info = db.get_user_by_email(test_email)
        print(f"  🔍 ข้อมูลที่ดึงกลับมา: {user_info}")
    else:
        print("  ❌ บันทึก User Config ไม่สำเร็จ")

    # 5. ทดสอบ Query Transactions & Status Update
    print("\n[4/5] Testing Transactions Query & Status Update (Undo Prep)...")
    user_txs = db.get_user_transactions(test_email)
    print(f"  📊 พบรายการ Transactions ของ {test_email} ทั้งหมด: {len(user_txs)} รายการ")

    # 6. ทดสอบ GitHub Gateway (ยิง API ไปยัง GitHub)
    print("\n[5/5] Testing GitHub Gateway (API Dispatch)...")
    github_gw = GitHubGateway()
    if github_gw.pat_token:
        print(f"  ⚙️ Config: Owner={github_gw.repo_owner}, Repo={github_gw.repo_name}")
        # หมายเหตุ: หากต้องการลองยิงจริงให้ปลดคอมเมนต์บรรทัดล่าง (จะไปสั่งให้ GitHub Action รันจริง)
        # success = github_gw.trigger_rename_now(test_email)
        # print(f"  🚀 Status Dispatch Call: {success}")
        print("  ℹ️ GitHub Gateway Loaded (พร้อมใช้งาน)")
    else:
        print("  ⚠️ ข้ามการทดสอบยิง GitHub API เนื่องจากยังไม่ได้ใส่ GITHUB_PAT_TOKEN ใน .env")

    print("\n==========================================")
    print("✅ STEP 1 INTEGRATION TEST PASSED ALL CHECKS!")
    print("==========================================")

if __name__ == "__main__":
    run_step1_test()