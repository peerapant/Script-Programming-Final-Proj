## Sprint 1 Changelog

### [1.5.0]

### Added

* **Interactive Graphical User Interface (GUI):** เพิ่มส่วนติดต่อผู้ใช้แบบ Interactive ด้วย `ipywidgets` ประกอบด้วยช่องกรอก Path สำหรับไฟล์ Excel และโฟลเดอร์รูปภาพ พร้อมปุ่มสั่งการ "ดูตัวอย่าง" (Preview) และ "ยืนยันการเปลี่ยนชื่อ" (Execute)
* **Custom CSS UI Styling:** ตกแต่งหน้าตา UI ด้วย Custom CSS นำเข้า Google Fonts (`Kanit` สำหรับข้อความทั่วไป และ `Fira Code` สำหรับส่วนแสดงผล Terminal) พร้อมปรับรูปแบบช่องป้อนข้อมูลและปุ่มกดให้มีความสวยงามทันสมัย

### Changed

* **Hex Alpha Color Optimization:** แปลงรหัสสี CSS จากรูปแบบ RGBA เป็น Hex 8 หลักที่มี Alpha Channel (เช่น `#2563eb26`, `#ef44444d`, `#ef444466`, `#0000001a`) เพื่อความกระชับและเพิ่มความเสถียรในการแสดงผลสไตล์บน Google Colab

### Fixed

* **Warning Noise Suppression:** เพิ่ม `warnings.filterwarnings("ignore", message=".*pin_memory.*")` เพื่อปิดการแสดงผลข้อความแจ้งเตือน PyTorch/EasyOCR `pin_memory` บน Colab ไม่ให้รบกวนหน้าจอ UI

---

### [1.4.0]

### Added

* **Event-Driven Handler Functions:** เพิ่มฟังก์ชัน Event Handlers (`on_preview_clicked` และ `on_execute_clicked`) พร้อมการล้างหน้าจอด้วย `clear_output()` ก่อนแสดงผลใหม่ ช่วยลดปัญหาการแสดงผลซ้ำซ้อน

### Changed

* **Decoupled Architecture (UI & Logic Separation):** แยกส่วนประมวลผล (Logic) ออกจากส่วนแสดงผล (UI) โดยให้ฟังก์ชัน `process_renamer_pipeline()` คืนค่า (Return) เป็น HTML String เพื่อส่งต่อให้ UI นำไปวาดลง `output_area`
* **Unified HTML Table Structure:** ปรับเปลี่ยนตารางแสดงผลพรีวิวจากการสร้าง `<table>` แยกย่อยรายแถว เป็นการใช้ `<table>` เดียวครอบแถว `<tr>` ทั้งหมด ช่วยให้ความกว้างของแต่ละคอลัมน์ตรงกัน 100% ตลอดทั้งรายการ

---

### [1.3.0]

### Added

* **Spot & Sequence Tracking Logic:** เพิ่มอัลกอริทึมวิเคราะห์ลำดับและตำแหน่งการถ่ายภาพอัตโนมัติ โดยพิจารณาจากระดับกำลังขยาย (หากกำลังขยายเพิ่มขึ้นนับเป็น Zoom, หากกำลังขยายลดลงนับเป็นการย้ายจุดถ่ายใหม่)
* **Enhanced Image Pre-Processing Pipeline:** ปรับปรุงขั้นตอนเตรียมภาพก่อนทำ OCR ด้วยการตัดขอบ (Crop), ปรับ Grayscale, Resize ขยายขนาด 3 เท่าแบบ CUBIC, Binarization Threshold (200) และ Erosion (2x2) เพื่อสกัดตัวเลขกำลังขยายได้อย่างถูกต้อง

### Changed

* **Standardized File Output Pattern:** ปรับโครงสร้างรูปแบบการตั้งชื่อไฟล์ใหม่ให้อยู่ในรูปแบบ `[ชื่อตัวอย่าง]-[ลำดับจุด].[ลำดับการขยาย]_[กำลังขยาย].[นามสกุลไฟล์]` (เช่น `PK1-1.2_X250.tif`) เพื่อความชัดเจนและเป็นระเบียบ

### Fixed

* **Data Matching & Fallback Handling:** ปรับปรุงระบบจับคู่ข้อมูลระหว่าง Excel กับชื่อไฟล์โดยใช้ Key ผสม `(วันที่, ID)` ร่วมกับระบบสำรอง (Fallback) กรณีวันที่ไม่ตรงกัน

---

### [1.2.0]

### Added

* **HTML Table Display:** เพิ่มการแสดงผลตารางเปรียบเทียบชื่อไฟล์เดิม -> ชื่อไฟล์ใหม่ด้วย `IPython.display.HTML` แบบพรีวิวตารางใน Google Colab
* **Buddhist Era Date Normalization:** ปรับแต่งฟังก์ชัน `normalize_date()` ให้รองรับการแปลง พ.ศ. เป็น ค.ศ. (ลบ 543 เมื่อปี > 2500) และแปลงวันที่ในรูปแบบต่างๆ (DDMMYY, YYYY-MM-DD, ตัวคั่นหลากหลาย) ให้เป็น `YYYY-MM-DD` มาตรฐาน
* **Modular Pipeline Structure:** ครอบโค้ดหลักทั้งหมดเข้าฟังก์ชัน `process_renamer_pipeline(excel_path, base_folder_path, dry_run=True)` เพื่อความเป็นระเบียบและเรียกใช้ง่าย
* **Comprehensive Inline Documentation:** เพิ่ม Docstring และ Inline Comment ภาษาไทยตามมาตรฐาน PEP 8 ครอบคลุมทุกฟังก์ชัน

### Changed

