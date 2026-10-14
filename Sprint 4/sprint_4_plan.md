## เอกสารแผนงาน สถาปัตยกรรม และรายงานผลการทดสอบประจำ Sprint 4

**ชื่อโปรเจกต์:** ระบบประมวลผลและเปลี่ยนชื่อไฟล์ภาพถ่ายกล้องจุลทรรศน์อิเล็กตรอนอัตโนมัติ (SEM Rock Image Renamer / RockSpec OCR)

**วิชา:** CP352301 Script Programming | **ภาคการศึกษา:** 1/2569

**ระยะเวลา:** Sprint 4 (สัปดาห์ที่ 15: Production Web Application, DevOps, CI/CD Deployment & Project Closure)

---

### 1. วัตถุประสงค์และขอบเขตโครงการ (Project Purpose & Scope)

ต่อยอดจากต้นแบบ Streamlit Web UI ใน Sprint 3 โดยปรับสถาปัตยกรรมส่วนหน้าเว็บทั้งหมดให้เป็นแอปพลิเคชันระดับ Production ด้วย FastAPI พร้อม Containerize และ Deploy ขึ้นระบบ Cloud Hosting จริง รวมถึงปิดช่องโหว่ด้านประสบการณ์ผู้ใช้ที่พบใน Sprint 3 (ปัญหา OAuth 2.0 และข้อจำกัดการประมวลผลแบบ Real-time) โดยมีขอบเขตการทำงานใน Sprint 4 ดังนี้:

* ปรับสถาปัตยกรรมส่วนหน้าเว็บจาก Streamlit (Sprint 3) มาเป็น **FastAPI + Jinja2 Template Engine** พร้อม Static Assets (`templates/`, `static/`) และ `SessionMiddleware` สำหรับจัดการ Session ผู้ใช้
* ออกแบบระบบ Login ใหม่ทั้งหมดจาก Google OAuth 2.0 รายบุคคล (Sprint 3) มาเป็น **ระบบ OTP ยืนยันตัวตนผ่านอีเมล 6 หลัก** เพื่อลดความซับซ้อนของผู้ใช้ปลายทาง โดยให้สิทธิ์การอ่าน/เปลี่ยนชื่อไฟล์ทำผ่าน Service Account กลางแทนการขอสิทธิ์ Google Drive รายบุคคล
* พัฒนาแดชบอร์ดจัดการโฟลเดอร์ (หน้า Home และ Folder Detail) พร้อมระบบลงทะเบียนลิงก์ Google Drive Folder และ Google Sheet ผ่าน **URL Parser** ที่สกัด ID อัตโนมัติจากลิงก์ที่ผู้ใช้วาง
* สร้างระบบ **Undo ย้อนคืนชื่อไฟล์แบบ Batch ตามวันที่** พร้อมหน้าต่างพรีวิวไฟล์ก่อนยืนยัน และอีเมลสรุปผลหลังดำเนินการ
* เชื่อมปุ่ม **"เปลี่ยนชื่อตอนนี้"** บนหน้าเว็บเข้ากับ GitHub Actions ผ่าน REST API (`workflow_dispatch`) เพื่อสั่งรัน Batch Pipeline แบบ On-Demand ได้ทันทีโดยไม่ต้องรอรอบ Cron Job
* Containerize เว็บแอปด้วย **Docker** (แยก `requirements-web.txt` ออกจาก Dependency ของ Batch Pipeline) และ Deploy ขึ้น **Fly.io** พร้อมตั้งค่า CI/CD อัตโนมัติ (`.github/workflows/deploy_web.yml`)
* ปรับปรุง Workflow เดิมจาก Sprint 2 (`auto_rename.yml`) ให้รองรับ Input สำหรับสั่งรันแบบ On-Demand จากเว็บ และเพิ่มการแจ้งเตือนสรุปผลผ่าน **Discord Webhook** (`notifier.py`)
* สรุปปิดโครงการ (Project Wrap-up): ทดสอบระบบแบบ End-to-End ครบทุกองค์ประกอบตั้งแต่ Sprint 1-4 และจัดทำคู่มือการใช้งาน (`how_to_use.html`) ฉบับสมบูรณ์สำหรับผู้ใช้งานจริง

