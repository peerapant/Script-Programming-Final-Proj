## Sprint 4 Changelog

### [4.6.0]

### Added

* **Docker Containerization (`Dockerfile`, `.dockerignore`):** เพิ่ม Dockerfile แบบ Multi-Step ที่ติดตั้งเฉพาะ Dependency ของเว็บแอปจาก `requirements-web.txt` คัดลอกเฉพาะ `app.py`, `src/`, `templates/`, `static/` เข้า Image และรันด้วย `uvicorn app:app --host 0.0.0.0 --port 8080`
* **Fly.io Hosting Configuration (`fly.toml`, `Procfile`):** เพิ่มไฟล์คอนฟิก Fly.io ระบุ Region `sin` (Singapore), `internal_port = 8080`, `auto_stop_machines`/`auto_start_machines` และ `min_machines_running = 0` เพื่อประหยัดค่าใช้จ่ายเมื่อไม่มีผู้ใช้งาน พร้อม `Procfile` สำรองสำหรับ Platform ที่รองรับ Procfile
* **Automated Web Deployment Workflow (`.github/workflows/deploy_web.yml`):** เพิ่ม CI/CD Workflow ที่ Deploy เว็บแอปขึ้น Fly.io อัตโนมัติด้วยคำสั่ง `flyctl deploy --remote-only` ทุกครั้งที่มีการ Push เข้า Branch `main` ในพาธที่เกี่ยวข้อง (`app.py`, `src/**`, `templates/**`, `static/**`, `Dockerfile`, `fly.toml` ฯลฯ) พร้อมรองรับ Manual Trigger (`workflow_dispatch`)

### Changed

* **`auto_rename.yml` On-Demand Dispatch Inputs:** ปรับ Workflow เดิมจาก Sprint 2 ให้รับ Input `user_email` และ `dry_run` ผ่าน `workflow_dispatch` เพื่อให้ `GitHubGateway` และ Admin สามารถสั่งรันแบบเจาะจงผู้ใช้หรือทั้งหมดได้จากภายนอก
* **Cron Schedule Adjustment:** ปรับความถี่การรันอัตโนมัติจากทุก 6 ชั่วโมง (Sprint 2) เป็นวันละ 1 ครั้ง (`0 0 * * *` ตรงกับ 07:00 น. เวลาไทย) เพื่อลดการใช้ Runner Minutes โดยไม่จำเป็น เนื่องจากมีปุ่ม On-Demand Trigger ชดเชยแล้ว

### Security

* **Fly.io API Token Isolation:** เก็บ `FLY_API_TOKEN` ไว้ใน GitHub Secrets เท่านั้น ไม่ฝังค่าลงในไฟล์ Workflow หรือซอร์สโค้ดโดยตรง
* **Dockerignore Secret Exclusion:** กำหนด `.dockerignore` ให้กรอง `.env`, `.env.example`, `.git/`, `tests/`, `.github/` ออกจาก Build Context ของ Docker เพื่อป้องกันข้อมูลลับหลุดเข้าไปใน Image

---

### [4.5.0]

### Added

* **On-Demand GitHub Actions Trigger (`github_gateway.py`):** เพิ่มคลาส `GitHubGateway` สำหรับยิง REST API `POST /actions/workflows/auto_rename.yml/dispatches` ไปยัง GitHub พร้อม Endpoint `/trigger/rename-now` ในหน้า Folder Detail ให้ผู้ใช้กดปุ่ม "เปลี่ยนชื่อตอนนี้" เพื่อสั่งประมวลผลทันทีโดยไม่ต้องรอ Cron Job
* **Discord Webhook Notifier (`notifier.py`):** เพิ่มคลาส `WebhookNotifier` ส่งสรุปผลการรัน Batch Pipeline (จำนวนผู้ใช้ จำนวนโฟลเดอร์ สำเร็จ/ไม่สำเร็จ) เข้า Discord Channel ผ่าน Webhook URL ทุกครั้งที่ `main.py` ทำงานจบ
* **Unit Test สำหรับ Webhook Notifier:** เพิ่ม `test_webhook_notifier()` ใน `tests/test_rockspec.py` ทดสอบการส่งแจ้งเตือนด้วย `unittest.mock.patch("requests.post")`

