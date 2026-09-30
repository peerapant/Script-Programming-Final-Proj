# เอกสารแผนงาน สถาปัตยกรรม และรายงานผลการทดสอบประจำ Sprint 2

**ชื่อโปรเจกต์:** ระบบประมวลผลและเปลี่ยนชื่อไฟล์ภาพถ่ายกล้องจุลทรรศน์อิเล็กตรอนอัตโนมัติ (SEM Rock Image Renamer)  
**วิชา:** CP352301 Script Programming | **ภาคการศึกษา:** 1/2569  
**ระยะเวลา:** Sprint 2 (สัปดาห์ที่ 13: Core Infrastructure, Cloud APIs, DB & Headless GitHub Actions)

---

## 1. วัตถุประสงค์และขอบเขตโครงการ (Project Purpose & Scope)

ย้ายระบบประมวลผลจากเดิมที่รันบน Local/Google Colab ขึ้นสู่ระบบอัตโนมัติบน Cloud 100% แบบ Headless (ไม่มี UI) สามารถรันประมวลผลเบื้องหลังได้ตามรอบเวลาที่กำหนด (Cron Job) และรันผ่านคำสั่ง CLI โดยมีขอบเขตการทำงานใน Sprint 2 ดังนี้:

- **Data Access Layer (DAL):** เชื่อมต่อ Google Sheets เป็น Database (รองรับตาราง Users, Transactions_Log, OTP_Store) โดยควบคุม Rate Limit
- **Google Drive API & Dual-Key Drive Engine:** สกัดภาพเข้า Memory Stream (`io.BytesIO`) โดยไม่เขียนไฟล์ลงดิสก์ และใช้ระบบ Dual-Key Drive Engine (`file_id` + `name`) ในการอ้างอิงและเปลี่ยนชื่อไฟล์
- **Security Token Encryption:** เพิ่มระบบความปลอดภัย เข้ารหัสและถอดรหัส Refresh Token ของผู้ใช้ด้วย `cryptography.fernet.Fernet`
- **Batch Pipeline Orchestrator & CLI:** สร้าง Batch Pipeline Orchestrator และหน้าต่าง CLI (`main.py`) รองรับคำสั่ง `--user_email`, `--all_users`, และ `--dry_run`
- **CI/CD GitHub Actions Automation:** ตั้งค่า CI/CD บน GitHub Actions (`auto_rename.yml`) สั่งรันอัตโนมัติทุก 6 ชั่วโมงและแบบสั่งด้วยมือ (Manual Trigger) พร้อมดึงค่าความลับผ่าน GitHub Secrets

---

## 2. สถาปัตยกรรมระบบ (Modular Architecture & Separation of Concerns)

โครงสร้างระบบถูกปรับปรุงให้รองรับการทำงานบน Cloud API และ Headless Execution แบบแยกชั้นหน้าที่ (Layered Architecture):

+------------------------------------------------------------------------+
|                   MODULE 1: DATA ACCESS LAYER (DAL)                    |
|  - sheets_db.py (Google Sheets DB: Users, Transactions_Log, OTP_Store) |
|  - drive_service.py (Drive API: Dual-Key file_id & name, Memory Stream)|
|  - email_gateway.py (SMTP Mail Gateway: แจ้งเตือนผลผ่าน Gmail/App Pass)   |
+----------------------------------+-------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
|                   MODULE 2: BUSINESS LOGIC LAYER (BLL)                 |
|  - security.py (Fernet Token Encryption / Decryption)                  |
|  - renamer_service.py (Dual-Key Matching & Flag EXTERNAL_RENAMED)      |
|  - pipeline.py (Batch Orchestrator: Scan -> OCR -> Rename -> Log/Email)|
+----------------------------------+-------------------------------------+
                                   |
                                   v
