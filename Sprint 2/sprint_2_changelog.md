## Sprint 2 Changelog

### [2.3.0]

### Added

* **Headless Pipeline CLI:** เพิ่มอินเทอร์เฟซการทำงานผ่าน Command Line (`main.py` / `src/pipeline.py`) ที่รองรับพารามิเตอร์ `--user_email` เพื่อเปิดให้ระบบทำงานเบื้องหลังได้โดยไม่ต้องผ่านส่วนติดต่อผู้ใช้
* **Automated Cloud Execution Workflow:** ระบบประมวลผลอัตโนมัติบน GitHub Actions (`.github/workflows/auto_rename.yml`) ที่รองรับการตั้งเวลาทำงานประจำวัน (Cron Schedule: `0 1 * * *`) และการสั่งรันด้วยตนเอง (Manual Trigger)
* **Workflow Concurrency & Timeout Controls:** กลไกจำกัดการทำงานซ้อนกัน (Concurrency Group) และการตั้งเวลาหมดอายุการทำงาน (Timeout) เพื่อป้องกันข้อมูลขัดแย้งกันใน Google Sheets

### Changed

* **Automated Cloud Execution Model:** ปรับเปลี่ยนสถาปัตยกรรมหลักให้เป็น Cloud-Native Headless Service ที่สามารถรันประมวลผลแบบอัตโนมัติได้อย่างสมบูรณ์

### Security

* **GitHub Secrets Management:** เชื่อมโยงการจัดการความลับและการเข้าถึง Cloud ผ่าน GitHub Secrets (`GCP_SERVICE_ACCOUNT_KEY`, `MASTER_ENCRYPTION_KEY`, `SMTP_USER`, `SMTP_PASSWORD`)

---

### [2.2.0]

### Added

* **Token Encryption Engine:** มอดูลเข้ารหัสและถอดรหัส `Refresh Token` ด้วย Fernet (`cryptography.fernet`) ร่วมกับ `MASTER_ENCRYPTION_KEY` สำหรับบันทึกข้อมูลสิทธิ์การใช้งานลง Google Sheets อย่างปลอดภัย
* **Automated Email Notifier:** ระบบส่งอีเมลแจ้งเตือนสรุปผลการประมวลผลเปลี่ยนชื่อไฟล์ (สถานะ SUCCESS, FAILED, EXTERNAL_RENAMED) ในรูปแบบ HTML ผ่าน SMTP/Gmail API

### Security

* **Credential Isolation:** กำหนดนโยบายยกเว้นการติดตามไฟล์ข้อมูลความลับ (`.env`, `service_account.json`, `*.pem`) บน Git เพื่อป้องกันข้อมูลรั่วไหล

---

### [2.1.0]

### Added

* **Google Drive API Service Integration:** ระบบเข้าถึงและจัดการไฟล์บน Cloud ผ่าน Google Drive API
* **Dual-Key File Tracking Engine:** ระบบติดตามสถานะไฟล์แบบสองชั้นด้วย Google Drive `file_id` ร่วมกับชื่อไฟล์ปัจจุบัน เพื่อตรวจจับและบันทึกสถานะกรณีไฟล์ถูกเปลี่ยนชื่อจากภายนอก (`EXTERNAL_RENAMED`)
* **In-Memory Image Stream Processing:** ระบบประมวลผลรูปภาพผ่าน Memory Stream (`io.BytesIO`) ส่งตรงเข้า EasyOCR โดยไม่ต้องบันทึกไฟล์ชั่วคราวลงดิสก์
* **Google Sheets Database Adapter:** ตัวเชื่อมต่อ Google Sheets API (`gspread`) สำหรับใช้เป็นฐานข้อมูลหลักของระบบ ครอบคลุม 3 ตารางหลัก (`Users`, `Transactions_Log`, `OTP_Store`)
* **API Rate Limit Batch Processing:** กลไกจัดกลุ่มการอ่านและเขียนข้อมูล (Batch Read/Write) เพื่อควบคุมปริมาณการเรียกใช้ Google Sheets API ไม่ให้เกินโควตา 60 Requests/Minute

### Changed

* **Database Architecture Shift:** ปรับเปลี่ยนระบบจัดเก็บข้อมูลหลักจากไฟล์ Excel ท้องถิ่นมาเป็น Google Sheets

---

### [2.0.0]

### Added

* **Environment Variable Management:** ระบบจัดการค่าคอนฟิกูเรชันผ่านไฟล์ `.env` ด้วย `python-dotenv`

### Changed

* **Standalone Script Architecture:** ปรับเปลี่ยนโครงสร้างซอฟต์แวร์จากเดิมที่เป็น Google Colab Notebook ให้กลายเป็นสคริปต์ Python อิสระ (Standalone Script) เพื่อรองรับการนำไปปฏิบัติตามสภาพแวดล้อมต่างๆ