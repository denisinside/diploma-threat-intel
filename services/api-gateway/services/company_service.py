import repositories.companies_repo as companies_repo
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime, timezone


async def get_company_by_id(db: AsyncIOMotorDatabase, company_id: str) -> dict:
    company = await companies_repo.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


async def get_company_by_domain(db: AsyncIOMotorDatabase, domain: str) -> dict:
    company = await companies_repo.get_company_by_domain(db, domain)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


async def get_all_companies(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 50,
) -> List[dict]:
    return await companies_repo.get_all_companies(db, skip=skip, limit=limit)


async def update_company(
    db: AsyncIOMotorDatabase, company_id: str, update_data: dict,
) -> dict:
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc)
    company = await companies_repo.update_company(db, company_id, update_data)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


async def delete_company(db: AsyncIOMotorDatabase, company_id: str) -> bool:
    deleted = await companies_repo.delete_company(db, company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Company not found")
    return True
