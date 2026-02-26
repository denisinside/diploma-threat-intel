from fastapi import APIRouter, Request, HTTPException, Query, Depends
from models.responses.common import MessageResponse
from models.requests.leaks_requests import TelegramLeakSourceRequest
import services.leaks_service as leaks_service
from api.v1.dependencies import PaginationParams
from typing import List, Optional

router = APIRouter(prefix="/leaks", tags=["leaks"])


# --- Leak Sources (MongoDB) ---

@router.post("/sources")
async def create_source(body: dict, request: Request) -> dict:
    db = request.app.mongodb
    return await leaks_service.create_source(db, body)


@router.post("/sources/telegram")
async def create_telegram_source(body: TelegramLeakSourceRequest, request: Request) -> dict:
    """
    Create leak source from Telegram scraper. Deduplicates by sha256.
    Returns 409 if a source with the same sha256 already exists.
    """
    db = request.app.mongodb
    data = body.model_dump(exclude_none=True)
    return await leaks_service.create_telegram_source(db, data)


@router.get("/check-hash/{sha256}")
async def check_hash_exists(sha256: str, request: Request) -> dict:
    """
    Check if a leak source with given sha256 already exists (for deduplication).
    Returns exists: true/false and source_id if exists.
    """
    db = request.app.mongodb
    source = await leaks_service.get_source_by_sha256(db, sha256)
    if source:
        return {"exists": True, "source_id": source.get("_id")}
    return {"exists": False}


@router.get("/sources")
async def get_all_sources(
    request: Request,
    pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await leaks_service.get_all_sources(db, skip=pg.skip, limit=pg.limit)


@router.get("/sources/{source_id}")
async def get_source(source_id: str, request: Request) -> dict:
    db = request.app.mongodb
    return await leaks_service.get_source(db, source_id)


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str, request: Request) -> MessageResponse:
    db = request.app.mongodb
    await leaks_service.delete_source(db, source_id)
    return MessageResponse(message="Leak source deleted successfully")


# --- Leak Records search (Elasticsearch) ---

@router.get("/search")
async def search_leaks(
    request: Request,
    q: Optional[str] = Query(None, min_length=2, description="Full-text search"),
    domain: Optional[str] = Query(None, description="Search by domain (e.g. 'company.com')"),
    email: Optional[str] = Query(None, description="Search by exact email"),
    email_pattern: Optional[str] = Query(None, description="Wildcard search (e.g. '*@company.com')"),
    pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    """Search leaked records via Elasticsearch"""
    es = request.app.elasticsearch

    if email:
        return await leaks_service.search_by_email(es, email, size=pg.limit, skip=pg.skip)
    elif domain:
        return await leaks_service.search_by_domain(es, domain, size=pg.limit, skip=pg.skip)
    elif email_pattern:
        return await leaks_service.search_by_email_pattern(
            es, email_pattern, size=pg.limit, skip=pg.skip,
        )
    elif q:
        return await leaks_service.search_fulltext(es, q, size=pg.limit, skip=pg.skip)
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one search parameter: q, domain, email, or email_pattern",
        )
