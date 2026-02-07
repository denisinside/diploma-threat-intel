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
    projection: dict[str, int] | None = {},
):
    projection["_id"] = 0
    return await db[collection].find_one(query, projection)

async def find_many(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
    projection: dict[str, int] | None = {},
    limit: int | None = None,
    skip: int | None = None,
):
    projection["_id"] = 0
    return await db[collection].find(query, projection).skip(skip).limit(limit).to_list(None)

async def is_exists(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
):
    return await db[collection].count_documents(query) > 0

async def delete_one(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
):
    return await db[collection].delete_one(query)

async def update_one(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
    update: dict[str, Any],
):
    return await db[collection].update_one(query, update)

async def count_documents(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
):
    return await db[collection].count_documents(query)

async def aggregate(
    db: AsyncIOMotorDatabase,
    collection: str,
    pipeline: list[dict[str, Any]],
):
    return await db[collection].aggregate(pipeline)

async def distinct(
    db: AsyncIOMotorDatabase,
    collection: str,
    key: str,
    query: dict[str, Any],
):
    return await db[collection].distinct(key, query)
