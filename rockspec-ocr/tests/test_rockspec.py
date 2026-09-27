from unittest.mock import patch
import pytest
from src.repository import ExcelMappingRepository
from src.renamer_service import ImageRenamerService
from src.notifier import WebhookNotifier


def test_date_normalization():
    assert ExcelMappingRepository.normalize_date("18/09/2569") == "2026-09-18"


def test_clean_id():
    assert ExcelMappingRepository.clean_id("105.0") == "105"


def test_naming_rule():
    renamer = ImageRenamerService()
    new_name = renamer.generate_new_filename("Sandstone", 1, 2, 1000.0, ".tif")
    assert new_name == "Sandstone-1.2_X1k.tif"


@patch("requests.post")
def test_webhook_notifier(mock_post):
    mock_post.return_value.status_code = 204
    notifier = WebhookNotifier("https://discord.com/api/webhooks/mock")
    result = notifier.send_notification("Test", "Summary Test")
    assert result is True