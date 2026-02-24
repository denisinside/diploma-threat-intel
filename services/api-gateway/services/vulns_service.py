import repositories.vulns_repo as vulns_repo
import database.elastic as elastic
from shared.models.OSVVulnerability import OSVVulnerability
from motor.motor_asyncio import AsyncIOMotorDatabase
from elasticsearch import AsyncElasticsearch
from fastapi import HTTPException
from typing import List, Optional
from core.config import settings


async def get_vuln_by_id(db: AsyncIOMotorDatabase, vuln_id: str) -> Optional[dict]:
    if vuln_id.upper().startswith("CVE-"):
        return await vulns_repo.get_vulnerability_by_cve_id(db, vuln_id)
    elif vuln_id.upper().startswith("GHSA-"):
        return await vulns_repo.get_vulnerability_by_ghsa_id(db, vuln_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid vulnerability ID (must start with CVE- or GHSA-)")


async def get_ecosystems(
    db: AsyncIOMotorDatabase, skip: int = 0, limit: int = 0,
) -> List[str]:
    raw = await vulns_repo.get_ecosystems(db)
    filtered = [x for x in (raw or []) if x is not None]
    if limit > 0:
        return filtered[skip : skip + limit]
    return filtered[skip:] if skip > 0 else filtered


async def get_vulns_by_ecosystem(
    db: AsyncIOMotorDatabase, ecosystem: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await vulns_repo.get_vulnerabilities_by_ecosystem(db, ecosystem, skip=skip, limit=limit)


async def get_ecosystem_packages(
    db: AsyncIOMotorDatabase, ecosystem: str, skip: int = 0, limit: int = 0,
) -> List[str]:
    raw = await vulns_repo.get_ecosystem_packages(db, ecosystem)
    filtered = [x for x in (raw or []) if x is not None]
    if limit > 0:
        return filtered[skip : skip + limit]
    return filtered[skip:] if skip > 0 else filtered


async def get_vulnerabilities_by_package(
    db: AsyncIOMotorDatabase, package: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await vulns_repo.get_vulnerabilities_by_package(db, package, skip=skip, limit=limit)


# --- Elasticsearch-based search (full-text, fuzzy matching) ---

async def search_vulnerabilities(
    es: AsyncElasticsearch, query_text: str, size: int = 0, skip: int = 0,
) -> List[dict]:
    """Full-text search across vulnerability summary, details, aliases, id"""
    es_size = size if size > 0 else 10000
    return await elastic.multi_match_search(
        es,
        settings.ELASTICSEARCH_INDEX_NAME_VULNERABILITIES,
        query_text,
        fields=["summary^3", "details", "id^2", "aliases^2"],
        size=es_size,
        from_=skip,
    )
