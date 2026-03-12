import database.mongo as mongo
import database.elastic as elastic
from typing import Any, List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from core.config import settings
from datetime import datetime

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
        es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS, "domain.keyword", domain, size=size, from_=from_,
    )


async def search_records_by_email(
    es: AsyncElasticsearch, email: str, size: int = 50, from_: int = 0,
) -> List[dict]:
    """Search leaked records by exact email"""
    return await elastic.term_search(
        es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS, "email.keyword", email, size=size, from_=from_,
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
        es, settings.ELASTICSEARCH_INDEX_NAME_LEAKS, "email.keyword", pattern, size=size, from_=from_,
    )


async def search_records_with_total(
    es: AsyncElasticsearch,
    query: dict[str, Any],
    size: int = 25,
    from_: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    return await elastic.search_with_total(
        es,
        settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        query=query,
        size=size,
        from_=from_,
        track_total_hits=True,
    )


def build_search_query(
    q: Optional[str] = None,
    domain: Optional[str] = None,
    email: Optional[str] = None,
    email_pattern: Optional[str] = None,
) -> dict[str, Any]:
    if email:
        return {"term": {"email.keyword": email}}
    if domain:
        return {"term": {"domain.keyword": domain}}
    if email_pattern:
        return {"wildcard": {"email.keyword": {"value": email_pattern, "case_insensitive": True}}}
    if q:
        return {
            "multi_match": {
                "query": q,
                "fields": ["email", "username", "domain", "tags", "url", "leaktype"],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        }
    return {"match_all": {}}


async def count_records(es: AsyncElasticsearch, query: dict[str, Any]) -> int:
    response = await es.count(
        index=settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        query=query,
        request_timeout=12,
    )
    return int(response.get("count", 0))


async def aggregate_source_counts(
    es: AsyncElasticsearch, query: dict[str, Any], size: int = 5000,
) -> list[dict[str, Any]]:
    body = {
        "query": query,
        "size": 0,
        "aggs": {"by_source": {"terms": {"field": "leak_source_ids", "size": size}}},
    }
    response = await es.search(
        index=settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        body=body,
        request_timeout=12,
    )
    return response.get("aggregations", {}).get("by_source", {}).get("buckets", [])


async def aggregate_top_domains(
    es: AsyncElasticsearch, query: dict[str, Any], size: int = 10,
) -> list[dict[str, Any]]:
    body = {
        "query": query,
        "size": 0,
        "aggs": {
            "top_domains": {
                "terms": {
                    "field": "domain.keyword",
                    "size": size,
                    "order": {"_count": "desc"},
                }
            }
        },
    }
    response = await es.search(
        index=settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        body=body,
        request_timeout=12,
    )
    return response.get("aggregations", {}).get("top_domains", {}).get("buckets", [])


async def aggregate_password_histogram(es: AsyncElasticsearch, query: dict[str, Any]) -> dict[str, int]:
    # Sampling-based histogram to avoid expensive script aggregations on very large indices.
    body = {
        "query": query,
        "size": 5000,
        "_source": ["password"],
        "track_total_hits": False,
    }
    response = await es.search(
        index=settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        body=body,
        request_timeout=20,
    )
    hits = response.get("hits", {}).get("hits", [])
    buckets = {"1-6": 0, "7-8": 0, "9-10": 0, "11-12": 0, "13-16": 0, "17+": 0}
    for hit in hits:
        source = hit.get("_source", {})
        password = source.get("password")
        if not isinstance(password, str):
            continue
        length = len(password)
        if 1 <= length <= 6:
            buckets["1-6"] += 1
        elif 7 <= length <= 8:
            buckets["7-8"] += 1
        elif 9 <= length <= 10:
            buckets["9-10"] += 1
        elif 11 <= length <= 12:
            buckets["11-12"] += 1
        elif 13 <= length <= 16:
            buckets["13-16"] += 1
        elif length >= 17:
            buckets["17+"] += 1
    return buckets


async def count_critical_alerts(
    es: AsyncElasticsearch,
    query: dict[str, Any],
    include_weak_passwords: bool = False,
) -> int:
    # Fast branch: keyword tags only (safe for very large datasets).
    tag_query = {
        "bool": {
            "must": [query],
            "should": [
                {"term": {"tags": "admin"}},
                {"term": {"tags": "root"}},
            ],
            "minimum_should_match": 1,
        }
    }
    tag_response = await es.count(
        index=settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        query=tag_query,
        request_timeout=20,
    )
    total = int(tag_response.get("count", 0))

    if not include_weak_passwords:
        return total

    # Weak password estimation on filtered datasets only via sampled docs.
    body = {
        "query": query,
        "size": 3000,
        "_source": ["password"],
        "track_total_hits": False,
    }
    weak_resp = await es.search(
        index=settings.ELASTICSEARCH_INDEX_NAME_LEAKS,
        body=body,
        request_timeout=20,
    )
    weak_hits = weak_resp.get("hits", {}).get("hits", [])
    weak_count = 0
    for hit in weak_hits:
        source = hit.get("_source", {})
        password = source.get("password")
        if isinstance(password, str) and 0 < len(password) <= 8:
            weak_count += 1
    return total + weak_count


async def count_sources(db: AsyncIOMotorDatabase) -> int:
    return await db[source_collection].count_documents({})


async def count_recent_sources(
    db: AsyncIOMotorDatabase, since: datetime,
) -> int:
    return await db[source_collection].count_documents({"created_at": {"$gte": since}})


async def get_sources_created_since(
    db: AsyncIOMotorDatabase, since: datetime,
) -> list[dict[str, Any]]:
    docs = await db[source_collection].find({"created_at": {"$gte": since}}).to_list(None)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs


async def get_sources_by_ids(
    db: AsyncIOMotorDatabase, source_ids: list[str],
) -> list[dict[str, Any]]:
    if not source_ids:
        return []
    object_ids: list[ObjectId] = []
    for source_id in source_ids:
        try:
            object_ids.append(ObjectId(source_id))
        except Exception:
            continue
    if not object_ids:
        return []
    docs = await db[source_collection].find({"_id": {"$in": object_ids}}).to_list(None)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs
