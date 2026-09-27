# Final Project Pitch

### 1. Project Title

ระบบประมวลผลและเปลี่ยนชื่อไฟล์ภาพถ่ายกล้องจุลทรรศน์อิเล็กตรอนอัตโนมัติ (SEM Rock Image Renamer)

---

### 2. Problem Statement

ในการศึกษาวิจัยทางธรณีวิทยาและการวิเคราะห์แผ่นหินบาง (Thin-section) นักวิจัยต้องถ่ายภาพผ่านกล้องจุลทรรศน์จำนวนมากในหลายจุดและหลายกำลังขยาย ปัญหาที่พบคือ:

* **Manual Work & Time-Consuming:** นักวิจัยต้องเปิดดูภาพ อ่านสเกลกำลังขยายด้วยสายตา แล้วพิมพ์เปลี่ยนชื่อไฟล์ทีละภาพ
* **Human Error:** เสี่ยงต่อการพิมพ์ชื่อไฟล์ผิด พิมพ์รหัสตัวอย่างผิด หรือใส่วันที่ผิดฟอร์แมต
* **Lack of Automation:** ขาดระบบอัตโนมัติในการรับไฟล์ใหม่และเชื่อมโยงข้อมูลกับบันทึกใน Excel

---

### 3. Proposed Solution

**RockSpec OCR** คือระบบ **Automated Pipeline** สำหรับจัดระเบียบภาพถ่ายจากกล้องจุลทรรศน์แบบ Hands-Free

1. **Folder Watcher:** คอยเฝ้าระวังโฟลเดอร์รับไฟล์ เมื่อนักวิจัยโยนรูปถ่ายใหม่เข้าโฟลเดอร์ ระบบจะตรวจจับและประมวลผลทันที
2. **Computer Vision & OCR:** ใช้ OpenCV ปรับคุณภาพภาพ และใช้ EasyOCR สกัดค่ากำลังขยาย ($X10$, $X20$, $X1000$) จากภาพถ่ายโดยตรง
3. **Smart Matching & Normalization:** ปรับฟอร์แมตวันที่ (พ.ศ. $\rightarrow$ ค.ศ.), รหัส ID และแมตช์ชื่อหินจากไฟล์ Excel/CSV Master อัตโนมัติ
4. **Automated Notification:** สรุปผลการประมวลผลและส่งการแจ้งเตือนเข้า **Discord / Email** ทันทีหลังประมวลผลเสร็จ

---

### 4. Domain

**Data Analysis & Management / AI-Assisted Software**

---

### 5. API(s) to Use

* **API Name:** EasyOCR Engine / PyTorch Vision Pipeline
* **Documentation Link:** [https://github.com/JaidedAI/EasyOCR](https://github.com/JaidedAI/EasyOCR)
* **Type of Data:** ข้อมูลภาพถ่ายดิบ (`.tif`, `.png`, `.jpg`), อาร์เรย์พิกัดข้อความ (Bounding Boxes), อาร์เรย์อักขระตัวเลขและตัวอักษรที่กำหนด (`0123456789xX`)

---

### 6. Data Persistence Plan

**File-based (Google Sheet)**

* **Input:** อ่านข้อมูลตัวอย่างหลักจากไฟล์ `.xlsx` ผ่าน `pandas`
* **Output:** ดำเนินการเปลี่ยนชื่อไฟล์ภาพลงใน Google Drive อัตโนมัติ พร้อมบันทึกประวัติการทำงานลงในไฟล์ `process_log.xlsl`

---

### 7. Framework Style

**Functional (Modular Pipeline Functions)**

* ออกแบบเป็นสถาปัตยกรรมท่อส่งข้อมูล (Data Pipeline):
`Folder Watcher Trigger` $\rightarrow$ `Image Pre-processing` $\rightarrow$ `OCR Extraction` $\rightarrow$ `Metadata Matching` $\rightarrow$ `File Renaming` $\rightarrow$ `Webhook Notification`

---

### 8. Roles & Responsibilities

**Member 1 : System Planner & Pipeline Developer (ผู้วางโครงสร้างและพัฒนาสคริปต์หลัก)**<br>
* Planner: ออกแบบโครงสร้างระบบ (Pipeline Architecture),
วางลำดับขั้นตอนการทำงานอัตโนมัติ (Automated Workflow) และกำหนดวิธีจัดเก็บไฟล์/เชื่อมต่อ Webhook
* Debugger & Tester: เขียนชุดทดสอบอัตโนมัติด้วย pytest, สร้างภาพทดสอบจำลอง (Mock Files) เพื่อหาข้อผิดพลาด (Debug) เช่น กรณีอ่านภาพไม่ติด หรือวันที่ผิดฟอร์แมต ก่อนนำโค้ดไปรันจริง

**Member 2 : CI/CD Integrator & Quality Debugger**
* Coder (Core Dev): เขียนสคริปต์หลักสำหรับประมวลผลภาพ (OpenCV), ดึงข้อความด้วย EasyOCR, และสร้างระบบเฝ้าระวังโฟลเดอร์อัตโนมัติ (Folder Watcher)


---

### 9. Features (MVP)

1. **Automated Folder Watcher:** ตรวจจับไฟล์ภาพถ่ายใหม่ที่ถูกอัปโหลดเข้ามาในโฟลเดอร์ และเริ่มกระบวนการประมวลผลโดยอัตโนมัติ
2. **Image Pre-processing & OCR Extraction:** ดึงค่ากำลังขยายภาพถ่ายอัตโนมัติด้วย OpenCV + EasyOCR
3. **Data Normalization & Matching:** ปรับมาตรฐานวันที่ (พ.ศ./ค.ศ.) และจับคู่รหัสหินกับไฟล์ Excel Master
4. **Dry-Run & Automated Renaming:** โหมดทดสอบจำลองภาพก่อนเปลี่ยนชื่อจริง และโหมดรันเปลี่ยนชื่อไฟล์อัตโนมัติ
5. **Automated Webhook Notification:** ส่งข้อความสรุปผลการทำงาน (เช่น สรุปจำนวนไฟล์ที่สำเร็จ/ข้อผิดพลาด) ไปยัง Email

---

### 10. Stretch Features (Optional)

* **EXIF Metadata Writing:** บันทึกค่ากำลังขยายและรหัสหินลงใน EXIF Metadata ของไฟล์ภาพเพื่อใช้ในการค้นหาเชิงลึก

---

### 11. Evaluation Checklist

* [x] **API works:** เรียกใช้ EasyOCR สกัดข้อความ และส่ง Notification Webhook สำเร็จ
* [x] **Data persisted correctly:** เปลี่ยนชื่อไฟล์ภาพในระบบ และบันทึก Audit Log สำเร็จ
* [x] **Code follows PEP 8:** จัดโครงสร้างโค้ดเป็นระเบียบ แบ่งโมดูลชัดเจน
* [x] **Tests run:** มีชุดทดสอบ `pytest` สำหรับฟังก์ชันประมวลผลข้อมูลและเปลี่ยนชื่อไฟล์
* [x] **CI/CD pipeline simulated/real:** มี GitHub Actions รัน `pytest` อัตโนมัติเมื่อ ถึงเวลาที่ set ไว้
* [x] **README includes setup + usage instructions:** เอกสารการติดตั้ง สรุปวิธีรันระบบ Automate และการตั้งค่า Webhook
* [x] **Team roles documented:** ระบุบทบาทหน้าที่และการหมุนเวียนบทบาทชัดเจน
