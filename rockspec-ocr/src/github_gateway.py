import os
import requests
from typing import Optional


class GitHubGateway:
    """Gateway สำหรับเชื่อมต่อกับ GitHub REST API สั่งรัน GitHub Actions Workflow"""

    def __init__(
        self, 
        repo_owner: Optional[str] = None, 
        repo_name: Optional[str] = None, 
        pat_token: Optional[str] = None
    ):
        self.repo_owner = repo_owner or os.getenv("GITHUB_REPO_OWNER")
        self.repo_name = repo_name or os.getenv("GITHUB_REPO_NAME")
        self.pat_token = pat_token or os.getenv("GITHUB_PAT_TOKEN")

    def trigger_rename_now(self, user_email: str, workflow_filename: str = "auto_rename.yml") -> bool:
        """
        ส่ง Dispatch Event เพื่อสั่งให้ GitHub Actions ทำงานแบบ On-Demand
        
        :param user_email: อีเมลของผู้ใช้ที่กดสั่งงาน
        :param workflow_filename: ชื่อไฟล์ workflow .yml
        :return: True หากส่งคำสั่งสำเร็จ (Status 204)
        """
        if not self.repo_owner or not self.repo_name or not self.pat_token:
            print("[ERROR] ไม่พบการตั้งค่า GITHUB_REPO_OWNER, GITHUB_REPO_NAME หรือ GITHUB_PAT_TOKEN")
            return False

        url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/actions/workflows/{workflow_filename}/dispatches"
        
        headers = {
            "Authorization": f"Bearer {self.pat_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        payload = {
            "ref": "main",
            "inputs": {
                "user_email": user_email
            }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 204:
                print(f"[GITHUB DISPATCH SUCCESS] ส่งคำสั่งรัน Workflow ให้ {user_email} สำเร็จ")
                return True
            else:
                print(f"[ERROR] GitHub REST API ตอบกลับด้วย Status Code: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"[ERROR] ไม่สามารถส่งคำสั่ง Dispatch ไปยัง GitHub API ได้: {e}")
            return False