---

### 2. สถาปัตยกรรมระบบ (Modular Architecture & Separation of Concerns)

โครงสร้างระบบถูกขยายและปรับปรุงให้เป็น Production-Grade Web Service ที่สมบูรณ์ โดยยังคงใช้ Data Access Layer และ Business Logic Layer หลักจาก Sprint 2 ร่วมกันทั้งฝั่งเว็บและฝั่ง Batch Pipeline:

```text
┌────────────────────────────────────────────────────────────────────────┐
│              MODULE 4: PRESENTATION LAYER (PRODUCTION WEB UI)          │
│  - app.py (FastAPI ASGI App, SessionMiddleware, Jinja2Templates)       │
│  - templates/ (login.html, home.html, folder_detail.html, how_to_use)  │
│  - static/style.css (Kanit Font, Vibrant Card & Pill Button UI)        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│          MODULE 5: AUTHENTICATION LAYER (EMAIL OTP, NO OAUTH)          │
│  - auth_service.py (Generate/Verify OTP 6 หลัก, หมดอายุ 5 นาที)          │
│  - Central Service Account Model (ผู้ใช้แชร์สิทธิ์ Editor ให้ Bot แทน      │
│    การขอสิทธิ์ OAuth รายบุคคล)                                           │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│          MODULE 6: FOLDER MANAGEMENT & UNDO OPERATIONS LAYER           │
│  - url_parser.py (สกัด Drive Folder ID / Sheet ID จากลิงก์ที่ผู้ใช้วาง)     │
│  - undo_service.py (Batch Undo ตามวันที่ + อีเมลสรุปผล)                  │
│  - github_gateway.py (Trigger GitHub Actions ผ่าน REST API Dispatch)   │
│  - notifier.py (ส่งสรุปผล Batch Pipeline ผ่าน Discord Webhook)          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│        MODULE 7: DEVOPS & CI/CD DEPLOYMENT INFRASTRUCTURE              │
│  - Dockerfile / .dockerignore (Lean Image เฉพาะ Dependency ฝั่งเว็บ)     │
│  - fly.toml / Procfile (Fly.io Hosting, Auto Start/Stop Machines)      │
│  - .github/workflows/deploy_web.yml (Auto Deploy ขึ้น Fly.io)          │
│  - .github/workflows/auto_rename.yml (ปรับ Cron + On-Demand Dispatch) │
└────────────────────────────────────────────────────────────────────────┘

```

*(ทั้งหมดนี้ยังคงเรียกใช้ MODULE 1 DATA ACCESS LAYER และ MODULE 2 BUSINESS LOGIC LAYER ชุดเดิมที่สร้างไว้ตั้งแต่ Sprint 2 เป็นแกนกลางร่วมกัน)*

---

### 3. นิยามความเสร็จสมบูรณ์ของงาน (Definition of Done - DoD)

งานใน Sprint 4 ถือว่าเสร็จสมบูรณ์ (Done) เมื่อผ่านเกณฑ์ต่อไปนี้ทุกข้อ:

