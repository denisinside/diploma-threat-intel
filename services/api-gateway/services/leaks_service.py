import repositories.leaks_repo as leaks_repo
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime, timezone


# --- Leak Sources (MongoDB) ---

async def create_source(db: AsyncIOMotorDatabase, source_data: dict) -> dict:
    source_data["created_at"] = datetime.now(timezone.utc)
    source_data["updated_at"] = datetime.now(timezone.utc)
    return await leaks_repo.create_source(db, source_data)


async def create_telegram_source(db: AsyncIOMotorDatabase, data: dict) -> dict:
    """
    Create leak source from Telegram scraper. Checks sha256 for deduplication.
    Raises HTTPException 409 if duplicate.
    """
    sha256 = data.get("sha256")
    if not sha256:
        raise HTTPException(status_code=400, detail="sha256 is required")

    existing = await leaks_repo.find_source_by_sha256(db, sha256)
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Duplicate: leak source with this sha256 already exists",
            headers={"X-Existing-Source-Id": str(existing.get("_id", ""))},
        )

    name = data.get("name") or f"combo_{data.get('channel_id', '')}_{data.get('message_id', '')}"
    origin_url = f"tg://channel/{data.get('channel_id', '').lstrip('-')}?msg={data.get('message_id', '')}"

    source_data = {
        "name": name,
        "source_type": "telegram",
        "origin_url": origin_url,
        "size_bytes": data.get("size_bytes"),
        "sha256": sha256,
        "metadata": {
            "channel_id": data.get("channel_id"),
            "message_id": data.get("message_id"),
            "filename": data.get("filename"),
            "downloaded_at": data.get("downloaded_at"),
        },
    }
    return await create_source(db, source_data)


async def get_source(db: AsyncIOMotorDatabase, source_id: str) -> dict:
    source = await leaks_repo.get_source_by_id(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Leak source not found")
    return source


async def get_source_by_sha256(db: AsyncIOMotorDatabase, sha256: str) -> Optional[dict]:
    """Get leak source by SHA-256 hash (for deduplication check)"""
    return await leaks_repo.find_source_by_sha256(db, sha256)


async def get_all_sources(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await leaks_repo.get_all_sources(db, skip=skip, limit=limit)


async def delete_source(db: AsyncIOMotorDatabase, source_id: str) -> bool:
    deleted = await leaks_repo.delete_source(db, source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Leak source not found")
    return True


# --- Leak Records search (Elasticsearch) ---

async def search_by_domain(
    es: AsyncElasticsearch, domain: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Find all leaked credentials for a specific domain"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_by_domain(es, domain, size=es_size, from_=skip)


async def search_by_email(
    es: AsyncElasticsearch, email: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Check if a specific email was found in leaks"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_by_email(es, email, size=es_size, from_=skip)


async def search_fulltext(
    es: AsyncElasticsearch, query_text: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """General full-text search across leak records"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_fulltext(es, query_text, size=es_size, from_=skip)


async def search_by_email_pattern(
    es: AsyncElasticsearch, pattern: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Wildcard search for emails (e.g. '*@company.com')"""
    es_size = size if size > 0 else 10000
    return await leaks_repo.search_records_by_email_pattern(es, pattern, size=es_size, from_=skip)
