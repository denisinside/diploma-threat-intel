import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User

collection = "users"

async def get_user_by_id(db: AsyncIOMotorDatabase, id: str) -> Optional[User]:
    return await mongo.find_one(db, collection, {"_id": ObjectId(id)})

async def get_user_by_email(db: AsyncIOMotorDatabase, email: str) -> Optional[User]:
    return await mongo.find_one(db, collection, {"email": email})

async def get_users_by_ids(db: AsyncIOMotorDatabase, ids: List[str]) -> List[User]:
    return await mongo.find_many(db, collection, {"_id": {"$in": ids}})

async def get_users_by_company_id(db: AsyncIOMotorDatabase, company_id: str) -> List[User]:
    return await mongo.find_many(db, collection, {"company_id": company_id})

async def get_users_by_company_domain(db: AsyncIOMotorDatabase, domain: str) -> List[User]:
    return await mongo.find_many(db, collection, {"email": {"$regex": f"@{domain}$"}})

async def create_user(db: AsyncIOMotorDatabase, user: User) -> User:
    return await mongo.insert_one(db, collection, user)

async def update_user(db: AsyncIOMotorDatabase, id: str, user: User) -> User:
    return await mongo.update_one(db, collection, {"_id": ObjectId(id)}, {"$set": user.model_dump()})

async def delete_user(db: AsyncIOMotorDatabase, id: str) -> bool:
    return await mongo.delete_one(db, collection, {"_id": ObjectId(id)})
