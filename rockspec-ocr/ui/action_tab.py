import streamlit as st

def render_action_tab(github_gw, user_config: dict, user_email: str):
    """แสดง UI แท็บสั่งรันกระบวนการอ่านและเปลี่ยนชื่อไฟล์"""
    st.subheader("สั่งรันกระบวนการอ่านและเปลี่ยนชื่อไฟล์ภาพ (OCR Rename Process)")
    
    current_folder_id = user_config.get("drive_folder_id", "")
    current_sheet_id = user_config.get("mapping_excel_id", "")

    # ตรวจสอบความพร้อมของข้อมูลก่อนสั่งรัน
    ready_to_run = True
    if not current_folder_id or not current_sheet_id:
        st.warning("กรุณาตั้งค่า Google Drive Folder และ Google Sheet ใน แท็บ 1 ให้ครบถ้วนก่อน")
        ready_to_run = False

    # สรุปสถานะการตั้งค่าปัจจุบัน
    st.markdown(f"""
    <div class="status-card">
        <h4 style="margin-top:0; color:#1E293B;">สรุปการตั้งค่าพร้อมสั่งรัน</h4>
        <ul style="margin-bottom:0;">
            <li><b>User Email:</b> {user_email}</li>
            <li><b>Target Folder ID:</b> <code>{current_folder_id or 'ยังไม่ได้ตั้งค่า'}</code></li>
            <li><b>Mapping Sheet ID:</b> <code>{current_sheet_id or 'ยังไม่ได้ตั้งค่า'}</code></li>
            <li><b>Engine Credential:</b> Service Account</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # ปุ่มส่งคำสั่งไปยัง GitHub Action Worker
    if st.button("เริ่มสแกนและเปลี่ยนชื่อไฟล์ทันที (Trigger Process)", type="primary", disabled=not ready_to_run):
        with st.spinner("กำลังส่งคำสั่งไปยัง GitHub Actions Worker Engine..."):
            success = github_gw.trigger_rename_now(user_email)
            if success:
                st.balloons()
                st.success("ส่งคำสั่งประมวลผลสำเร็จ! คุณสามารถติดตามสถานะการทำงานได้ในหน้าประวัติหรือบน GitHub Actions")
            else:
                st.error("ไม่สามารถส่งคำสั่งไปยัง GitHub ได้ กรุณาตรวจสอบ GITHUB_PAT_TOKEN และการตั้งค่า Repository ใน .env")