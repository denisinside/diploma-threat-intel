from __future__ import annotations
from typing import Any
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel


def init_mongodb(uri: str, db_name: str) -> tuple[AsyncIOMotorClient, AsyncIOMotorDatabase]:
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    return client, db


async def ensure_indexes(db: AsyncIOMotorDatabase):
    """Create all necessary indexes for application collections"""

    # --- users ---
    await db["users"].create_indexes([
        IndexModel([("email", ASCENDING)], unique=True),
        IndexModel([("company_id", ASCENDING)]),
    ])

    # --- companies ---
    await db["companies"].create_indexes([
        IndexModel([("domain", ASCENDING)], unique=True),
    ])

    # --- company_registration_requests ---
    await db["company_registration_requests"].create_indexes([
        IndexModel([("status", ASCENDING)]),
        IndexModel([("domain", ASCENDING)]),
    ])

    # --- assets ---
    await db["assets"].create_indexes([
        IndexModel([("company_id", ASCENDING)]),
        IndexModel([("company_id", ASCENDING), ("name", ASCENDING)]),
        IndexModel([("company_id", ASCENDING), ("type", ASCENDING)]),
        IndexModel([("company_id", ASCENDING), ("is_active", ASCENDING)]),
    ])

    # --- tickets ---
    await db["tickets"].create_indexes([
        IndexModel([("company_id", ASCENDING)]),
        IndexModel([("company_id", ASCENDING), ("status", ASCENDING)]),
        IndexModel([("company_id", ASCENDING), ("status", ASCENDING), ("vulnerability_id", ASCENDING)]),
        IndexModel([("company_id", ASCENDING), ("status", ASCENDING), ("detected_at", DESCENDING)]),
        IndexModel([("company_id", ASCENDING), ("status", ASCENDING), ("resolved_at", DESCENDING)]),
        IndexModel([("asset_id", ASCENDING)]),
        IndexModel([("vulnerability_id", ASCENDING)]),
        IndexModel([("company_id", ASCENDING), ("created_at", DESCENDING)]),
    ])

    # --- subscriptions ---
    await db["subscriptions"].create_indexes([
        IndexModel([("company_id", ASCENDING)]),
        IndexModel([("asset_id", ASCENDING)]),
    ])

    # --- notification_channels ---
    await db["notification_channels"].create_indexes([
        IndexModel([("company_id", ASCENDING)]),
    ])

    # --- leak_sources ---
    await db["leak_sources"].create_indexes([
        IndexModel([("source_type", ASCENDING)]),
        IndexModel(
            [("sha256", ASCENDING)],
            unique=True,
            partialFilterExpression={"sha256": {"$exists": True, "$type": "string"}},
        ),
    ])

    # --- vulnerabilities ---
    await db["vulnerabilities"].create_indexes([
        IndexModel([("id", ASCENDING)], unique=True),
        IndexModel([("aliases", ASCENDING)]),
        IndexModel([("database_specific.severity", ASCENDING)]),
        IndexModel([("affected.package.ecosystem", ASCENDING)]),
        IndexModel([("affected.package.name", ASCENDING)]),
        IndexModel([("modified", DESCENDING)]),
    ])

    logger.info("MongoDB indexes ensured for all collections")

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
    limit: int = 0,
    skip: int = 0,
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


# --- Entity helpers (DBModel-based collections, _id → string) ---

async def find_one_entity(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
):
    """Find one document with ObjectId _id converted to string"""
    doc = await db[collection].find_one(query)
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


async def find_many_entities(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
    skip: int = 0,
    limit: int = 0,
):
    """Find many documents with ObjectId _id converted to string"""
    docs = await db[collection].find(query).skip(skip).limit(limit).to_list(None)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs


async def insert_one_entity(
    db: AsyncIOMotorDatabase,
    collection: str,
    document: dict[str, Any],
):
    """Insert document and return it with string _id"""
    result = await db[collection].insert_one(document)
    document["_id"] = str(result.inserted_id)
    return document


async def update_one_entity(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
    update: dict[str, Any],
):
    """Update one document and return the updated version"""
    await db[collection].update_one(query, update)
    return await find_one_entity(db, collection, query)


async def delete_one_entity(
    db: AsyncIOMotorDatabase,
    collection: str,
    query: dict[str, Any],
) -> bool:
    """Delete one document and return True if deleted"""
    result = await db[collection].delete_one(query)
    return result.deleted_count > 0