### Changed

* **`main.py` Summary Aggregation:** ปรับ Entry Point ให้รวบรวมผลลัพธ์ของผู้ใช้ทุกคนที่มีไฟล์เข้าสู่กระบวนการจริง (`active_folders_count > 0`) ก่อนส่งสรุปเดียวเข้า Discord แทนการแจ้งเตือนแยกทีละคน

---

### [4.4.0]

### Added

* **Undo Batch Service (`undo_service.py`):** เพิ่มคลาส `UndoService` สำหรับย้อนคืนชื่อไฟล์กลับเป็นชื่อเดิมบน Google Drive เป็น Batch ตามวันที่ที่เลือก โดยใช้สิทธิ์ของ Service Account กลางตัวเดียวกับ Batch Pipeline
* **Undo Preview & Confirmation Modal:** เพิ่ม Modal บนหน้า `folder_detail.html` ให้ผู้ใช้เลือกวันที่ที่ต้องการย้อนคืน พร้อมพรีวิวตัวอย่างไฟล์สูงสุด 3 รายการต่อโฟลเดอร์ย่อยก่อนกดยืนยัน และกล่องยืนยันอีกชั้นด้วย `confirm()` เพื่อป้องกันการกดพลาด
* **Undo Status Tracking:** เพิ่มการบันทึกสถานะ `UNDONE` ลง Transaction Log ผ่าน `update_transaction_status()` และกรองรายการที่เคย Undo ไปแล้วออกจากรายการที่แสดงในครั้งถัดไป
* **Batch Undo Email Report:** เพิ่มอีเมลสรุปผลการย้อนคืนชื่อไฟล์ (จำนวนสำเร็จ/ไม่สำเร็จ แยกตามโฟลเดอร์ย่อย) ส่งกลับไปยังผู้ใช้ที่กดยืนยันการ Undo

---

### [4.3.0]

### Added

* **Folder Detail Page (`folder_detail.html`, `GET /folder-detail/{folder_id}`):** เพิ่มหน้าแสดงรายละเอียดโฟลเดอร์หลัก ดึงรายชื่อโฟลเดอร์ย่อยและไฟล์ภาพภายในจาก Google Drive มาแสดงเป็นรายการพร้อมลิงก์เปิดไฟล์โดยตรง
* **Async Drive Metadata Fetching:** ใช้ `asyncio.to_thread()` ดึงชื่อโฟลเดอร์และไฟล์จาก Google Drive API แบบ Non-blocking เพื่อไม่ให้ Event Loop ของ FastAPI ค้างระหว่างรอผล API

### Changed

* **Top Navbar ขยายไปทุกหน้า:** เพิ่มแถบเมนูด้านบนแบบ Pinned (หน้าหลัก, วิธีการใช้งาน, ออกจากระบบ) ให้ใช้งานร่วมกันทั้งหน้า Home, Folder Detail และ How-to-Use พร้อม Modal ยืนยันก่อนออกจากระบบ

---

### [4.2.0]

### Added

* **Home Dashboard (`home.html`, `GET/POST /home`):** เพิ่มหน้าหลักแสดงรายการโฟลเดอร์ที่ผู้ใช้ลงทะเบียนไว้แบบ Unique พร้อมลิงก์ไปยัง Google Drive และ Google Sheet ของแต่ละโฟลเดอร์
* **URL Parser (`url_parser.py`):** เพิ่มคลาส `URLParser` สกัด Google Drive Folder ID และ Google Spreadsheet ID จากลิงก์ที่ผู้ใช้วางในฟอร์ม รองรับทั้งรูปแบบ URL เต็ม (`/folders/...`, `/spreadsheets/d/...`) และรูปแบบ Raw ID
* **Folder Registration Form (`POST /home/add-folder`):** เพิ่มฟอร์มลงทะเบียนโฟลเดอร์ใหม่โดยวางลิงก์ Google Sheet และ Google Drive Folder แล้วบันทึกลง Google Sheets DB ผ่าน `upsert_user_config()` อัตโนมัติ

