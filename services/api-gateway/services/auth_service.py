import repositories.users_repo as users_repo
import repositories.companies_repo as companies_repo
from models.requests.auth_requests import (
    RegisterUserRequest, RegisterCompanyRequest,
    LoginRequest, ResetPasswordRequest, ForgotPasswordRequest,
)
from core.security import hash_password, verify_password, create_access_token
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from datetime import datetime, timezone


async def register_company(db: AsyncIOMotorDatabase, request: RegisterCompanyRequest) -> dict:
    """Register a new company"""
    if await companies_repo.domain_exists(db, request.domain):
        raise HTTPException(status_code=409, detail="Company with this domain already exists")

    company_data = {
        "name": request.name,
        "domain": request.domain,
        "subscription_plan": request.subscription_plan.value if request.subscription_plan else "free",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    return await companies_repo.create_company(db, company_data)


async def register_user(db: AsyncIOMotorDatabase, request: RegisterUserRequest) -> dict:
    """Register a new user"""
    if await users_repo.email_exists(db, request.email):
        raise HTTPException(status_code=409, detail="User with this email already exists")

    if request.company_id:
        company = await companies_repo.get_company_by_id(db, request.company_id)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

    user_data = {
        "email": request.email,
        "full_name": request.full_name,
        "password_hash": hash_password(request.password),
        "company_id": request.company_id,
        "role": "viewer",
        "last_login": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    user = await users_repo.create_user(db, user_data)

    user.pop("password_hash", None)
    return user


async def login(db: AsyncIOMotorDatabase, request: LoginRequest) -> dict:
    """Authenticate user and return JWT token"""
    user = await users_repo.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    await users_repo.update_user(db, user["_id"], {
        "last_login": datetime.now(timezone.utc),
    })

    token = create_access_token({
        "sub": user["_id"],
        "email": user["email"],
        "role": user.get("role", "viewer"),
        "company_id": user.get("company_id"),
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user.get("role", "viewer"),
            "company_id": user.get("company_id"),
        },
    }


async def reset_password(db: AsyncIOMotorDatabase, request: ResetPasswordRequest) -> dict:
    """Reset user password (requires knowing the email)"""
    user = await users_repo.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await users_repo.update_user(db, user["_id"], {
        "password_hash": hash_password(request.new_password),
        "updated_at": datetime.now(timezone.utc),
    })

    return {"message": "Password reset successfully", "success": True}


async def forgot_password(db: AsyncIOMotorDatabase, request: ForgotPasswordRequest) -> dict:
    """Initiate password reset flow (stub - would send email in production)"""
    user = await users_repo.get_user_by_email(db, request.email)
    response = {"message": "If the email exists, a reset link has been sent", "success": True};
    if not user:
        return response

    # TODO: send password reset email via notification service
    return response