* [x] **FastAPI Web Application Migration:** ย้ายส่วนติดต่อผู้ใช้จาก Streamlit มาเป็น FastAPI + Jinja2 พร้อมแยกไฟล์ `templates/` และ `static/` อย่างเป็นระเบียบ รองรับการรันจริงด้วย `uvicorn`
* [x] **OTP Email Login System:** ผู้ใช้สามารถเข้าสู่ระบบด้วยอีเมลและรหัส OTP 6 หลักที่หมดอายุใน 5 นาที โดยไม่ต้องผ่านขั้นตอน Google OAuth Consent Screen อีกต่อไป
* [x] **Folder Registration Dashboard:** หน้า Home รองรับการลงทะเบียนลิงก์ Google Drive Folder และ Google Sheet ผ่าน `URLParser` พร้อมแสดงรายการโฟลเดอร์ที่ลงทะเบียนไว้แบบ Unique
* [x] **Undo Batch System:** หน้า Folder Detail มี Modal เลือกวันที่ย้อนคืนชื่อไฟล์ พรีวิวตัวอย่างไฟล์ก่อนยืนยัน และส่งอีเมลสรุปผลหลังดำเนินการ
* [x] **On-Demand GitHub Actions Trigger:** ปุ่ม "เปลี่ยนชื่อตอนนี้" สั่งรัน Workflow `auto_rename.yml` ผ่าน GitHub REST API (`workflow_dispatch`) ได้สำเร็จ แก้ไขข้อจำกัด Real-time ที่พบใน Sprint 3
* [x] **Docker Containerization:** สร้าง `Dockerfile` ที่ใช้ `requirements-web.txt` เฉพาะ Dependency ของเว็บแอป (ไม่รวม `torch`/`easyocr`/`opencv`) ทำให้ Image มีขนาดเล็กและ Build เร็ว
* [x] **Fly.io Deployment & CI/CD:** Deploy เว็บแอปขึ้น Fly.io สำเร็จผ่าน `.github/workflows/deploy_web.yml` ที่ทำงานอัตโนมัติเมื่อมีการ Push โค้ดที่เกี่ยวข้องเข้า Branch `main`
* [x] **Discord Webhook Notification:** Batch Pipeline ส่งสรุปผลการประมวลผล (จำนวนผู้ใช้/สำเร็จ/ไม่สำเร็จ) เข้า Discord Channel ผ่าน `notifier.py` ได้ถูกต้องทุกรอบการรัน
* [x] **Project Closure Regression Test:** ทดสอบระบบ End-to-End ครบทุกองค์ประกอบของโครงการ (Sprint 1-4) และปรับปรุงคู่มือการใช้งาน (`how_to_use.html`) ให้ครบถ้วนพร้อมส่งมอบ

---

### 4. แผนการจัดสรรหน้าที่และบทบาทภายในทีม (Team Roles & Responsibilities)

| บทบาท (Role) | สมาชิกที่รับผิดชอบ | ภารกิจหลักใน Sprint 4 |
| --- | --- | --- |
| **Planner / Team Leader** | พีรพล พรหมมิ | • ออกแบบสถาปัตยกรรมเว็บแอป Production (FastAPI) และระบบ Authentication แบบ OTP<br>• วางแผนโครงสร้าง Docker Image และ CI/CD Deployment Pipeline บน Fly.io<br>• จัดทำเอกสารสรุปแผนงานและปิดโครงการภาพรวมทั้ง 4 Sprint |
| **Coder** | ธนธรณ์ ผาลัง | • พัฒนา `app.py`, `templates/`, `static/style.css` และโมดูล `auth_service.py`, `undo_service.py`, `url_parser.py`, `github_gateway.py`, `notifier.py`<br>• เขียน `Dockerfile`, `.dockerignore`, `fly.toml`, `Procfile` และปรับปรุง `.github/workflows/auto_rename.yml` ให้รองรับ On-Demand Trigger |
| **Debugger / QA** | ธนธรณ์ ผาลัง | • ทดสอบ Deploy จริงบน Fly.io และตรวจสอบ CI/CD Pipeline (`deploy_web.yml`)<br>• ทดสอบ OTP Login, Undo System และปุ่ม On-Demand Trigger แบบ End-to-End<br>• ทำ Regression Test รวบยอดทั้งโครงการก่อนส่งมอบ |

---

### 5. ผลการทดสอบระบบและตารางขอบเขตระบบ (QA Testing & Edge Cases Results)

ผู้ทดสอบ (ธนธรณ์ - Debugger / QA) ได้ทำการทดสอบระบบเว็บแอป Production บน **Fly.io** และ CI/CD Pipeline ที่เกี่ยวข้อง โดยมีผลการทดสอบดังนี้:

