import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

collection = "assets"


async def create_asset(db: AsyncIOMotorDatabase, asset: dict) -> dict:
    return await mongo.insert_one_entity(db, collection, asset)


async def get_asset_by_id(db: AsyncIOMotorDatabase, asset_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, collection, {"_id": ObjectId(asset_id)})


async def get_assets_by_company(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"company_id": company_id}, skip=skip, limit=limit,
    )


async def get_assets_by_company_and_type(
    db: AsyncIOMotorDatabase, company_id: str, asset_type: str,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"company_id": company_id, "type": asset_type},
    )


async def update_asset(db: AsyncIOMotorDatabase, asset_id: str, update_data: dict) -> Optional[dict]:
    return await mongo.update_one_entity(
        db, collection, {"_id": ObjectId(asset_id)}, {"$set": update_data},
    )


async def delete_asset(db: AsyncIOMotorDatabase, asset_id: str) -> bool:
    return await mongo.delete_one_entity(db, collection, {"_id": ObjectId(asset_id)})


async def count_assets_by_company(db: AsyncIOMotorDatabase, company_id: str) -> int:
    return await mongo.count_documents(db, collection, {"company_id": company_id})
