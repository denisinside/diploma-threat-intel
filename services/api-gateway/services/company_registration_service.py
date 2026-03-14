import repositories.company_registration_requests_repo as requests_repo
import repositories.companies_repo as companies_repo
import repositories.users_repo as users_repo
from core.security import hash_password
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from datetime import datetime, timezone
from typing import List


async def submit_company_registration_request(db: AsyncIOMotorDatabase, data: dict) -> dict:
    """Submit a company registration request (public, pending super_admin approval)"""
    if await companies_repo.domain_exists(db, data["domain"]):
        raise HTTPException(status_code=409, detail="Company with this domain already exists")
    if await requests_repo.domain_exists_in_pending(db, data["domain"]):
        raise HTTPException(status_code=409, detail="Registration request for this domain already pending")
    if await users_repo.email_exists(db, data["admin_email"]):
        raise HTTPException(status_code=409, detail="Admin email already registered")

    request_data = {
        "name": data["name"],
        "domain": data["domain"],
        "admin_email": data["admin_email"],
        "admin_full_name": data["admin_full_name"],
        "admin_password_hash": hash_password(data["admin_password"]),
        "status": "pending",
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    created = await requests_repo.create_request(db, request_data)
    created.pop("admin_password_hash", None)
    return created


async def get_pending_requests(db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 100) -> List[dict]:
    """List pending company registration requests (super_admin only)"""
    items = await requests_repo.get_pending_requests(db, skip=skip, limit=limit)
    for r in items:
        r.pop("admin_password_hash", None)
    return items


async def approve_request(db: AsyncIOMotorDatabase, request_id: str) -> dict:
    """Approve a company registration request: create company + admin user (super_admin only)"""
    req = await requests_repo.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    if await companies_repo.domain_exists(db, req["domain"]):
        await requests_repo.update_request(db, request_id, {"status": "rejected", "rejection_reason": "Domain already exists"})
        raise HTTPException(status_code=409, detail="Company with this domain already exists")
    if await users_repo.email_exists(db, req["admin_email"]):
        await requests_repo.update_request(db, request_id, {"status": "rejected", "rejection_reason": "Email already registered"})
        raise HTTPException(status_code=409, detail="Admin email already registered")

    company = await companies_repo.create_company(db, {
        "name": req["name"],
        "domain": req["domain"],
        "subscription_plan": "free",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })

    user = await users_repo.create_user(db, {
        "email": req["admin_email"],
        "full_name": req["admin_full_name"],
        "password_hash": req["admin_password_hash"],
        "company_id": company["_id"],
        "role": "admin",
        "last_login": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })

    await requests_repo.update_request(db, request_id, {
        "status": "approved",
        "approved_at": datetime.now(timezone.utc),
        "company_id": company["_id"],
        "admin_user_id": user["_id"],
        "updated_at": datetime.now(timezone.utc),
    })

    return {"company": company, "admin_user": {k: v for k, v in user.items() if k != "password_hash"}}


async def reject_request(db: AsyncIOMotorDatabase, request_id: str, reason: str | None = None) -> dict:
    """Reject a company registration request (super_admin only)"""
    req = await requests_repo.get_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    if req.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Request already processed")

    await requests_repo.update_request(db, request_id, {
        "status": "rejected",
        "rejected_at": datetime.now(timezone.utc),
        "rejection_reason": reason or "Rejected by administrator",
        "updated_at": datetime.now(timezone.utc),
    })
    return {"message": "Request rejected"}
