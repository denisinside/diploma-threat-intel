from __future__ import annotations
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

def init_mongodb(uri: str, db_name: str) -> tuple[AsyncIOMotorClient, AsyncIOMotorDatabase]:
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    return client, db

def get_collection(db: AsyncIOMotorDatabase, name: str):
    return db[name]

async def insert_one(db: AsyncIOMotorDatabase, collection: str, document: dict[str, Any]):
    result = await db[collection].insert_one(document)
    return result

async def find_one(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
    projection: dict[str, int] | None = None,
):
    return await db[collection].find_one(query, projection)
