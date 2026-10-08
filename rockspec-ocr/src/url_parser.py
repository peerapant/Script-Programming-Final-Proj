import re
from typing import Optional


class URLParser:
    """Utility Class สำหรับสกัด ID จาก Google Drive Folder URL และ Google Sheets URL"""

    @staticmethod
    def extract_drive_folder_id(url_or_id: str) -> Optional[str]:
        """
        สกัด Google Drive Folder ID จาก URL หรือคืนค่า ID เดิมหากระบุเข้ามาตรงๆ
        รองรับรูปแบบ:
        - https://drive.google.com/drive/folders/1A2B3C4D5E6F...
        - https://drive.google.com/drive/u/0/folders/1A2B3C4D5E6F...
        - 1A2B3C4D5E6F... (Raw ID)
        """
        if not url_or_id:
            return None
        
        text = url_or_id.strip()
        pattern = r'folders/([a-zA-Z0-9_-]+)'
        match = re.search(pattern, text)
        
        if match:
            return match.group(1)
        
        # กรณีระบุ ID เข้ามาตรงๆ (ไม่มี / หรือ http)
        if '/' not in text and len(text) >= 20:
            return text
            
        return None

    @staticmethod
    def extract_spreadsheet_id(url_or_id: str) -> Optional[str]:
        """
        สกัด Google Spreadsheet ID จาก URL หรือคืนค่า ID เดิมหากระบุเข้ามาตรงๆ
        รองรับรูปแบบ:
        - https://docs.google.com/spreadsheets/d/1X2Y3Z4W5V6U.../edit...
        - 1X2Y3Z4W5V6U... (Raw ID)
        """
        if not url_or_id:
            return None
            
        text = url_or_id.strip()
        pattern = r'spreadsheets/d/([a-zA-Z0-9_-]+)'
        match = re.search(pattern, text)
        
        if match:
            return match.group(1)
            
        if '/' not in text and len(text) >= 20:
            return text
            
        return None