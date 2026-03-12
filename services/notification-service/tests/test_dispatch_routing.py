import os
import sys

SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_ROOT = os.path.abspath(os.path.join(SERVICE_ROOT, "..", ".."))
sys.path.insert(0, SERVICE_ROOT)
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "test_db")
os.environ.setdefault("SMTP_HOST", "localhost")
os.environ.setdefault("SMTP_USERNAME", "user")
os.environ.setdefault("SMTP_PASSWORD", "pass")
os.environ.setdefault("SMTP_FROM_EMAIL", "noreply@example.com")

from dispatch.router import _event_matches_rule, _is_severity_allowed
from shared.models.notification_event import NotificationEvent, NotificationEventType, NotificationSeverity


def test_severity_threshold():
    assert _is_severity_allowed("high", "medium") is True
    assert _is_severity_allowed("low", "critical") is False


def test_vuln_rule_matches_by_keyword():
    event = NotificationEvent(
        event_type=NotificationEventType.VULN_DETECTED,
        source="cve-parser",
        severity=NotificationSeverity.HIGH,
        data={"vuln_id": "CVE-2026-1000", "summary": "nginx vulnerability"},
    )
    rule = {"sub_type": "vulnerability", "keyword": "nginx", "min_severity": "medium"}
    assert _event_matches_rule(event, rule) is True
