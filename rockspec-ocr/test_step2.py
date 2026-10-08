import os
import json
from dotenv import load_dotenv

from src.sheets_db import GoogleSheetsDB
from src.email_gateway import EmailGateway
from src.security import SecurityEngine
from src.url_parser import URLParser
from src.auth_service import AuthService
from src.undo_service import UndoService

load_dotenv()

def run_step2_test():
    print("==========================================")
    print("🧪 START STEP 2 (BLL) INTEGRATION TEST")
    print("==========================================")

    # 1. Test URLParser
    print("\n[1/4] Testing URLParser...")
    sample_drive_url = "https://drive.google.com/drive/folders/1A2B3C4D5E6F7G8H9I0J?usp=sharing"
    sample_sheet_url = "https://docs.google.com/spreadsheets/d/1X2Y3Z4W5V6U7T8S9R0Q/edit#gid=0"
    
    extracted_folder_id = URLParser.extract_drive_folder_id(sample_drive_url)
    extracted_sheet_id = URLParser.extract_spreadsheet_id(sample_sheet_url)
    
    print(f"  🔍 Folder ID Extracted: {extracted_folder_id}")
    print(f"  🔍 Sheet ID Extracted:  {extracted_sheet_id}")
    assert extracted_folder_id == "1A2B3C4D5E6F7G8H9I0J", "Folder ID parsing failed!"
    assert extracted_sheet_id == "1X2Y3Z4W5V6U7T8S9R0Q", "Sheet ID parsing failed!"
    print("  ✅ URLParser Passed!")

    # 2. Test KKU Email Validation
    print("\n[2/4] Testing KKU Email Validation...")
    valid_email = "student@kkumail.com"
    invalid_email = "external@gmail.com"
    
    assert AuthService.validate_kku_email(valid_email) == True, "Valid email failed!"
    assert AuthService.validate_kku_email(invalid_email) == False, "Invalid email passed!"
    print("  ✅ Email Validation Passed!")

    # 3. Test Service Initialization
    print("\n[3/4] Testing Services Setup...")
    gcp_key_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    master_key = os.getenv("MASTER_ENCRYPTION_KEY") or SecurityEngine.generate_master_key()

    if not gcp_key_json or not spreadsheet_id:
        print("  ⚠️ ไม่พบ GCP_SERVICE_ACCOUNT_KEY หรือ SPREADSHEET_ID ข้ามการทดสอบ DB Session")
        return

    service_account_info = json.loads(gcp_key_json)
    db = GoogleSheetsDB(spreadsheet_id, service_account_info)
    email_gw = EmailGateway(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
    security = SecurityEngine(master_key)

    auth_service = AuthService(db, email_gw, security)
    undo_service = UndoService(db, security, email_gw)
    print("  ✅ AuthService & UndoService Loaded Successfully!")

    # 4. Test OAuth Authorization URL Generation
    print("\n[4/4] Testing OAuth URL Generation...")
    if auth_service.client_id and auth_service.client_secret:
        oauth_url = auth_service.get_google_oauth_url(valid_email)
        print(f"  🔗 Generated OAuth Consent URL: {oauth_url[:60]}...")
        print("  ✅ OAuth URL Generation Passed!")
    else:
        print("  ⚠️ ข้ามการทดสอบ OAuth URL เนื่องจากยังไม่ได้ตั้งค่า GOOGLE_CLIENT_ID / SECRET ใน .env")

    print("\n==========================================")
    print("✅ STEP 2 INTEGRATION TEST PASSED ALL CHECKS!")
    print("==========================================")

if __name__ == "__main__":
    run_step2_test()