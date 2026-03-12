import os
import sys

SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(SERVICE_ROOT, "..", ".."))
sys.path.insert(0, SERVICE_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from models.enums import ChannelType
from models.requests.subscriptions_requests import validate_channel_config


def test_validate_telegram_config_ok():
    validate_channel_config(
        ChannelType.TELEGRAM,
        {"bot_token": "123:abc", "chat_id": "-100123456"},
    )


def test_validate_signal_requires_recipients():
    try:
        validate_channel_config(
            ChannelType.SIGNAL,
            {"base_url": "http://localhost:8080", "number": "+123", "recipients": []},
        )
        assert False, "Expected validation error"
    except ValueError as exc:
        assert "recipients[]" in str(exc)
