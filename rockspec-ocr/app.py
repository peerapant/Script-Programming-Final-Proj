import os
import json
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.sheets_db import GoogleSheetsDB
from src.email_gateway import EmailGateway
from src.security import SecurityEngine
from src.auth_service import AuthService
from src.undo_service import UndoService
from src.github_gateway import GitHubGateway

# Import UI Components ที่แยกไว้
from ui.styles import apply_custom_css
from ui.auth_view import render_auth_view
from ui.config_tab import render_config_tab
from ui.action_tab import render_action_tab
from ui.history_tab import render_history_tab

st.set_page_config(page_title="RockSpec OCR", page_icon="", layout="wide")
apply_custom_css()

@st.cache_resource
def init_services():
    service_account_info = json.loads(os.getenv("GCP_SERVICE_ACCOUNT_KEY"))
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    master_key = os.getenv("MASTER_ENCRYPTION_KEY") or SecurityEngine.generate_master_key()
    
    db = GoogleSheetsDB(spreadsheet_id, service_account_info)
    email_gw = EmailGateway(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
    security = SecurityEngine(master_key)
    
    return db, AuthService(db, email_gw, security), UndoService(db, security, email_gw), GitHubGateway(), service_account_info.get("client_email")

db, auth_service, undo_service, github_gw, sa_email = init_services()

if "user_email" not in st.session_state:
    st.session_state.user_email = None

# Header
st.markdown("<div class='main-title'>RockSpec OCR Management System</div>", unsafe_allow_html=True)

# Auth Routing
if not st.session_state.user_email:
    render_auth_view(auth_service)
    st.stop()

# Main App Layout
user_config = db.get_user_by_email(st.session_state.user_email) or {}

tab1, tab2, tab3 = st.tabs(["ตั้งค่า", "สั่งรัน", "ประวัติ"])

with tab1:
    render_config_tab(db, user_config, st.session_state.user_email, sa_email)
with tab2:
    render_action_tab(github_gw, user_config, st.session_state.user_email)
with tab3:
    render_history_tab(db, undo_service, st.session_state.user_email)