+------------------------------------------------------------------------+
|            MODULE 3: PRESENTATION & CI/CD LAYER (CLI & AUTOMATION)     |
|  - main.py (CLI Entrypoint: --user_email, --all_users, --dry_run)      |
|  - .github/workflows/auto_rename.yml (Cron Job, Secrets & Runner)      |
+------------------------------------------------------------------------+

---

## 3. นิยามความเสร็จสมบูรณ์ของงาน (Definition of Done - DoD)

งานใน Sprint 2 ถือว่าเสร็จสมบูรณ์ (Done) เมื่อผ่านเกณฑ์ต่อไปนี้ทุกข้อ:

- [x] **Cloud Database Adapter (`sheets_db.py`):** สร้างฐานข้อมูลบน Google Sheets 3 Tabs (Users, Transactions_Log, OTP_Store) และใช้ Batch Operations (`gspread.get_all_records()`, `append_rows()`) เพื่อป้องกันปัญหา Rate Limit (60 req/min)
- [x] **Dual-Key Drive Engine (`drive_service.py`):** ดึงภาพเข้า Memory Stream (`io.BytesIO`) และเปลี่ยนชื่อไฟล์ผ่าน `file_id` บน Google Drive ได้โดยไม่ต้องเขียนลงดิสก์
- [x] **Security Token Encryption (`security.py`):** เข้ารหัส/ถอดรหัส Refresh Token ของผู้ใช้ได้อย่างปลอดภัยด้วย `cryptography.fernet.Fernet` ผ่าน `MASTER_ENCRYPTION_KEY`
- [x] **External Rename Tracking (`renamer_service.py`):** ตรวจจับไฟล์ที่ถูกเปลี่ยนชื่อจากภายนอกด้วย `file_id` แล้วทำ Flag สถานะ `EXTERNAL_RENAMED` ลงใน Log ได้ถูกต้อง
- [x] **Headless CLI Entrypoint (`main.py`):** รองรับการเรียกใช้ผ่าน CLI ทั้งแบบระบุอีเมลรายคน, สั่งรันผู้ใช้ทั้งหมด และโหมดจำลอง `--dry_run`
- [x] **Automated CI/CD Execution (`auto_rename.yml`):** รันบน GitHub Actions ผ่านทุกขั้นตอน 100% (ตั้งแต่ Setup, System Libs, Dependencies, Unit Tests จนถึง Pipeline Execution)

---

## 4. แผนการจัดสรรหน้าที่และบทบาทภายในทีม (Team Roles & Responsibilities)

| บทบาท (Role) | สมาชิกที่รับผิดชอบ | ภารกิจหลักใน Sprint 2 |
| :--- | :--- | :--- |
| **Planner / Team Leader** | พีรพล พรหมมิ | - ออกแบบสถาปัตยกรรมระบบ Cloud API และระบบความปลอดภัย (Token Encryption)<br>- ออกแบบโครงสร้าง CI/CD Workflow (`auto_rename.yml`) และจัดการ GitHub Secrets<br>- จัดทำเอกสารสรุปแผนงานและสอบทานโครงสร้างภาพรวม |
| **Coder** | ธนธรณ์ ผาลัง | - พัฒนา Data Access Layer (`sheets_db.py`, `drive_service.py`, `email_gateway.py`) <br>- พัฒนา Business Logic Layer (`security.py`, `renamer_service.py`, `pipeline.py`)<br>- เขียนจุดเชื่อมต่อ CLI (`main.py`) สำหรับ GitHub Actions |
| **Debugger / QA** | พีรพล พรหมมิ | - ทดสอบการรัน CI/CD บน GitHub Actions Runner (Ubuntu Linux)<br>- แก้ไขข้อผิดพลาดของ OS Dependencies, Import Path, และ Directory Context<br>- สอบทานความเสถียรของระบบการอ่าน Multiline Secrets และ EasyOCR Model Caching |

---

## 5. ผลการทดสอบระบบและตารางขอบเขตระบบ (QA Testing & Edge Cases Results)

