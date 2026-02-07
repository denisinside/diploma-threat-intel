import repositories.company_repo as company_repo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import Company

async def get_company_by_id(db: AsyncIOMotorDatabase, id: str) -> Optional[Company]:
    return await company_repo.get_company_by_id(db, id)

async def get_company_by_domain(db: AsyncIOMotorDatabase, domain: str) -> Optional[Company]:
    return await company_repo.get_company_by_domain(db, domain)

async def create_company(db: AsyncIOMotorDatabase, company: Company) -> Company:
    return await company_repo.create_company(db, company)