| ลำดับ | กรณีทดสอบ (Test Case) | อินพุตนำเข้า (Test Input) | พฤติกรรมที่คาดหวัง vs ผลการทดสอบจริง | สถานะ (Status) |
| --- | --- | --- | --- | --- |
| **1** | **OTP Login Flow แบบเต็มรูปแบบ** | กรอกอีเมล → กดขอรหัส OTP → กรอกรหัส 6 หลัก (Auto-Advance/Paste) | ระบบส่งอีเมล OTP ภายใน 5 นาที ตรวจสอบรหัสถูกต้องแล้ว Redirect เข้าหน้า `/home` สำเร็จ ปุ่ม "เปลี่ยนอีเมล" และ "ส่งรหัสใหม่" ทำงานถูกต้อง | **PASSED** |
| **2** | **URL Parser สกัด ID จากลิงก์หลายรูปแบบ** | ลิงก์ Drive Folder และ Sheet ที่มี `/u/0/`, Query String ต่อท้าย หรือ ID ดิบ | `extract_drive_folder_id()` และ `extract_spreadsheet_id()` สกัด ID ได้ถูกต้องครบทุกรูปแบบ และแจ้งเตือนเมื่อกรอกลิงก์ผิดรูปแบบ | **PASSED** |
| **3** | **Folder Detail & Subfolder Listing** | คลิกโฟลเดอร์ที่ลงทะเบียนไว้จากหน้า Home | ระบบดึงชื่อโฟลเดอร์หลัก รายชื่อโฟลเดอร์ย่อย และไฟล์ภาพภายในจาก Google Drive มาแสดงผลถูกต้องครบถ้วน | **PASSED** |
| **4** | **On-Demand Rename Trigger** | กดปุ่ม "เปลี่ยนชื่อตอนนี้" บนหน้า Folder Detail | `GitHubGateway.trigger_rename_now()` ยิง `workflow_dispatch` ไปยัง `auto_rename.yml` สำเร็จ (Response 204) ระบบประมวลผลเบื้องหลังโดยผู้ใช้ไม่ต้องรอ Cron Job | **PASSED** |
| **5** | **Undo Batch by Date** | เลือกวันที่จาก Modal และยืนยันย้อนคืนชื่อไฟล์ | ระบบย้อนคืนชื่อไฟล์ทุกรายการของวันนั้นกลับเป็นชื่อเดิม บันทึกสถานะ `UNDONE` ลง Log และส่งอีเมลสรุปผลสำเร็จ/ไม่สำเร็จแยกตามโฟลเดอร์ย่อย | **PASSED** |
| **6** | **Docker Build & Local Container Run** | `docker build` ด้วย `requirements-web.txt` แล้วรันด้วย `uvicorn app:app --port 8080` | Image Build สำเร็จโดยไม่ดึง `torch`/`easyocr`/`opencv` เข้ามา ขนาด Image เล็กลงอย่างมีนัยสำคัญ เว็บแอปทำงานได้ปกติที่พอร์ต 8080 | **PASSED** |
| **7** | **Fly.io Deployment ผ่าน CI/CD** | Push โค้ดที่แก้ไข `app.py`/`templates`/`static` เข้า Branch `main` | `.github/workflows/deploy_web.yml` ทำงานอัตโนมัติ เรียก `flyctl deploy --remote-only` ด้วย `FLY_API_TOKEN` จาก GitHub Secrets และ Deploy สำเร็จ | **PASSED** |
| **8** | **Discord Webhook Notification** | รัน `main.py --all_users` ให้ครบ 1 รอบ Batch Pipeline | `WebhookNotifier` ส่งสรุปผล (จำนวนผู้ใช้ จำนวนไฟล์สำเร็จ/ไม่สำเร็จ) เข้า Discord Channel ผ่าน Webhook URL ได้ถูกต้อง สถานะ Response 204 | **PASSED** |
| **9** | **Regression: auto_rename.yml หลังปรับปรุง** | ปรับ Cron จากทุก 6 ชั่วโมง (Sprint 2) เป็นวันละ 1 ครั้ง และเพิ่ม Input `user_email`/`dry_run` | Workflow เดิมยังรันผ่าน `pytest` และ Batch Pipeline ได้ปกติ ไม่กระทบ Test Case ที่ผ่านมาจาก Sprint 2 | **PASSED** |

---

### 6. สรุปบทเรียนประจำ Sprint (Sprint Retrospective)

### 🌟 Wow! (จุดเด่นที่ทำได้ดีมาก)