ผู้ทดสอบ (พีรพล - Debugger / QA) ได้ทำการทดสอบรัน Workflow บน **GitHub Actions (Ubuntu Runner)** และระบบส่วนหน้า CLI ตามขอบเขตงานใน Sprint 2 โดยมีผลการทดสอบดังนี้:

| ลำดับ | กรณีทดสอบ (Test Case) | อินพุตนำเข้า (Test Input) | พฤติกรรมที่คาดหวัง vs ผลการทดสอบจริง | สถานะ (Status) |
| :---: | :--- | :--- | :--- | :---: |
| 1 | Google Sheets DB & Batch Operations | `sheets_db.py` (Users, Transactions_Log, OTP_Store) | อ่านข้อมูลแบบ `get_all_records()` และเขียนแบบ `append_rows()` สำเร็จ ระบบประมวลผลราบรื่นโดยไม่ติดปัญหา API Rate Limit (60 req/min) | **PASSED** |
| 2 | In-Memory Stream & Drive Dual-Key | `drive_service.py` (`file_id`, `name`) | สกัดไฟล์ภาพเข้า `io.BytesIO` เพื่อประมวลผล OCR และเปลี่ยนชื่อไฟล์ผ่าน `file_id` บน Google Drive ได้โดยไม่ต้องเขียนไฟล์ลงดิสก์ | **PASSED** |
| 3 | Token Encryption & Safety | `security.py` + `MASTER_ENCRYPTION_KEY` | ถอดรหัส Refresh Token ของผู้ใช้ผ่าน `Fernet` ได้ถูกต้อง และสามารถอ่าน `GCP_SERVICE_ACCOUNT_KEY` แบบ Multiline JSON จาก Environment Variable เข้า Memory ได้โดยตรง | **PASSED** |
| 4 | External Rename Tracking | `renamer_service.py` (ไฟล์ที่ `file_id` ตรงกัน แต่ `name` บน Drive เปลี่ยนไป) | ระบบตรวจจับได้ว่าไฟล์ถูกเปลี่ยนชื่อจากภายนอก จึงทำการ Flag สถานะ `EXTERNAL_RENAMED` ลงใน `Transactions_Log` ก่อนแมปชื่อใหม่ได้ถูกต้อง | **PASSED** |
| 5 | CLI Entrypoint & Dry-Run | `python main.py --all_users --dry_run` และ `--user_email` | สคริปต์สแกนผู้ใช้ตามอาร์กิวเมนต์ที่ระบุ และจำลองการประมวลผลโดยไม่มีการเปลี่ยนชื่อไฟล์จริงบน Google Drive เมื่อเปิดโหมด `--dry_run` | **PASSED** |
| 6 | Linux System Dependencies Compatibility | Runner: `ubuntu-latest` | อัปเดตแพ็กเกจใน Workflow เป็น `libgl1` และ `libglib2.0-0` ทดแทน `libgl1-mesa-glx` ที่ตกรุ่น แก้ไขปัญหา Build Error (`exit code 100`) ทำให้ OpenCV/EasyOCR ทำงานบน Linux ได้สำเร็จ | **PASSED** |
| 7 | Working Directory & Python Import Path | `.github/workflows/auto_rename.yml` | กำหนด `working-directory: rockspec-ocr` และใส่ `PYTHONPATH: .` ในขั้นตอน `pytest` แก้ปัญหาหา `requirements.txt` ไม่เจอ และปัญหา `ModuleNotFoundError: No module named 'src'` | **PASSED** |
| 8 | Secrets Integration & Automated Tests | GitHub Repository Secrets | เพิ่ม `pytest` ในขั้นตอนติดตั้ง Dependencies และดึงค่า Secrets ทั้ง 6 ตัวเข้า Environment Variable ได้ครบถ้วน แก้ปัญหา `[CRITICAL ERROR] ไม่พบ GCP_SERVICE_ACCOUNT_KEY` | **PASSED** |
| 9 | EasyOCR Model Caching Optimization | สเต็ป `actions/cache@v4` ที่ `~/.EasyOCR` | ระบบทำการบันทึก Cache ของ CRAFT Detection Model ไว้ ทำให้การรันรอบถัดไปไม่ต้องดาวน์โหลดโมเดลใหม่ ช่วยลดเวลาการทำงานของ Runner อย่างมีประสิทธิภาพ | **PASSED** |

