import os
from cryptography.fernet import Fernet


class SecurityEngine:
    def __init__(self, master_key: str = None):
        key = master_key or os.getenv("MASTER_ENCRYPTION_KEY")
        if not key:
            raise ValueError("ไม่พบ MASTER_ENCRYPTION_KEY ใน Environment Variables")
        self.fernet = Fernet(key.encode() if isinstance(key, str) else key)

    @staticmethod
    def generate_master_key() -> str:
        """ใช้สำหรับสร้าง Master Key ใหม่"""
        return Fernet.generate_key().decode()

    def encrypt_token(self, plain_token: str) -> str:
        """เข้ารหัส Token เพื่อนำไปเก็บใน Google Sheets"""
        if not plain_token:
            return ""
        return self.fernet.encrypt(plain_token.encode()).decode()

    def decrypt_token(self, cipher_token: str) -> str:
        """ถอดรหัส Token เพื่อนำมาใช้ขอ Access Token"""
        if not cipher_token:
            return ""
        return self.fernet.decrypt(cipher_token.encode()).decode()