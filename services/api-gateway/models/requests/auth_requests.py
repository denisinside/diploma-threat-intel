from pydantic import BaseModel, EmailStr, Field
from models.enums import SubscriptionPlan
from typing import Optional

class RegisterUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    company_id: Optional[str] = None

class RegisterCompanyRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., description="Primary domain for auto-discovery")
    subscription_plan: Optional[SubscriptionPlan] = SubscriptionPlan.FREE

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=100)

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=8, max_length=100)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class CompanyRegistrationRequest(BaseModel):
    """Public request for company registration (pending super_admin approval)"""
    name: str = Field(..., min_length=2, max_length=100)
    domain: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_full_name: str = Field(..., min_length=2, max_length=100)
    admin_password: str = Field(..., min_length=8, max_length=100)


class RegisterAnalystRequest(BaseModel):
    """Company admin registers a new analyst"""
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
