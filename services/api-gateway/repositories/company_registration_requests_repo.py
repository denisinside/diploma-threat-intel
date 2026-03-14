import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

collection = "company_registration_requests"


async def create_request(db: AsyncIOMotorDatabase, data: dict) -> dict:
    return await mongo.insert_one_entity(db, collection, data)


async def get_request_by_id(db: AsyncIOMotorDatabase, request_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, collection, {"_id": ObjectId(request_id)})


async def get_pending_requests(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"status": "pending"}, skip=skip, limit=limit,
    )


async def get_all_requests(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(db, collection, {}, skip=skip, limit=limit)


async def update_request(
    db: AsyncIOMotorDatabase, request_id: str, update_data: dict,
) -> Optional[dict]:
    return await mongo.update_one_entity(
        db, collection, {"_id": ObjectId(request_id)}, {"$set": update_data},
    )


async def domain_exists_in_pending(db: AsyncIOMotorDatabase, domain: str) -> bool:
    return await mongo.is_exists(db, collection, {"domain": domain, "status": "pending"})
