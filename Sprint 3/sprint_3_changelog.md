## Sprint 3 Changelog

### [3.3.0]

### Added

* **Multi-Environment Secrets Loader:** เพิ่มระบบอ่านค่าคอนฟิกูเรชันแบบยืดหยุ่น รองรับทั้งไฟล์ `.env` (ผ่าน `python-dotenv`) สำหรับรันบนเครื่อง Local และ `st.secrets` สำหรับรันบน Streamlit Community Cloud โดยไม่ต้องแก้โค้ด
* **Streamlit Community Cloud Deployment Target:** ตั้งค่าการ Deploy แอป `app.py` ขึ้น Streamlit Community Cloud ควบคู่กับการรันบน `localhost:8501` สำหรับทดสอบในเครื่อง

### Changed

* **OAuth Consent Screen Scope Configuration:** ปรับประเภท OAuth Consent Screen เป็น Internal / Test Users (รองรับบัญชี `@kkumail.com`, `@kku.ac.th`) เพื่อให้บุคลากรกลุ่มเป้าหมายกดมอบสิทธิ์ใช้งานได้ทันที โดยไม่ต้องผ่านกระบวนการ Google Verification ที่ใช้เวลานาน

### Security

* **GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET Isolation:** แยกค่าความลับของ OAuth Client ออกจากโค้ด โดยอ่านผ่าน Environment Variable / Streamlit Secrets เท่านั้น ไม่ฝังค่าลงในซอร์สโค้ดโดยตรง

---

### [3.2.0]

### Added

* **Encrypted Refresh Token Persistence:** เชื่อมต่อผลลัพธ์จาก OAuth Callback เข้ากับ `security.py` (Fernet) เพื่อเข้ารหัส Refresh Token ก่อนบันทึกอัตโนมัติลงตาราง `Users` ใน Google Sheets DB ทันทีที่ผู้ใช้กดมอบสิทธิ์สำเร็จ
* **User Mapping Dashboard:** เพิ่มฟอร์มในหน้าเว็บ `app.py` สำหรับกรอก Google Drive Folder ID และ Google Sheet Mapping URL/ID เชื่อมต่อกับ `sheets_db.py` เพื่ออัปเดตข้อมูลผู้ใช้โดยตรงจากฝั่ง Web UI

### Changed

* **User Config Update Flow:** ปรับฟังก์ชันบันทึกข้อมูลผู้ใช้ให้รองรับการอัปเดตทั้งจากฝั่ง Headless Pipeline (Sprint 2) และฝั่ง Web UI (Sprint 3) โดยใช้ Schema ตาราง `Users` ร่วมกัน

---

### [3.1.0]

### Added

* **Google OAuth 2.0 Authorization Flow (`oauth_service.py`):** เพิ่มโมดูลสร้าง Authorization URL สำหรับ Redirect ผู้ใช้ไปขอสิทธิ์เข้าถึง Google Drive และฟังก์ชันแลกเปลี่ยน Authorization Code เป็น Refresh Token
* **OAuth Status Display:** เพิ่มปุ่ม "คลิกที่นี่เพื่อมอบสิทธิ์ Access Google Drive" และส่วนแสดงสถานะการมอบสิทธิ์บนหน้าเว็บ `app.py`

### Fixed

* **Error 401: invalid_client:** แก้ไขปัญหาระบบ OAuth ไม่พบ Client ID เนื่องจากยังไม่ได้สร้าง OAuth Client ID บน Google Cloud Console โดยสร้าง Client ID ใหม่และกำหนด Redirect URI เป็น `http://localhost:8501`

---

### [3.0.0]

### Added

* **Streamlit Web Frontend (`app.py`):** เพิ่มส่วนติดต่อผู้ใช้แบบเว็บด้วย Streamlit เป็นครั้งแรก ต่อยอดจากระบบ Headless Pipeline ของ Sprint 2 ให้ผู้ใช้ทั่วไปเข้าถึงระบบผ่านเบราว์เซอร์ได้โดยไม่ต้องใช้ CLI
* **MODULE 4: Presentation Layer (Web UI):** เพิ่มชั้นสถาปัตยกรรมใหม่ครอบ Business Logic Layer และ Data Access Layer เดิมจาก Sprint 2 เพื่อรองรับการแสดงผลผ่านเว็บ

### Changed

* **Entry Point Expansion:** ขยายช่องทางการเข้าใช้งานระบบจากเดิมที่มีเฉพาะ CLI (`main.py`) และ GitHub Actions ให้เพิ่มช่องทาง Web UI (`streamlit run app.py`) ควบคู่กัน โดยยังคงใช้ Data Access Layer และ Business Logic Layer ชุดเดิมจาก Sprint 2 ร่วมกันทั้งสองฝั่ง
