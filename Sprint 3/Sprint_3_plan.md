## เอกสารแผนงาน สถาปัตยกรรม และรายงานผลการทดสอบประจำ Sprint 3

**ชื่อโปรเจกต์:** ระบบประมวลผลและเปลี่ยนชื่อไฟล์ภาพถ่ายกล้องจุลทรรศน์อิเล็กตรอนอัตโนมัติ (SEM Rock Image Renamer)

**วิชา:** CP352301 Script Programming | **ภาคการศึกษา:** 1/2569

**ระยะเวลา:** Sprint 3 (สัปดาห์ที่ 14: Streamlit Web UI, OAuth 2.0 Authorization, User Management Dashboard & Cloud Deployment)

---

### 1. วัตถุประสงค์และขอบเขตโครงการ (Project Purpose & Scope)

ต่อยอดจากระบบ Headless Pipeline ใน Sprint 2 โดยการพัฒนาส่วนติดต่อผู้ใช้แบบเว็บ (Web User Interface) ด้วย Streamlit เพื่ออำนวยความสะดวกให้ผู้ใช้งานทั่วไปสามารถเข้าสู่ระบบ มอบสิทธิ์การเข้าถึง Google Drive ผ่าน OAuth 2.0 และตั้งค่าการเชื่อมต่อข้อมูลได้เองอย่างสะดวก โดยมีขอบเขตการทำงานใน Sprint 3 ดังนี้:

* พัฒนา **Streamlit Web Frontend (`app.py`)** เป็นส่วนหน้าจอหลักสำหรับผู้ใช้งาน แสดงสถานะการมอบสิทธิ์และจัดการข้อมูลส่วนตัว
* เชื่อมต่อ **Google OAuth 2.0 Authentication Flow** สำหรับขอสิทธิ์เข้าถึง Google Drive และจัดเก็บ Refresh Token แบบเข้ารหัส (`Fernet`) ลงในฐานข้อมูล Google Sheets DB โดยอัตโนมัติ
* สร้างหน้าต่าง **User Mapping Dashboard** ให้ผู้ใช้สามารถระบุ Google Drive Folder ID และ Google Sheet Mapping URL/ID เพื่อใช้จับคู่ข้อมูลภาพถ่าย SEM
* ตั้งค่าการรันและ Deploy บน **Streamlit Community Cloud / Local Host** พร้อมจัดการความลับผ่าน `.env` และ Streamlit Secrets (`st.secrets`)
* ทดสอบการใช้งานร่วมระหว่างส่วนหน้าเว็บ (Streamlit Frontend) และส่วนหลังบ้าน (GitHub Actions Batch Pipeline)

---

### 2. สถาปัตยกรรมระบบ (Modular Architecture & Separation of Concerns)

โครงสร้างระบบถูกขยายเพื่อเชื่อมต่อส่วนติดต่อผู้ใช้แบบเว็บ (Web UI) เข้ากับ Data Access Layer และ Business Logic Layer เดิมจาก Sprint 2:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   MODULE 4: PRESENTATION LAYER (WEB UI)                │
│  - app.py (Streamlit Web Application Frontend)                         │
│  - OAuth Authorization Button & Status Display                         │
│  - User Mapping Configuration Form (Folder ID & Sheet Mapping ID)      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   MODULE 2: BUSINESS LOGIC LAYER (BLL)                 │
│  - oauth_service.py (OAuth 2.0 Code Exchange & Token Handling)         │
│  - security.py (Fernet Token Encryption / Decryption)                  │
│  - renamer_service.py & pipeline.py (Batch Processing Orchestrator)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   MODULE 1: DATA ACCESS LAYER (DAL)                    │
│  - sheets_db.py (Google Sheets DB: Users, Transactions_Log, OTP_Store) │
│  - drive_service.py (Google Drive API Integration & In-Memory Stream)  │
│  - email_gateway.py (SMTP Mail Notification System)                    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│            MODULE 3: AUTOMATION & DEPLOYMENT INFRASTRUCTURE            │
│  - Streamlit Community Cloud / Localhost Server (Port 8501)            │
│  - .github/workflows/auto_rename.yml (Cron Job Execution & Runner)     │
└────────────────────────────────────────────────────────────────────────┘

