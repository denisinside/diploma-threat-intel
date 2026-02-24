import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

collection = "users"


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, collection, {"_id": ObjectId(user_id)})


async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, collection, {"email": email})


async def get_users_by_company(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"company_id": company_id}, skip=skip, limit=limit,
    )


async def create_user(db: AsyncIOMotorDatabase, user_data: dict) -> dict:
    return await mongo.insert_one_entity(db, collection, user_data)


async def update_user(db: AsyncIOMotorDatabase, user_id: str, update_data: dict) -> Optional[dict]:
    return await mongo.update_one_entity(
        db, collection, {"_id": ObjectId(user_id)}, {"$set": update_data},
    )


async def delete_user(db: AsyncIOMotorDatabase, user_id: str) -> bool:
    return await mongo.delete_one_entity(db, collection, {"_id": ObjectId(user_id)})


async def email_exists(db: AsyncIOMotorDatabase, email: str) -> bool:
    return await mongo.is_exists(db, collection, {"email": email})
