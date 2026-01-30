from pydantic import BaseModel, EmailStr
from typing import Optional, List
from pydantic import Field

class LeakSource(BaseModel):
    """
    Represents the container/origin of the leak (e.g., a Telegram Archive).
    """
    name: str = Field(..., description="Name of the dump or archive")
    source_type: str = Field(..., description="Source origin: 'telegram', 'darkweb', 'forum'")
    origin_url: Optional[str] = None
    size_bytes: Optional[int] = None

class LeakRecord(BaseModel):
    """
    A single compromised record found inside a LeakSource.
    """
    leak_source_id: str = Field(...)
    
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = Field(None, description="Masked plaintext")
    domain: Optional[str] = Field(None, description="Extracted domain from email/url")
    phone: Optional[str] = None
    
    tags: List[str] = [] # e.g. ["admin", "vpn", "jira"]