```

---

### 3. นิยามความเสร็จสมบูรณ์ของงาน (Definition of Done - DoD)

งานใน Sprint 3 ถือว่าเสร็จสมบูรณ์เมื่อผ่านเกณฑ์การทดสอบและถูกระบุสถานะอย่างชัดเจนดังนี้:

* [x] **Streamlit Web Application (`app.py`):** สร้างหน้าเว็บแสดงผลข้อมูลผู้ใช้ สถานะการมอบสิทธิ์ และฟอร์มสำหรับกรอกข้อมูลการตั้งค่าได้อย่างถูกต้อง
* [ ] **OAuth 2.0 Authorization Flow (`oauth_service.py`):** เชื่อมต่อ OAuth 2.0 Web Client รับ Redirection Code และแลกเปลี่ยนเป็น Refresh Token ได้สมบูรณ์
* [x] **Encrypted Token Persistence:** บันทึก Refresh Token ที่ผ่านการเข้ารหัสด้วย `Fernet` ลงใน Google Sheets DB (ตาราง Users) ได้โดยอัตโนมัติหลังผู้ใช้กดมอบสิทธิ์
* [x] **User Mapping Dashboard:** ฟอร์มรับค่า Google Drive Folder ID และ Google Sheet Mapping ID ทำงานร่วมกับ `sheets_db.py` ในการอัปเดตข้อมูลผู้ใช้ได้ถูกต้อง
* [x] **Secrets & Environment Configuration:** รองรับการอ่านค่าคอนฟิกทั้งจากไฟล์ `.env` สำหรับการรันในเครื่อง Local และ `st.secrets` สำหรับการรันบน Cloud

---

### 4. แผนการจัดสรรหน้าที่และบทบาทภายในทีม (Team Roles & Responsibilities)

| บทบาท (Role) | สมาชิกที่รับผิดชอบ | ภารกิจหลักใน Sprint 3 |
| --- | --- | --- |
| **Planner / Team Leader** | พีรพล พรหมมิ | • ออกแบบสถาปัตยกรรมส่วนติดต่อผู้ใช้ (Web UI) และ OAuth 2.0 Authorization Flow<br>• กำหนดแนวทางการตั้งค่า Google Cloud Console (OAuth Client ID, Consent Screen, Domain Rules)<br>• จัดทำเอกสารสรุปแผนงานและสอบทานความถูกต้องของระบบภาพรวม |
| **Coder** | ธนธรณ์ ผาลัง | • พัฒนาหน้าเว็บหลัก `app.py` ด้วย Streamlit และสร้างฟอร์มจัดการ User Mapping<br>• เชื่อมต่อ OAuth 2.0 Flow เพื่อดึง Refresh Token และบันทึกเข้ารหัสลง Google Sheets DB<br>• ปรับแต่งการอ่านค่าความลับสลับระหว่าง `.env` และ `st.secrets` |
| **Debugger / QA** | ธนธรณ์ ผาลัง | • ทดสอบการรัน Streamlit บน Local Environment (`localhost:8501`) และ Streamlit Cloud<br>• วิเคราะห์และแก้ไขข้อผิดพลาด OAuth เช่น `Error 401: invalid_client` และหน้าเตือน Unverified App<br>• ตรวจสอบความถูกต้องของการจัดเก็บข้อมูล Refresh Token และ User Mapping ใน Google Sheets DB |

---

### 5. ผลการทดสอบระบบและตารางขอบเขตระบบ (QA Testing & Edge Cases Results)

ผู้ทดสอบ (ธนธรณ์ - Debugger / QA) ได้ทำการทดสอบระบบส่วนหน้าเว็บ (Streamlit Web UI) และกระบวนการยืนยันตัวตน OAuth 2.0 โดยมีผลการทดสอบดังนี้:

| ลำดับ | กรณีทดสอบ (Test Case) | อินพุตนำเข้า (Test Input) | พฤติกรรมที่คาดหวัง vs ผลการทดสอบจริง | สถานะ (Status) |
| --- | --- | --- | --- | --- |
| **1** | **Streamlit Local Launch & Email Prompt** | `streamlit run app.py` บน Terminal | ระบบแสดงข้อความต้อนรับรับค่า Email ใน Terminal สามารถกด Enter เพื่อข้ามและเปิดพอร์ต `http://localhost:8501` ได้สำเร็จ | **PASSED** |
| **2** | **OAuth Authorization Link Generation** | กดปุ่ม "คลิกที่นี่เพื่อมอบสิทธิ์ Access Google Drive" | ระบบสร้าง URL เพื่อ Redirect ผู้ใช้ไปยังหน้าล็อกอินและขอสิทธิ์การใช้งานจาก Google OAuth 2.0 ได้ถูกต้อง | **PASSED** |
| **3** | **OAuth Client ID & Error 401 Handling** | บัญชีผู้ใช้กดมอบสิทธิ์โดยที่ยังไม่ตั้งค่า Credentials | ตรวจพบ `Error 401: invalid_client` เนื่องจากไม่มี Client ID สั่งแก้ไขโดยสร้าง OAuth Client ID และระบุ Redirect URI เป็น `http://localhost:8501` แก้ไขสำเร็จ | **PASSED** |
| **4** | **OAuth Consent Screen & Internal Domain** | บัญชีผู้ใช้ `@kkumail.com` / `@kku.ac.th` | ตั้งค่า User Type เป็น Internal / Test Users เพื่อให้บุคลากรในมหาวิทยาลัยกดมอบสิทธิ์เข้าใช้งานได้โดยไม่ติดบล็อก | **PASSED** |
| **5** | **Encrypted Refresh Token Storage** | Callback authorization code จาก Google | ระบบเปลี่ยน Code เป็น Refresh Token นำไปเข้ารหัสผ่าน `Fernet` และอัปเดตลงตาราง `Users` ใน Google Sheets DB สำเร็จ | **PASSED** |
| **6** | **User Mapping Settings Update** | กรอก Google Drive Folder ID และ Sheet Mapping URL ใน `app.py` | ฟอร์มทำการตรวจสอบความถูกต้องและบันทึกค่าลงฐานข้อมูล Google Sheets เพื่อให้สคริปต์หลังบ้านนำไปใช้งานต่อได้ถูกต้อง | **PASSED** |
| **7** | **Streamlit Secrets Integration** | ตั้งค่า Secrets ใน Streamlit Community Cloud | ระบบสามารถอ่านค่า `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` จาก `st.secrets` แทนไฟล์ `.env` ได้อย่างไม่มีปัญหา | **PASSED** |

