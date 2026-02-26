import database.mongo as mongo
import database.elastic as elastic
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from core.config import settings

source_collection = "leak_sources"
record_collection = "leak_records"


# --- Leak Sources (MongoDB) ---

async def create_source(db: AsyncIOMotorDatabase, source_data: dict) -> dict:
    return await mongo.insert_one_entity(db, source_collection, source_data)


async def get_source_by_id(db: AsyncIOMotorDatabase, source_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, source_collection, {"_id": ObjectId(source_id)})


async def find_source_by_sha256(db: AsyncIOMotorDatabase, sha256: str) -> Optional[dict]:
    """Find existing leak source by SHA-256 hash (for deduplication)"""
    return await mongo.find_one_entity(db, source_collection, {"sha256": sha256})


async def get_all_sources(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(db, source_collection, {}, skip=skip, limit=limit)


async def delete_source(db: AsyncIOMotorDatabase, source_id: str) -> bool:
    return await mongo.delete_one_entity(db, source_collection, {"_id": ObjectId(source_id)})


# --- Leak Records search (Elasticsearch - much faster for large datasets) ---

async def search_records_by_domain(
    es: AsyncElasticsearch, domain: str, size: int = 50, from_: int = 0,
) -> List[dict]:
    """Search leaked records by domain (e.g. 'company.com')"""
    return await elastic.term_search(
        es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS, "domain", domain, size=size, from_=from_,
    )


async def search_records_by_email(
    es: AsyncElasticsearch, email: str, size: int = 50, from_: int = 0,
) -> List[dict]:
    """Search leaked records by exact email"""
    return await elastic.term_search(
        es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS, "email", email, size=size, from_=from_,
    )


async def search_records_fulltext(
    es: AsyncElasticsearch, query_text: str, size: int = 50, from_: int = 0,
) -> List[dict]:
    """Full-text search across email, username, domain"""
    return await elastic.multi_match_search(
        es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        query_text, fields=["email", "username", "domain", "tags", "url", "leaktype"], size=size, from_=from_,
    )


async def search_records_by_email_pattern(
    es: AsyncElasticsearch, pattern: str, size: int = 50, from_: int = 0,
) -> List[dict]:
    """Wildcard search (e.g. '*@company.com')"""
    return await elastic.wildcard_search(
        es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS, "email", pattern, size=size, from_=from_,
    )
