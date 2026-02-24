import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

collection = "companies"


async def create_company(db: AsyncIOMotorDatabase, company_data: dict) -> dict:
    return await mongo.insert_one_entity(db, collection, company_data)


async def get_company_by_id(db: AsyncIOMotorDatabase, company_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, collection, {"_id": ObjectId(company_id)})


async def get_company_by_domain(db: AsyncIOMotorDatabase, domain: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, collection, {"domain": domain})


async def get_all_companies(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(db, collection, {}, skip=skip, limit=limit)


async def update_company(db: AsyncIOMotorDatabase, company_id: str, update_data: dict) -> Optional[dict]:
    return await mongo.update_one_entity(
        db, collection, {"_id": ObjectId(company_id)}, {"$set": update_data},
    )


async def delete_company(db: AsyncIOMotorDatabase, company_id: str) -> bool:
    return await mongo.delete_one_entity(db, collection, {"_id": ObjectId(company_id)})


async def domain_exists(db: AsyncIOMotorDatabase, domain: str) -> bool:
    return await mongo.is_exists(db, collection, {"domain": domain})
