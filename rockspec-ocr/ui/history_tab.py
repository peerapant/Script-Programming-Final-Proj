import streamlit as st

def render_history_tab(db, undo_service, user_email: str):
    """แสดง UI แท็บประวัติการทำงาน และระบบคืนชื่อเดิม (Undo Engine)"""
    st.subheader("ประวัติการเปลี่ยนชื่อไฟล์ภาพและการย้อนคืน (Undo History)")
    st.write("รายการไฟล์ที่เคยผ่านการประมวลผลเปลี่ยนชื่อในระบบ คุณสามารถสั่งคืนค่าเป็นชื่อเดิมได้ทีละรายการ")

    if st.button("อัปเดตประวัติล่าสุด"):
        st.rerun()

    # ดึงประวัติเฉพาะของผู้ใช้งานปัจจุบันจาก Sheets DB
    transactions = db.get_user_transactions(user_email)

    if not transactions:
        st.info("ยังไม่มีประวัติการเปลี่ยนชื่อไฟล์สำหรับบัญชีนี้")
    else:
        # แสดงรายการประวัติย้อนหลังพร้อมปุ่มกด Undo
        for idx, tx in enumerate(transactions):
            file_id = tx.get("Drive_File_ID", "")
            orig_name = tx.get("Original_Name", "")
            new_name = tx.get("New_Name", "")
            status = str(tx.get("Status", "")).upper()
            ts = tx.get("Timestamp", "")

            with st.container():
                c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
                with c1:
                    st.write(f"**ชื่อเดิม:** `{orig_name}`")
                    st.caption(f"ID: {file_id}")
                with c2:
                    st.write(f"**ชื่อใหม่:** `{new_name}`")
                    st.caption(f"เวลา: {ts}")
                with c3:
                    if status in ["COMPLETED", "SUCCESS"]:
                        st.success("SUCCESS")
                    elif status == "UNDONE":
                        st.warning("UNDONE")
                    else:
                        st.info(status)
                with c4:
                    # ปุ่มย้อนคืนชื่อเดิม
                    if status != "UNDONE":
                        if st.button("คืนชื่อเดิม", key=f"undo_{idx}_{file_id}"):
                            with st.spinner("กำลังเปลี่ยนชื่อไฟล์กลับ..."):
                                ok, msg = undo_service.undo_file_rename(file_id, user_email)
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    else:
                        st.text("คืนชื่อแล้ว")
            st.divider()