import os
import json
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

load_dotenv()

# Local Application Imports (โมดูลในโปรเจกต์นี้)
from src.drive_service import GoogleDriveService
from src.email_gateway import EmailGateway
from src.sheets_db import GoogleSheetsDB
from src.security import SecurityEngine
from src.auth_service import AuthService
from src.undo_service import UndoService
from src.url_parser import URLParser
from src.github_gateway import GitHubGateway

def get_undo_service():
    gcp_key_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    service_account_info = json.loads(gcp_key_json) if gcp_key_json else {}
    db = GoogleSheetsDB(spreadsheet_id, service_account_info)
    drive_service = GoogleDriveService(service_account_info)
    email_gw = EmailGateway(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
    return UndoService(db, drive_service, email_gw)

# 1. ต้องประกาศสร้างตัวแปร app ตรงนี้ก่อนเป็นอันดับแรกสุด
app = FastAPI(title="RockSpec OCR Management System")

# 2. หลังจากนั้นค่อยตั้งค่า Middleware, Mount static และเขียน Route ต่างๆ
app.add_middleware(SessionMiddleware, secret_key=os.getenv("MASTER_ENCRYPTION_KEY", "super-secure-secret-key"))
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.cache = None 

# ฟังก์ชันดึงบริการหลังบ้านแบบ Lazy Initialization
def get_auth_service():
    gcp_key_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    master_key = os.getenv("MASTER_ENCRYPTION_KEY") or SecurityEngine.generate_master_key()
    
    service_account_info = json.loads(gcp_key_json) if gcp_key_json else {}
    db = GoogleSheetsDB(spreadsheet_id, service_account_info)
    email_gw = EmailGateway(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
    security = SecurityEngine(master_key)
    return AuthService(db, email_gw, security)

def get_db():
    gcp_key_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    service_account_info = json.loads(gcp_key_json) if gcp_key_json else {}
    return GoogleSheetsDB(spreadsheet_id, service_account_info)

def get_drive_service():
    gcp_key_json = os.getenv("GCP_SERVICE_ACCOUNT_KEY")
    service_account_info = json.loads(gcp_key_json) if gcp_key_json else {}
    return GoogleDriveService(service_account_info)

def get_github_gateway():
    return GitHubGateway()


@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    """หน้า Login หลัก (เฟสกรอกอีเมล และเฟสกรอก OTP 6 ช่อง)"""
    if request.session.get("user_email"):
        return RedirectResponse(url="/home", status_code=303)
    
    otp_sent = request.session.get("otp_sent", False)
    temp_email = request.session.get("temp_email", "")
    error_msg = request.session.pop("error_msg", None)
    success_msg = request.session.pop("success_msg", None)
    
    return templates.TemplateResponse(request, "login.html", {
        "otp_sent": otp_sent,
        "temp_email": temp_email,
        "error_msg": error_msg,
        "success_msg": success_msg
    })


@app.post("/auth/send-otp")
async def send_otp(request: Request, email: str = Form(...)):
    """เฟส 1: รับอีเมล สุ่มและส่งรหัส OTP"""
    auth_service = get_auth_service()
    clean_email = email.strip().lower()
    ok, msg = auth_service.generate_and_send_otp(clean_email)
    if ok:
        request.session["otp_sent"] = True
        request.session["temp_email"] = clean_email
        request.session["success_msg"] = "ส่งรหัส OTP ไปยังอีเมลของคุณเรียบร้อยแล้ว"
    else:
        request.session["error_msg"] = msg
    return RedirectResponse(url="/", status_code=303)


@app.post("/auth/verify-otp")
async def verify_otp(request: Request, otp_code: str = Form(...)):
    """เฟส 2: ตรวจสอบความถูกต้องของรหัส OTP 6 หลัก"""
    auth_service = get_auth_service()
    temp_email = request.session.get("temp_email", "")
    if auth_service.verify_otp(temp_email, otp_code):
        request.session["user_email"] = temp_email
        request.session.pop("otp_sent", None)
        request.session.pop("temp_email", None)
        return RedirectResponse(url="/home", status_code=303)
    else:
        request.session["error_msg"] = "รหัส OTP ไม่ถูกต้องหรือหมดอายุ กรุณาลองใหม่อีกครั้ง"
        return RedirectResponse(url="/", status_code=303)


@app.post("/auth/reset")
async def reset_auth(request: Request):
    """ปุ่มเปลี่ยนอีเมล: ล้างค่าชั่วคราวและกลับไปเฟสกรอกอีเมลใหม่"""
    request.session.pop("otp_sent", None)
    request.session.pop("temp_email", None)
    return RedirectResponse(url="/", status_code=303)


@app.post("/auth/resend-otp")
async def resend_otp(request: Request):
    """ส่งรหัส OTP ใหม่อีกครั้งไปยังอีเมลเดิม"""
    auth_service = get_auth_service()
    temp_email = request.session.get("temp_email", "")
    if not temp_email:
        return RedirectResponse(url="/", status_code=303)
    
    ok, msg = auth_service.generate_and_send_otp(temp_email)
    if ok:
        request.session["success_msg"] = "ส่งรหัส OTP ใหม่ไปยังอีเมลของคุณเรียบร้อยแล้ว"
    else:
        request.session["error_msg"] = msg
    return RedirectResponse(url="/", status_code=303)

import asyncio

@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """หน้า Home รวมข้อมูลผู้ใช้ รายการโฟลเดอร์ และฟอร์มลงทะเบียนโฟลเดอร์ใหม่"""
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/", status_code=303)
    
    db = get_db()
    drive_service = get_drive_service()
    all_users = db.get_users() or []
    user_records = [u for u in all_users if str(u.get("email", "")).strip().lower() == user_email.strip().lower()]
    
    # ทำ Unique เพื่อให้ได้รายการโฟลเดอร์ที่ไม่ซ้ำกัน
    # 1. ในฟังก์ชัน @app.get("/home") ให้เพิ่ม folder_url เข้าไปใน unique_folders
    unique_folders = {}
    for r in user_records:
        folder_id = r.get("drive_folder_id") or r.get("Folder_ID") or r.get("drive_id")
        sheet_id = r.get("mapping_excel_id") or r.get("Sheet_ID") or r.get("sheet_id")
        if folder_id and folder_id not in unique_folders:
            # 1. ในฟังก์ชัน @app.get("/home") ให้เพิ่ม folder_url เข้าไปใน unique_folders
            folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}" if sheet_id else "#"
            
            folder_name = f"โฟลเดอร์ ({folder_id[:8]}...)"
            try:
                def fetch_drive_name():
                    meta = drive_service.service.files().get(fileId=folder_id, fields='name').execute()
                    return meta.get('name')
                
                actual_name = await asyncio.wait_for(asyncio.to_thread(fetch_drive_name), timeout=3.0)
                if actual_name:
                    folder_name = actual_name
            except Exception:
                pass

            unique_folders[folder_id] = {
                "id": folder_id,
                "name": folder_name,
                "folder_url": folder_url,  # 📌 เพิ่มลิงก์ Drive ของโฟลเดอร์นั้นๆ
                "sheet_url": sheet_url
            }
            
    folders = list(unique_folders.values())
    error_msg = request.session.pop("error_msg", None)
    success_msg = request.session.pop("success_msg", None)
    
    return templates.TemplateResponse(request, "home.html", {
        "user_email": user_email,
        "folders": folders,
        "error_msg": error_msg,
        "success_msg": success_msg
    })

@app.post("/home/add-folder")
async def add_folder(request: Request, sheet_link: str = Form(...), folder_link: str = Form(...)):
    """รับลิงก์ Google Sheet และ Google Drive Folder จากฟอร์มลงทะเบียนโฟลเดอร์ใหม่ สกัด ID แล้วบันทึกลงฐานข้อมูล"""
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/", status_code=303)

    folder_id = URLParser.extract_drive_folder_id(folder_link)
    sheet_id = URLParser.extract_spreadsheet_id(sheet_link)

    if not folder_id or not sheet_id:
        request.session["error_msg"] = "ลิงก์ที่กรอกไม่ถูกต้อง กรุณาตรวจสอบลิงก์ Google Drive Folder และ Google Sheet อีกครั้ง"
        return RedirectResponse(url="/home", status_code=303)

    db = get_db()
    save_ok = db.upsert_user_config(
        email=user_email,
        drive_folder_id=folder_id,
        mapping_excel_id=sheet_id,
    )

    if save_ok:
        request.session["success_msg"] = "ลงทะเบียนโฟลเดอร์ใหม่เรียบร้อยแล้ว"
    else:
        request.session["error_msg"] = "ไม่สามารถบันทึกข้อมูลโฟลเดอร์ได้ กรุณาลองใหม่อีกครั้ง"

    return RedirectResponse(url="/home", status_code=303)


@app.get("/how-to-use", response_class=HTMLResponse)
async def how_to_use_page(request: Request):
    """หน้าวิธีการใช้งาน (How to use)"""
    if not request.session.get("user_email"):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request, "how_to_use.html", {"user_email": request.session.get("user_email")})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/folder-detail/{folder_id}", response_class=HTMLResponse)