1. **Lean Docker Image & Auto-Scale-to-Zero:** การแยก `requirements-web.txt` ออกจาก Dependency หนักของ Batch Pipeline (`torch`, `easyocr`, `opencv`) ร่วมกับการตั้งค่า `auto_stop_machines` / `min_machines_running = 0` บน Fly.io ช่วยลดต้นทุน Hosting และเวลา Build/Deploy ได้อย่างมาก
2. **OTP Login ลดความซับซ้อนกว่า OAuth อย่างชัดเจน:** การเปลี่ยนจาก OAuth 2.0 รายบุคคล (Sprint 3) มาเป็น OTP ผ่านอีเมลคู่กับ Service Account กลาง ทำให้ตัดปัญหา `Error 401: invalid_client` และขั้นตอน Google Verification ที่ซับซ้อนออกไปทั้งหมด ผู้ใช้ทั่วไปเข้าสู่ระบบได้ในไม่กี่คลิก
3. **สะพานเชื่อม Web-to-CI/CD แบบไร้รอยต่อ:** `GitHubGateway` ที่เชื่อมปุ่มบนเว็บเข้ากับ `workflow_dispatch` ของ GitHub Actions โดยตรง แก้ข้อจำกัด "ต้องรอรอบ Cron Job" ที่บันทึกไว้ใน Retrospective ของ Sprint 3 ได้สำเร็จ โดยไม่ต้องเปลี่ยนสถาปัตยกรรม Batch Pipeline เดิมเลย

---

### 💡 Whoops! (ปัญหาที่พบและแนวทางการแก้ไข)

1. **ปัญหาการเปิดเว็บช้า ในช่วงเริ่มต้น:**
* *ปัญหา:* การทดลอง Build Docker Image ครั้งแรกใช้ `requirements.txt` ตัวเดียวกับ Batch Pipeline ทำให้ดึง `torch`, `easyocr`, `opencv-python` เข้ามาด้วย ส่งผลให้ Image มีขนาดใหญ่เกินความจำเป็นสำหรับเว็บแอปที่ไม่ได้ทำ OCR โดยตรง
* *แนวทางแก้ไข:* แยกไฟล์ `requirements-web.txt` เฉพาะ Dependency ของ FastAPI/Jinja2/Google API และเพิ่ม `.dockerignore` กรองไฟล์ `main.py`, `requirements.txt`, `tests/`, `.github/` ออกจาก Build Context

2. **ความถี่ Cron Job ของ Batch Pipeline ไม่สอดคล้องกับพฤติกรรมผู้ใช้จริง:**
* *ปัญหา:* รอบเวลาทุก 6 ชั่วโมงจาก Sprint 2 ถี่เกินความจำเป็นเมื่อเทียบกับปริมาณไฟล์ที่ผู้ใช้อัปโหลดจริงต่อวัน ทำให้สิ้นเปลือง Runner Minutes โดยไม่จำเป็น
* *แนวทางแก้ไข:* ปรับ Cron Schedule ใน `auto_rename.yml` เป็นวันละ 1 ครั้ง (`0 0 * * *` เวลา 07:00 น. ไทย) และชดเชยด้วยปุ่ม "เปลี่ยนชื่อตอนนี้" บนเว็บสำหรับกรณีที่ผู้ใช้ต้องการผลลัพธ์ทันที

---

# เกณฑ์การประเมินบทบาท (Evaluation Criteria)

---

## 1. เกณฑ์การประเมินบทบาท Planner (นักวางแผนและสถาปนิก)

| หัวข้อการประเมิน | ระดับปรับปรุง (1-2 คะแนน) | ระดับดี (3-4 คะแนน) | ระดับดีเยี่ยม (5 คะแนน) | คะแนนเต็ม |
| :--- | :--- | :--- | :--- | :---: |
| **การวางแผนและกำหนดขอบเขตงาน** | ขาดการระบุข้อกำหนดที่ชัดเจน ทำให้ Coder ไม่สามารถเริ่มงานได้ทันที | กำหนดโครงสร้างงานและฟีเจอร์พื้นฐานได้ แต่ขาดรายละเอียดบางส่วน | วางสเปกต์งานครอบคลุม รายละเอียด ชัดเจน Coder นำไปพัฒนาต่อได้ทันที | 5 |
| **การนิยาม Definition of Done (DoD)** | ไม่มีการกำหนดเงื่อนไขความเสร็จสมบูรณ์ของงาน | กำหนด DoD สำหรับฟีเจอร์หลัก แต่ไม่ได้ครอบคลุมเคสขอบเขต | กำหนด DoD ชัดเจน ครอบคลุมทั้งการทำงานปกติและพฤติกรรมเมื่อเกิดข้อผิดพลาด | 5 |
| **การจัดทำเอกสารโครงการ** | ไม่มีเอกสารแผนงานหรือระบุในไฟล์ PLAN.md ไม่ครบถ้วน | จัดทำเอกสาร PLAN.md เรียบร้อย เนื้อหาอ่านเข้าใจได้ดี | เอกสารจัดหมวดหมู่เป็นระเบียบ ใช้รูปแบบ Markdown ถูกต้องสมบูรณ์ | 5 |

