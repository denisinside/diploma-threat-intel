from fastapi import APIRouter, Request, HTTPException
from shared.models.OSVVulnerability import OSVVulnerability
import services.vulns_service as vulns_service
from typing import List
router = APIRouter(prefix="/vulns", tags=["vulns"])

@router.get("/ecosystems")
async def get_ecosystems(request: Request) -> List[str]:
    db = request.app.mongodb
    ecosystems = await vulns_service.get_ecosystems(db)
    return ecosystems

@router.get("/ecosystems/{ecosystem}")
async def get_vulns_by_ecosystem(ecosystem: str, request: Request) -> List[OSVVulnerability]:
    db = request.app.mongodb
    vulns = await vulns_service.get_vulns_by_ecosystem(db, ecosystem)
    return vulns

@router.get("/ecosystems/{ecosystem}/packages")
async def get_ecosystem_packages(ecosystem: str, request: Request) -> List[str]:
    db = request.app.mongodb
    packages = await vulns_service.get_ecosystem_packages(db, ecosystem)
    return packages

@router.get("/{vuln_id}")
async def get_vulnerability(vuln_id: str, request: Request) -> OSVVulnerability:
    db = request.app.mongodb
    vulnerability = await vulns_service.get_vuln_by_id(db, vuln_id)
    if vulnerability:
        return vulnerability
    else:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