---

### 6. สรุปบทเรียนประจำ Sprint (Sprint Retrospective)

### 🌟 Wow! (จุดเด่นที่ทำได้ดีมาก)

1. **Seamless Frontend-to-DB Authentication Persistence:** การเชื่อมโยง OAuth 2.0 เข้ากับ Streamlit ช่วยให้ผู้ใช้งานกดมอบสิทธิ์ผ่านหน้าเว็บเพียงครั้งเดียว ระบบจะทำการดึงและเข้ารหัส Refresh Token บันทึกลง Google Sheets DB โดยอัตโนมัติ ทำให้สคริปต์หลังบ้าน (GitHub Actions) นำ Token ไปใช้งานต่อเนื่องได้ทันทีโดยที่ผู้ใช้ไม่ต้องล็อกอินซ้ำ
2. **Flexible Multi-Environment Support:** โครงสร้างโค้ดส่วนการดึงค่าความลับถูกออกแบบให้ยืดหยุ่น โดยสามารถอ่านค่าจากไฟล์ `.env` ในการรันในเครื่อง Local
3. **Optimized Organization Scope Configuration:** การเลือกตั้งค่า OAuth Consent Screen แบบ Test Users ช่วยตัดปัญหาความยุ่งยากและระยะเวลาในการส่งตรวจสอบ Google Verification ทำให้ทีมงานสามารถทดสอบและเปิดให้ผู้ใช้กลุ่มเป้าหมายใช้งานได้ทันที

---

### 💡 Whoops! (ปัญหาที่พบ)

1. **ปัญหาข้อผิดพลาด Error 401: invalid_client ในช่วงเริ่มต้น:**
* *ปัญหา:* เมื่อผู้ใช้กดปุ่มมอบสิทธิ์ในหน้าเว็บ ระบบแสดงข้อผิดพลาด `Error 401: invalid_client (The OAuth client was not found)`


2. **ข้อจำกัดในการประมวลผลทันทีแบบ Real-time:**
* *ปัญหา:* ผู้ใช้งานที่อัปโหลดภาพถ่าย SEM ขึ้น Google Drive ต้องรอรอบเวลาการประมวลผลของ Cron Job บน GitHub Actions หรือต้องให้ Admin สั่งรัน Manual Trigger ผ่าน CLI
