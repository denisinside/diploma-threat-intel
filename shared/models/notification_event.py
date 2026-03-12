from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class NotificationEventType(str, Enum):
    LEAK_SOURCE_REGISTERED = "leak.source.registered"
    VULN_DETECTED = "vuln.detected"
    AUTH_PASSWORD_RESET_REQUESTED = "auth.password_reset_requested"
    CHANNEL_TEST = "channel.test"


class NotificationSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"


class NotificationEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: NotificationEventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = Field(..., description="Source service name, e.g. api-gateway")
    company_scope: Optional[list[str]] = Field(
        default=None,
        description="Optional explicit company IDs for routing. When missing, matcher is rule-based.",
    )
    severity: NotificationSeverity = NotificationSeverity.INFO
    data: dict[str, Any] = Field(default_factory=dict)
    version: str = Field(default="v1")
