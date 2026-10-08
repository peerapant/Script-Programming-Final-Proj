import streamlit as st
from src.url_parser import URLParser

def render_config_tab(db, user_config: dict, user_email: str, sa_email: str):
    st.subheader("วิธีเพิ่มสิทธิ์ Service Account ให้เป็น Editor")
    st.markdown(f"""
    <div class="guide-card">
        <h4>ขั้นตอนการแชร์สิทธิ์ (Share Access)</h4>
        <ol>
            <li>คัดลอกอีเมล Service Account: {sa_email}</li>
            <li>ไปยัง Google Drive / Sheets แล้วกด <b>แชร์ (Share)</b></li>
            <li>ใส่ อีเมลดังกล่าว ปรับสิทธิ์เป็น <b>"ผู้เขียน" (Editor)</b> แล้วกดส่ง</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.subheader("รายการโฟลเดอร์และตาราง Mapping ที่บันทึกไว้")
    
    current_folder_id = user_config.get("drive_folder_id", "")
    current_sheet_id = user_config.get("mapping_excel_id", "")

    with st.form("config_form"):
        folder_input = st.text_input("1. Google Drive Folder URL หรือ ID", value=current_folder_id)
        sheet_input = st.text_input("2. Google Sheet Mapping URL หรือ ID", value=current_sheet_id)
        if st.form_submit_button("บันทึกการตั้งค่า"):
            extracted_folder = URLParser.extract_drive_folder_id(folder_input)
            extracted_sheet = URLParser.extract_spreadsheet_id(sheet_input)
            
            if extracted_folder and extracted_sheet:
                db.upsert_user_config(user_email, extracted_folder, extracted_sheet, "", "active")
                st.success("บันทึกสำเร็จ")
                st.rerun()
            else:
                st.error("ลิงก์ไม่ถูกต้อง")