async def folder_detail_page(request: Request, folder_id: str):
    """หน้าแสดงรายละเอียดโฟลเดอร์ย่อยและรายชื่อไฟล์ภายในโฟลเดอร์หลัก"""
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/", status_code=303)
    
    db = get_db()
    drive_service = get_drive_service()
    
    # ดึงชื่อโฟลเดอร์หลัก
    folder_name = "รายละเอียดโฟลเดอร์"
    try:
        def get_meta():
            return drive_service.service.files().get(fileId=folder_id, fields='name').execute()
        meta = await asyncio.to_thread(get_meta)
        folder_name = meta.get('name', folder_name)
    except Exception:
        pass
        
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    
    # 📌 [เพิ่มใหม่] ดึงประวัติ Transaction มาจัดกลุ่มตามวันที่ สำหรับระบบ Undo
    user_transactions = db.get_user_transactions(user_email)
    undo_groups = {}
    for tx in user_transactions:
        status = str(tx.get("Status", "")).upper()
        if status == "UNDONE":
            continue
        ts = str(tx.get("Timestamp", ""))
        date_part = ts.split(" ")[0] if " " in ts else ts
        if not date_part:
            continue
            
        subfolder = tx.get("Subfolder_Name", "ทั่วไป")
        if date_part not in undo_groups:
            undo_groups[date_part] = {}
        if subfolder not in undo_groups[date_part]:
            undo_groups[date_part][subfolder] = []
            
        # เก็บตัวอย่างสูงสุด 3 ไฟล์แรกของแต่ละโฟลเดอร์ย่อยในรอบนั้นๆ
        if len(undo_groups[date_part][subfolder]) < 3:
            undo_groups[date_part][subfolder].append({
                "original_name": tx.get("Original_Name"),
                "new_name": tx.get("New_Name")
            })

    # ดึงรายชื่อโฟลเดอร์ย่อยและไฟล์ภาพภายใน
    subfolders_data = []
    try:
        def get_subs():
            return drive_service.list_subfolders(folder_id)
        subfolders_raw = await asyncio.to_thread(get_subs) or []
        
        for sub in subfolders_raw:
            sub_id = sub.get('id')
            sub_name = sub.get('name')
            
            def get_files():
                return drive_service.list_image_files(sub_id)
            files_raw = await asyncio.to_thread(get_files) or []
            file_names = [f.get('name') for f in files_raw]
            
            subfolders_data.append({
                "id": sub_id,
                "name": sub_name,
                "files": file_names
            })
    except Exception:
        pass

    success_msg = request.session.pop("success_msg", None)
    error_msg = request.session.pop("error_msg", None)

    return templates.TemplateResponse(request, "folder_detail.html", {
        "user_email": user_email,
        "folder_name": folder_name,
        "folder_url": folder_url,
        "subfolders": subfolders_data,
        "undo_groups": undo_groups,  # 📌 ส่งข้อมูลกลุ่มวันที่ Undo ไปแสดงที่ UI
        "success_msg": success_msg,
        "error_msg": error_msg
    })

