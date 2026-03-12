from fastapi import APIRouter, Request, HTTPException, Query, Depends
from shared.models.OSVVulnerability import OSVVulnerability
import services.vulns_service as vulns_service
from api.v1.dependencies import PaginationParams
from typing import List, Optional

router = APIRouter(prefix="/vulns", tags=["vulns"])


@router.get("/search")
async def search_vulnerabilities(
    request: Request,
    q: Optional[str] = Query(None, description="Search query (min 2 chars when provided)"),
    ecosystem: Optional[str] = Query(None, description="Filter by ecosystem"),
    package: Optional[str] = Query(None, description="Filter by package name"),
    cvss_min: Optional[float] = Query(None, ge=0, le=10),
    cvss_max: Optional[float] = Query(None, ge=0, le=10),
    published_from: Optional[str] = Query(None, description="Published from (YYYY-MM-DD)"),
    published_to: Optional[str] = Query(None, description="Published to (YYYY-MM-DD)"),
    cwe_id: Optional[str] = Query(None, description="CWE ID (e.g. 89)"),
    severity: Optional[str] = Query(None, description="Severity: LOW, MODERATE, HIGH, CRITICAL"),
    sort_by: Optional[str] = Query(None, description="Sort: published, modified, cvss, id"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    pg: PaginationParams = Depends(PaginationParams),
) -> dict:
    """Search vulnerabilities with filters. Returns {items, total}"""
    es = request.app.elasticsearch
    limit = pg.limit if pg.limit > 0 else 100
    return await vulns_service.search_vulnerabilities_v2(
        es,
        query_text=q,
        ecosystem=ecosystem,
        package=package,
        cvss_min=cvss_min,
        cvss_max=cvss_max,
        published_from=published_from,
        published_to=published_to,
        cwe_id=cwe_id,
        severity=severity,
        skip=pg.skip,
        limit=limit,
        sort_by=sort_by,
        sort_order=sort_order or "desc",
    )


@router.get("/stats")
async def get_vulnerability_stats(
    request: Request,
    all: bool = Query(False, description="If true, return stats for ALL vulns from MongoDB (ignores filters)"),
    company_id: Optional[str] = Query(None, description="Company ID for ticket/asset scoped KPI metrics"),
    q: Optional[str] = Query(None, min_length=2),
    ecosystem: Optional[str] = Query(None),
    package: Optional[str] = Query(None),
    cvss_min: Optional[float] = Query(None, ge=0, le=10),
    cvss_max: Optional[float] = Query(None, ge=0, le=10),
    published_from: Optional[str] = Query(None),
    published_to: Optional[str] = Query(None),
    cwe_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
) -> dict:
    """Get aggregated stats. Use all=true for stats from MongoDB (all vulns). Otherwise ES with filters."""
    if all:
        db = request.app.mongodb
        return await vulns_service.get_vuln_stats_from_mongo(db, company_id=company_id)
    es = request.app.elasticsearch
    db = request.app.mongodb
    return await vulns_service.get_vuln_stats(
        es,
        db=db,
        company_id=company_id,
        query_text=q,
        ecosystem=ecosystem,
        package=package,
        cvss_min=cvss_min,
        cvss_max=cvss_max,
        published_from=published_from,
        published_to=published_to,
        cwe_id=cwe_id,
        severity=severity,
    )


@router.get("/ecosystems")
async def get_ecosystems(request: Request, pg: PaginationParams = Depends(PaginationParams)) -> List[str]:
    db = request.app.mongodb
    return await vulns_service.get_ecosystems(db, skip=pg.skip, limit=pg.limit)


@router.get("/ecosystems/{ecosystem}")
async def get_vulns_by_ecosystem(
    ecosystem: str, request: Request, pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await vulns_service.get_vulns_by_ecosystem(db, ecosystem, skip=pg.skip, limit=pg.limit)


@router.get("/packages/search")
async def search_packages(
    request: Request,
    q: str = Query(..., min_length=2, description="Package name prefix"),
    limit: int = Query(20, ge=1, le=50),
) -> List[dict]:
    """Search packages by prefix, sorted by vuln count. For autocomplete."""
    db = request.app.mongodb
    return await vulns_service.search_packages(db, q, limit)


@router.get("/ecosystems/{ecosystem}/packages")
async def get_ecosystem_packages(
    ecosystem: str, request: Request, pg: PaginationParams = Depends(PaginationParams),
) -> List[str]:
    db = request.app.mongodb
    return await vulns_service.get_ecosystem_packages(db, ecosystem, skip=pg.skip, limit=pg.limit)


@router.get("/packages/{package}")
async def get_vulnerabilities_by_package(
    package: str, request: Request, pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await vulns_service.get_vulnerabilities_by_package(db, package, skip=pg.skip, limit=pg.limit)


@router.get("/{vuln_id}")
async def get_vulnerability(vuln_id: str, request: Request) -> dict:
    db = request.app.mongodb
    vulnerability = await vulns_service.get_vuln_by_id(db, vuln_id)
    if vulnerability:
        return vulnerability
    else:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
