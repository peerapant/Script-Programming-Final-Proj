from datetime import datetime
from typing import Optional
import requests


class WebhookNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url

    def send_notification(self, title: str, summary: str, status: str = "SUCCESS") -> bool:
        if not self.webhook_url:
            print(f"[NOTIFIER SKIPPED] {title}: {summary}")
            return False

        payload = {
            "embeds": [{
                "title": f"RockSpec OCR: {title}",
                "description": summary,
                "color": 3066993 if status == "SUCCESS" else 15158332,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }

        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            return response.status_code == 204
        except Exception as e:
            print(f"[WARNING] ไม่สามารถส่ง Webhook Notification ได้: {e}")
            return False