@app.post("/undo/execute")
async def execute_undo_by_date(request: Request, undo_date: str = Form(...)):
    """ดำเนินการย้อนคืนชื่อไฟล์ทั้งหมดในวันที่เลือก"""
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/", status_code=303)
        
    db = get_db()
    undo_service = get_undo_service()
    user_transactions = db.get_user_transactions(user_email)
    
    success_count = 0
    for tx in user_transactions:
        status = str(tx.get("Status", "")).upper()
        if status == "UNDONE":
            continue
        ts = str(tx.get("Timestamp", ""))
        date_part = ts.split(" ")[0] if " " in ts else ts
        if date_part == undo_date:
            file_id = tx.get("Drive_File_ID")
            if file_id:
                ok, msg = undo_service.undo_file_rename(file_id, user_email)
                if ok:
                    success_count += 1
                    
    if success_count > 0:
        request.session["success_msg"] = f"ย้อนคืนชื่อไฟล์ของวันที่ {undo_date} สำเร็จจำนวน {success_count} รายการ"
    else:
        request.session["error_msg"] = "ไม่พบไฟล์ที่สามารถย้อนคืนได้ในวันที่เลือก"
        
    referer = request.headers.get("referer", "/home")
    return RedirectResponse(url=referer, status_code=303)


@app.post("/trigger/rename-now")
async def trigger_rename_now(request: Request):
    """ปุ่ม 'เปลี่ยนชื่อตอนนี้': สั่งให้ GitHub Actions รัน Workflow เปลี่ยนชื่อไฟล์ทันทีแบบ On-Demand"""
    user_email = request.session.get("user_email")
    if not user_email:
        return RedirectResponse(url="/", status_code=303)

    github_gw = get_github_gateway()
    dispatched = github_gw.trigger_rename_now(user_email)

    if dispatched:
        request.session["success_msg"] = "ส่งคำสั่งเปลี่ยนชื่อไฟล์ทันทีเรียบร้อยแล้ว ระบบกำลังประมวลผลอยู่เบื้องหลัง กรุณารอสักครู่แล้วรีเฟรชหน้านี้"
    else:
        request.session["error_msg"] = "ไม่สามารถสั่งรันระบบเปลี่ยนชื่อไฟล์ได้ กรุณาตรวจสอบการตั้งค่า GitHub Actions หรือลองใหม่อีกครั้ง"

    referer = request.headers.get("referer", "/home")
    return RedirectResponse(url=referer, status_code=303)