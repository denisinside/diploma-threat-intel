from enum import Enum
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from pydantic import Field


class LeakType(str, Enum):
    """Type of leak: url (credentials from URL), stealer (infostealer logs), combo, breach, etc."""
    URL = "url"
    STEALER = "stealer"
    COMBO = "combo"
    BREACH = "breach"
    OTHER = "other"


class LeakSource(BaseModel):
    """
    Represents the container/origin of the leak (e.g., a Telegram Archive).
    """
    name: str = Field(..., description="Name of the dump or archive")
    source_type: str = Field(..., description="Source origin: 'telegram', 'darkweb', 'forum'")
    origin_url: Optional[str] = None
    size_bytes: Optional[int] = None
    sha256: Optional[str] = Field(None, description="SHA-256 hash of the file for deduplication")
    status: Optional[str] = Field("pending", description="Processing status: pending, processing, done, error")


class LeakRecord(BaseModel):
    """
    A single compromised record found inside a LeakSource.
    """
    leak_source_ids: List[str] = Field(default_factory=list, description="List of source IDs where this record was found")

    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, description="Masked plaintext")
    domain: Optional[str] = Field(None, description="Extracted domain from email/url")
    phone: Optional[str] = None
    url: Optional[str] = Field(None, description="Source URL where the credential was found")
    leaktype: Optional[str] = Field(None, description="Type of leak: url, stealer, combo, breach, other")

    tags: List[str] = []  # e.g. ["admin", "vpn", "jira"]