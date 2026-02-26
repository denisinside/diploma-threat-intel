from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TelegramLeakSourceRequest(BaseModel):
    """Request body for creating a leak source from Telegram scraper (Variant B)"""
    channel_id: str = Field(..., description="Telegram channel/chat ID (e.g. -1001234567890)")
    message_id: int = Field(..., description="Message ID containing the file")
    filename: str = Field(..., description="Original filename")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    sha256: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[a-fA-F0-9]{64}$",
        description="SHA-256 hash for deduplication (64 hex chars)",
    )
    downloaded_at: Optional[datetime] = Field(None, description="When the file was downloaded")
