import io
from typing import Any, Dict, List, Tuple
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class GoogleDriveService:
    SCOPES = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, service_account_info: Dict[str, Any]):
        creds = Credentials.from_service_account_info(service_account_info, scopes=self.SCOPES)
        self.service = build('drive', 'v3', credentials=creds)

    def list_subfolders(self, parent_folder_id: str) -> List[Dict[str, str]]:
        """ดึงรายชื่อโฟลเดอร์ย่อยใน Base Folder (เช่น โฟลเดอร์ระบุวันที่)"""
        query = f"'{parent_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        return results.get('files', [])

    def list_image_files(self, folder_id: str) -> List[Dict[str, str]]:
        """ดึงรายการไฟล์รูปภาพในโฟลเดอร์ โดยคืนค่าคู่ Dual-Key: (id, name)"""
        query = f"'{folder_id}' in parents and (mimeType contains 'image/' or name contains '.tif' or name contains '.tiff') and trashed = false"
        results = self.service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        return results.get('files', [])

    def download_file_to_memory(self, file_id: str) -> io.BytesIO:
        """ดาวน์โหลดไฟล์ลงใน Memory Stream โดยไม่ต้องบันทึกลง Disk"""
        request = self.service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream

    def rename_file(self, file_id: str, new_name: str) -> bool:
        """เปลี่ยนชื่อไฟล์บน Google Drive โดยใช้อ้างอิงผ่าน file_id"""
        try:
            file_metadata = {'name': new_name}
            self.service.files().update(fileId=file_id, body=file_metadata).execute()
            return True
        except Exception as e:
            print(f"[ERROR] ไม่สามารถเปลี่ยนชื่อไฟล์ {file_id} บน Drive ได้: {e}")
            return False