---

## 2. เกณฑ์การประเมินบทบาท Coder (นักเขียนโค้ด)

| หัวข้อการประเมิน | ระดับปรับปรุง (1-2 คะแนน) | ระดับดี (3-4 คะแนน) | ระดับดีเยี่ยม (5 คะแนน) | คะแนนเต็ม |
| :--- | :--- | :--- | :--- | :---: |
| **การจัดโครงสร้างโค้ดและโมดูล** | โค้ดเขียนรวมเป็นบล็อกเดียว ขาดการแยกฟังก์ชั่น | มีการแยกฟังก์ชั่นพื้นฐาน แต่บางฟังก์ชั่นรับภาระงานมากเกินไป | แยกฟังก์ชั่นชัดเจนตามหลัก Modular (display, input, main) | 5 |
| **การจัดการอินพุตและสถานะโปรแกรม** | โปรแกรมพังเมื่อกรอกข้อมูลผิด หรือไม่สามารถวนลูปรับค่าได้ | ใช้ while loop และ if-elif-else ควบคุมการทำงานได้ดี | ควบคุม Control Flow ได้สมบูรณ์ ใช้ `.strip().lower()` ป้องกันอินพุตเพี้ยน | 5 |
| **มาตรฐานและอ่านง่ายของโค้ด** | ตั้งชื่อตัวแปรไม่สื่อความหมาย ขาดคอมเมนต์ | ตั้งชื่อตัวแปรสื่อความหมาย มีคอมเมนต์ในจุดสำคัญ | โค้ดสะอาด มี Docstring อธิบายฟังก์ชั่น และปฏิบัติตามมาตรฐาน PEP8 | 5 |

---

## 3. เกณฑ์การประเมินบทบาท Debugger (นักทดสอบและประกันคุณภาพ)

| หัวข้อการประเมิน | ระดับปรับปรุง (1-2 คะแนน) | ระดับดี (3-4 คะแนน) | ระดับดีเยี่ยม (5 คะแนน) | คะแนนเต็ม |
| :--- | :--- | :--- | :--- | :---: |
| **การทดสอบเคสขอบเขต (Edge Cases)** | ทดสอบเฉพาะการทำงานปกติไม่ได้ทดสอบอินพุตที่ผิดพลาด | ทดสอบอินพุตผิดพลาดพื้นฐาน เช่น ตัวพิมพ์เล็ก-ใหญ่ | ทดสอบครอบคลุมทุกสภาวะ (ข้อมูลไม่ใช่ตัวเลข, ตัวพิมพ์ผสม, ช่องว่าง) | 5 |
| **การจัดการ Exception Handling** | ไม่มีการใช้ try-except ทำให้โปรแกรมหยุดทำงานเมื่อมี Error | มีการใช้ try-except ValueError ป้องกันโปรแกรมพัง | วางโครงสร้าง try-except ร่วมกับ Nested Loop เพื่อให้กรอกใหม่ได้เรียบร้อย | 5 |
| **การรายงานผลและการส่งมอบงาน** | ไม่จัดทำรายงานสรุปข้อผิดพลาดหรือเปิด PR ไม่เรียบร้อย | รายงานข้อผิดพลาดชัดเจน และสรุป Wow! & Whoops! ได้ดี | เขียนรายงานเปรียบเทียบ Observation/Expected/Actual ได้เป๊ะ พร้อมจัดการ PR สมบูรณ์ | 5 |