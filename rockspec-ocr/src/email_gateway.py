import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional


class EmailGateway:
    def __init__(self, smtp_user: Optional[str] = None, smtp_password: Optional[str] = None):
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        if not self.smtp_user or not self.smtp_password:
            print(f"[EMAIL SKIPPED] ไม่ได้ตั้งค่า SMTP Credentials. ข้ามการส่งถึง: {to_email}")
            return False

        msg = MIMEMultipart()
        msg['From'] = f"RockSpec OCR Automation <{self.smtp_user}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            print(f"📧 ส่งอีเมลแจ้งเตือนสำเร็จถึง: {to_email}")
            return True
        except Exception as e:
            print(f"[WARNING] ไม่สามารถส่งอีเมลถึง {to_email} ได้: {e}")
            return False