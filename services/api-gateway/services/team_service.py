import repositories.users_repo as users_repo
from core.security import hash_password
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import List


async def get_company_users(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 100,
) -> List[dict]:
    """List users in a company (admin only, for their own company)"""
    users = await users_repo.get_users_by_company(db, company_id, skip=skip, limit=limit)
    for u in users:
        u.pop("password_hash", None)
    return users


async def register_analyst(
    db: AsyncIOMotorDatabase, company_id: str, data: dict,
) -> dict:
    """Company admin registers a new analyst in their company"""
    if await users_repo.email_exists(db, data["email"]):
        raise HTTPException(status_code=409, detail="User with this email already exists")

    user = await users_repo.create_user(db, {
        "email": data["email"],
        "full_name": data["full_name"],
        "password_hash": hash_password(data["password"]),
        "company_id": company_id,
        "role": "analyst",
        "last_login": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    user.pop("password_hash", None)
    return user


async def delete_company_user(
    db: AsyncIOMotorDatabase, user_id: str, caller_company_id: str,
) -> bool:
    """Company admin deletes a user (analyst only, must be in same company)"""
    user = await users_repo.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.get("company_id") != caller_company_id:
        raise HTTPException(status_code=403, detail="Cannot delete user from another company")
    if user.get("role") == "admin":
        raise HTTPException(status_code=403, detail="Cannot delete company admin")
    return await users_repo.delete_user(db, user_id)
