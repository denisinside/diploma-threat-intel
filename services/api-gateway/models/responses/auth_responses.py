from pydantic import BaseModel
from typing import Optional


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User data without sensitive fields"""
    id: str
    company_id: Optional[str] = None
    email: str
    full_name: str
    role: str