* **PEP 8 Code Restructuring:** จัดหมวดหมู่ `import` แยกเป็น Standard Library, Third-Party (Data/Image) และ Colab/Display Utilities อย่างชัดเจน
* **Visual Output Formatting:** ปรับแต่งรูปแบบ HTML ให้แสดงผลกะทัดรัดและชิดซ้ายเพื่อให้อ่านง่ายขึ้น

### Fixed

* **Robust Path Validation:** เพิ่มระบบตรวจสอบความคงมีอยู่ของไฟล์ Excel และโฟลเดอร์รูปภาพก่อนเริ่มประมวลผล
* **Excel Reader Fallback:** เพิ่ม Try-Except สลับไปอ่านไฟล์ด้วย `pd.read_csv` หาก `openpyxl` อ่านไฟล์ Excel ไม่สำเร็จ

---

### [1.1.0]

### Added

* **Magnification Suffix Formatting:** เพิ่มฟังก์ชัน `format_mag_str()` เพื่อต่อท้ายชื่อไฟล์ด้วยค่ากำลังขยาย (`_Xmag` เช่น `_500`, `_1k`, `_2.5k`)
* **Filename Character Sanitization:** เพิ่มฟังก์ชัน `sanitize_filename()` กรองและเปลี่ยนอักขระต้องห้ามในระบบไฟล์ (`/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) ในคอลัมน์ C ให้เป็น `_`
* **ID String Cleaning:** เพิ่มฟังก์ชัน `clean_id()` ตัด `.0` ออกจากตัวเลข ID ที่อ่านมาจาก Excel เพื่อให้ตรงกับ ID บนชื่อไฟล์
* **Overview File Skipping:** เพิ่มเงื่อนไขข้ามการเปลี่ยนชื่อไฟล์ภาพรวมทั่วไป เช่น `1.tif` และ `2.tif` อัตโนมัติ
* **Flexible Multi-Extension Support:** รองรับนามสกุลไฟล์ภาพที่หลากหลายขึ้น ทั้ง `.tif`, `.tiff`, `.png`, `.jpg`, `.jpeg` (แบบไม่จำกัดตัวพิมพ์เล็ก/ใหญ่)
* **Real-Time Terminal Output:** เพิ่มการแสดงผลสถานะ Real-time (`กำลังอ่าน OCR...`) ขณะอ่านรูปภาพด้วย EasyOCR เพื่อไม่ให้หน้าจอค้าง
* **Fallback ID Matching:** เพิ่มระบบค้นหาชื่อหินจาก `rock_id` เพียงอย่างเดียว หากวันที่ใน Excel ไม่ตรงกับชื่อโฟลเดอร์

### Changed

* **Zoom & Point Counter Logic:** แก้ไขตรรกะลำดับจุดและครั้งที่ซูม—เมื่อกำลังขยายเพิ่มขึ้น (`current_mag < next_mag`) จะเป็นการเพิ่มซูม (`zoom_num += 1`) และเมื่อกำลังขยายลดลง/เท่าเดิม จะเป็นการเปลี่ยนจุดถ่ายใหม่ (`point_num += 1`, `zoom_num = 1`)
* **Regex Search Flexibility:** เปลี่ยนจาก `re.match` เป็น `re.search(r'(\d+)', filename)` เพื่อค้นหาตัวเลข ID จากตำแหน่งใดก็ได้ในชื่อไฟล์

### Fixed

* **Key Matching Mismatch:** แก้ปัญหาจับคู่ ID ไม่เจอเนื่องจากประเภทข้อมูล ID ใน Excel เป็น Float (`1.0`) ขณะที่ Regex ได้ String (`'1'`)
* **Drive Path Sensitivity Warnings:** เพิ่มข้อความแจ้งเตือนรายละเอียด Error เมื่อหาไฟล์ Excel หรือโฟลเดอร์ใน Drive ไม่เจอ

### Security

* **Filename Path Traversal Protection:** ป้องกันปัญหา Path Traversal และไฟล์พังจากการ renaming โดยใช้ Regex กรองชื่อหินจาก Excel ก่อนสั่ง `os.rename`

---

### [1.0.0]

### Added

* **Initial SEM Renaming Script:** สคริปต์เวอร์ชันแรกสำหรับเปลี่ยนชื่อไฟล์รูปภาพ SEM `.tif` บน Google Colab ตามข้อมูลใน Excel
* **Google Drive Integration:** เพิ่มการเชื่อมต่อ Google Drive ด้วย `google.colab.drive.mount('/content/drive')`
* **EasyOCR Scale Reading:** นำ EasyOCR มาใช้พร้อมระบบ Pre-processing ภาพ (Grayscale, Resize 3x CUBIC, Binarization Threshold 200, Erosion 2x2) เพื่ออ่านตัวเลขกำลังขยายจาก Scale bar บนรูป
* **Crop Box Configuration:** กำหนดตำแหน่ง Bounding Box (`CROP_BOX = (453, 908, 514, 930)`) สำหรับตัดเฉพาะแถบกำลังขยายภาพ
* **Excel Mapping Engine:** ระบบอ่านข้อมูล Excel เชื่อมโยง คอลัมน์ A (วันที่), คอลัมน์ B (ID หิน), คอลัมน์ C (ชื่อหิน)
* **Merged Cell Handling:** ใช้ `ffill()` ใน Pandas เติมค่าคอลัมน์ A กรณีมี Merged Cells ใน Excel
* **DRY_RUN Safety Execution:** เพิ่มโหมด `DRY_RUN = True` สำหรับทดสอบดูชื่อไฟล์ใหม่บนหน้าจอก่อนเปลี่ยนชื่อจริง
* **Sequential Naming Pattern:** รูปแบบการตั้งชื่อไฟล์พื้นฐาน `[ชื่อหิน]-[จุดที่].[ครั้งที่ซูม].ext`