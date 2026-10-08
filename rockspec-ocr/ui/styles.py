import streamlit as st

def apply_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@300;400;500;600;700&display=swap');

        /* 1. บังคับใช้ฟอนต์ Kanit กับทุก Element และทุกภาษา */
        *, html, body, [class*="css"], [class*="st-"], .stMarkdown, .stButton, .stTextInput, input, button, select, textarea {
            font-family: 'Kanit', sans-serif !important;
        }

        /* 2. ปรับลดขนาดฟอนต์ฐานลงเล็กน้อย (จากปกติ ~16px เหลือ 14px) */
        html, body, .stApp {
            font-size: 14px !important;
        }

        /* 3. ปรับขนาด Custom Classes ให้เล็กลงตามสัดส่วน */
        .main-title { 
            font-size: 1.85rem; 
            font-weight: 700; 
            color: #0F172A; 
            margin-bottom: 0.2rem;
        }
        .sub-title { 
            font-size: 0.95rem; 
            color: #64748B; 
            margin-bottom: 1.5rem; 
        }
        .status-card { 
            padding: 1rem; 
            border-radius: 12px; 
            background-color: #F8FAFC; 
            border: 1px solid #E2E8F0; 
            font-size: 0.9rem;
        }
        .guide-card { 
            padding: 1.25rem; 
            border-radius: 12px; 
            background-color: #EFF6FF; 
            border: 1px solid #BFDBFE; 
            font-size: 0.9rem;
        }
        .login-card { 
            background: #FFFFFF; 
            padding: 2rem 1.5rem; 
            border-radius: 16px; 
            border: 1px solid #E2E8F0; 
            max-width: 440px; 
            margin: 1.5rem auto; 
        }
    </style>
    """, unsafe_allow_html=True)