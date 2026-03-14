from pydantic import EmailStr, Field
from models.DBModel import DBModel
from models.enums import Role
from typing import Optional

from datetime import datetime

class Company(DBModel):
    """
    Represents a client organization using the platform.
    """
    name: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., description="Primary domain for auto-discovery")
    is_active: bool = True
    subscription_plan: str = "free"

class User(DBModel):
    """
    System user. Super_admin has no company_id; others belong to a company.
    """
    company_id: Optional[str] = None
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password_hash: str = Field(exclude=True)
    role: Role = Role.VIEWER
    last_login: Optional[datetime] = None