---

## 6. สรุปบทเรียนประจำ Sprint (Sprint Retrospective)

### 🌟 Wow! (จุดเด่นที่ทำได้ดีมาก)
1. **In-Memory Stream & Dual-Key Engine:** การดึงภาพประมวลผลผ่าน `io.BytesIO` ร่วมกับการใช้อ้างอิง `file_id` ช่วยลด Disk I/O บน Cloud Runner ได้อย่างดี และติดตามไฟล์ที่ถูกเปลี่ยนชื่อจากภายนอก (`EXTERNAL_RENAMED`) ได้อย่างแม่นยำ
2. **Secure Headless CI/CD Pipeline:** การปรับปรุงสคริปต์ให้อ่าน Secrets จาก Environment Variable ตรงเข้า Memory ใน Python ทำให้ไม่ต้องเขียนไฟล์ Credentials (เช่น Service Account JSON) ลงดิสก์ของ GitHub Actions ป้องกันการรั่วไหลของข้อมูลสำคัญ
3. **Optimized Runner Performance:** การทำ Caching สำหรับ Pip Dependencies และ EasyOCR Model (`~/.EasyOCR`) ร่วมกับการตั้งค่า Concurrency Lock ช่วยให้ระบบรันได้รวดเร็ว เซฟเวลาของ Runner และป้องกัน Race Condition เมื่อมีการสั่งรันซ้ำ

### 💡 Whoops! (ปัญหาที่พบและแนวทางการแก้ไข)
1. **ปัญหาชื่อแพ็กเกจ OpenCV บน Ubuntu Runner (Linux OS Mismatch):**
   - *ปัญหา:* สคริปต์ใน CI สั่งติดตั้ง `libgl1-mesa-glx` ซึ่งล้าสมัยใน Ubuntu เวอร์ชั่นใหม่ ทำให้เกิด Error `Process completed with exit code 100`
   - *แนวทางแก้ไข:* แก้ไขไฟล์ `.github/workflows/auto_rename.yml` โดยอัปเดตชื่อแพ็กเกจระบบเป็น `libgl1` และ `libglib2.0-0`
2. **ปัญหา Directory Context และ Python Import Path บน CI:**
   - *ปัญหา:* โครงสร้างโปรเจกต์เก็บบน GitHub โดยย้ายโฟลเดอร์ `.github` ไว้ที่ Root แต่โค้ดจริงอยู่ในโฟลเดอร์ย่อย `rockspec-ocr` ส่งผลให้ `pip install` หา `requirements.txt` ไม่เจอ และ `pytest` หาโมเดล `src` ไม่เจอ (`ModuleNotFoundError`)
   - *แนวทางแก้ไข:* กำหนด `defaults.run.working-directory: rockspec-ocr` ใน Job และระบุ `PYTHONPATH: .` ในขั้นตอนรัน `pytest`
3. **ปัญหาการดาวน์โหลด EasyOCR Model ซ้ำทุกรอบการรัน:**
   - *ปัญหา:* GitHub Actions สร้าง Virtual Machine เครื่องใหม่แบบสะอาดบริสุทธิ์ทุกครั้ง ทำให้ EasyOCR ต้องโหลด Detection Model (CRAFT) ขนาดใหญ่ใหม่ทุกรอบ ส่งผลให้เสียเวลาประมวลผล
   - *แนวทางแก้ไข:* เพิ่ม Step `actions/cache@v4` โดยกำหนด Target Path ไปที่ `~/.EasyOCR` เพื่อดึงไฟล์โมเดลจาก Cache มาใช้ซ้ำได้ทันที