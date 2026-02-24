from fastapi import APIRouter, Request, HTTPException, Query, Depends
from shared.models.OSVVulnerability import OSVVulnerability
import services.vulns_service as vulns_service
from api.v1.dependencies import PaginationParams
from typing import List

router = APIRouter(prefix="/vulns", tags=["vulns"])


@router.get("/search")
async def search_vulnerabilities(
    request: Request,
    q: str = Query(..., min_length=2, description="Search query"),
    pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    """Full-text search across vulnerabilities"""
    es = request.app.elasticsearch
    return await vulns_service.search_vulnerabilities(es, q, size=pg.limit, skip=pg.skip)


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
