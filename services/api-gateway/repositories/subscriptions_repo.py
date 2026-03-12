import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

sub_collection = "subscriptions"
channel_collection = "notification_channels"


# --- Subscriptions ---

async def create_subscription(db: AsyncIOMotorDatabase, sub: dict) -> dict:
    return await mongo.insert_one_entity(db, sub_collection, sub)


async def get_subscription_by_id(db: AsyncIOMotorDatabase, sub_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, sub_collection, {"_id": ObjectId(sub_id)})


async def get_subscriptions_by_company(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, sub_collection, {"company_id": company_id}, skip=skip, limit=limit,
    )


async def update_subscription(db: AsyncIOMotorDatabase, sub_id: str, update_data: dict) -> Optional[dict]:
    return await mongo.update_one_entity(
        db, sub_collection, {"_id": ObjectId(sub_id)}, {"$set": update_data},
    )


async def delete_subscription(db: AsyncIOMotorDatabase, sub_id: str) -> bool:
    return await mongo.delete_one_entity(db, sub_collection, {"_id": ObjectId(sub_id)})


async def delete_subscriptions_by_asset_id(db: AsyncIOMotorDatabase, asset_id: str) -> int:
    """Delete all subscriptions linked to asset. Returns number deleted."""
    result = await db[sub_collection].delete_many({"asset_id": asset_id})
    return result.deleted_count


# --- Notification Channels ---

async def create_channel(db: AsyncIOMotorDatabase, channel: dict) -> dict:
    return await mongo.insert_one_entity(db, channel_collection, channel)


async def get_channel_by_id(db: AsyncIOMotorDatabase, channel_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, channel_collection, {"_id": ObjectId(channel_id)})


async def get_channels_by_company(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, channel_collection, {"company_id": company_id}, skip=skip, limit=limit,
    )


async def update_channel(db: AsyncIOMotorDatabase, channel_id: str, update_data: dict) -> Optional[dict]:
    return await mongo.update_one_entity(
        db, channel_collection, {"_id": ObjectId(channel_id)}, {"$set": update_data},
    )


async def delete_channel(db: AsyncIOMotorDatabase, channel_id: str) -> bool:
    return await mongo.delete_one_entity(db, channel_collection, {"_id": ObjectId(channel_id)})
