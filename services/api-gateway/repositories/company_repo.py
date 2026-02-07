import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import Company

collection = "companies"

async def get_company_by_id(db: AsyncIOMotorDatabase, id: str) -> Optional[Company]:
    return await mongo.find_one(db, collection, {"_id": ObjectId(id)})

async def get_company_by_domain(db: AsyncIOMotorDatabase, domain: str) -> Optional[Company]:
    return await mongo.find_one(db, collection, {"domain": domain})

async def get_companies_by_ids(db: AsyncIOMotorDatabase, ids: List[str]) -> List[Company]:
    return await mongo.find_many(db, collection, {"_id": {"$in": ids}})

async def create_company(db: AsyncIOMotorDatabase, company: Company) -> Company:
    return await mongo.insert_one(db, collection, company)

async def update_company(db: AsyncIOMotorDatabase, id: str, company: Company) -> Company:
    return await mongo.update_one(db, collection, {"_id": ObjectId(id)}, {"$set": company.model_dump()})

async def delete_company(db: AsyncIOMotorDatabase, id: str) -> bool:
    return await mongo.delete_one(db, collection, {"_id": ObjectId(id)}) 