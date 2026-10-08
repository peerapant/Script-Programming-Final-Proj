import re
import streamlit as st

def is_valid_email(email: str) -> bool:
    """ตรวจสอบรูปแบบอีเมลสากลเบื้องต้น (รองรับทุกโดเมน)"""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def render_auth_view(auth_service):
    """แสดงหน้าต่างยืนยันตัวตนผ่าน OTP ทางอีเมล"""
    # จัดกึ่งกลางหน้าจอด้วย columns และสร้างการ์ดด้วย st.container(border=True)
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        with st.container(border=True):
            st.subheader("เข้าสู่ระบบ")
            st.caption("กรอกอีเมลของคุณเพื่อรับรหัส OTP ยืนยันตัวตนเข้าสู่ระบบ")

            # Step 1: กรอก Email
            input_email = st.text_input(
                "ระบุอีเมลผู้ใช้งาน (Email)", 
                value=st.session_state.get("temp_email", ""),
                placeholder="example@gmail.com"
            )

            if not st.session_state.get("otp_sent", False):
                if st.button("ขอรับรหัส OTP", type="primary", use_container_width=True):
                    if is_valid_email(input_email):
                        clean_email = input_email.strip().lower()
                        with st.spinner("กำลังส่ง OTP ไปยังอีเมลของคุณ..."):
                            ok, msg = auth_service.generate_and_send_otp(clean_email)
                            if ok:
                                st.session_state.otp_sent = True
                                st.session_state.temp_email = clean_email
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(f"ไม่สามารถส่ง OTP ได้: {msg}")
                    else:
                        st.warning("กรุณาระบุรูปแบบอีเมลให้ถูกต้อง (เช่น user@domain.com)")

            # Step 2: กรอกรหัส OTP ยืนยัน
            else:
                st.success(f"ส่งรหัส OTP ไปยัง {st.session_state.temp_email} เรียบร้อยแล้ว")
                otp_code = st.text_input("กรอกรหัส OTP 6 หลัก", max_chars=6, type="password")

                col_b1, col_b2 = st.columns([1, 1])
                with col_b1:
                    if st.button("ยืนยัน OTP", type="primary", use_container_width=True):
                        if auth_service.verify_otp(st.session_state.temp_email, otp_code):
                            st.session_state.user_email = st.session_state.temp_email
                            st.session_state.otp_sent = False
                            st.success("เข้าสู่ระบบสำเร็จ!")
                            st.rerun()
                        else:
                            st.error("รหัส OTP ไม่ถูกต้องหรือหมดอายุ")
                with col_b2:
                    if st.button("เปลี่ยนอีเมล", use_container_width=True):
                        st.session_state.otp_sent = False
                        st.rerun()