### Fixed

* **Drive Folder Name Fallback:** เพิ่มการดึงชื่อโฟลเดอร์จริงจาก Google Drive API แบบ Async พร้อม Timeout 3 วินาที หากดึงไม่สำเร็จจะ Fallback ไปแสดงชื่อย่อจาก Folder ID แทนเพื่อไม่ให้หน้าเว็บค้างหรือ Error

---

### [4.1.0]

### Added

* **Email OTP Authentication (`auth_service.py`):** เพิ่มระบบ Login ด้วยรหัส OTP 6 หลักที่ส่งผ่านอีเมล แทนที่การขอสิทธิ์ผ่าน Google OAuth 2.0 ที่ใช้ใน Sprint 3 โดยรหัสมีอายุการใช้งาน 5 นาทีและบันทึกลงตาราง `OTP_Store` ใน Google Sheets DB
* **Two-Phase Login UI (`login.html`):** เพิ่มฟอร์ม Login สองเฟส (กรอกอีเมล → กรอกรหัส OTP 6 ช่องแยก) พร้อม JavaScript จัดการ Auto-Advance ช่องถัดไป, รองรับ Paste รหัส 6 หลักทีเดียว, ปุ่มกด Backspace ย้อนกลับช่องก่อนหน้า และปุ่ม "เปลี่ยนอีเมล"/"ส่งรหัสใหม่"
* **Session-Based Auth Routes:** เพิ่ม Endpoint `/auth/send-otp`, `/auth/verify-otp`, `/auth/reset`, `/auth/resend-otp` และ `/logout` จัดการสถานะผู้ใช้ผ่าน `SessionMiddleware` แทนการเก็บ Token ฝั่ง Client

### Changed

* **Login Flow Simplification:** ปรับ Flow การยืนยันตัวตนให้ไม่ต้องขอสิทธิ์ Google Drive รายบุคคลอีกต่อไป ผู้ใช้เพียงแชร์สิทธิ์ Editor ให้ Service Account กลางผ่านหน้า "วิธีการใช้งาน" แทน

---

### [4.0.0]

### Added

* **FastAPI Web Application (`app.py`):** เริ่มต้นย้ายสถาปัตยกรรมส่วนหน้าเว็บจาก Streamlit (Sprint 3) มาเป็น FastAPI ASGI Application พร้อม `Jinja2Templates`, `StaticFiles` Mount ที่ `/static` และ `SessionMiddleware` เข้ารหัส Session ด้วย `MASTER_ENCRYPTION_KEY`
* **Template & Static Asset Structure:** เพิ่มโฟลเดอร์ `templates/` และ `static/style.css` แยกส่วน UI ออกจากโค้ด Python ตามหลัก Separation of Concerns พร้อมออกแบบธีม Vibrant Card, Pill Button และฟอนต์ `Kanit` ต่อยอดแนวทาง UI จาก Sprint 1
* **How-to-Use Guide Page (`how_to_use.html`):** เพิ่มหน้าคู่มือการใช้งานทีละขั้นตอน (ทำสำเนา Template Google Sheet, สร้างโฟลเดอร์ Drive, แชร์สิทธิ์ให้ Service Account, ลงทะเบียนลิงก์ในเว็บ) สำหรับผู้ใช้ใหม่

### Changed

* **Web Dependency Split (`requirements-web.txt`):** แยกรายการ Dependency ของเว็บแอป (`fastapi`, `uvicorn`, `jinja2`, `python-multipart`, `itsdangerous` ฯลฯ) ออกจาก `requirements.txt` ของ Batch Pipeline เพื่อเตรียมพร้อมสำหรับการ Containerize ในลำดับถัดไป
