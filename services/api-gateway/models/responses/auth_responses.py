from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User data without sensitive fields"""
    id: str
    company_id: str
    email: str
    full_name: str
    role: str
