import repositories.vulns_repo as vulns_repo
from shared.models.OSVVulnerability import OSVVulnerability
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import List

async def get_vuln_by_id(db: AsyncIOMotorDatabase, vuln_id: str) -> Optional[OSVVulnerability]:
    if vuln_id.lower().startswith("cve-"):
        return await vulns_repo.get_vulnerability_by_cve_id(db, vuln_id)
    elif vuln_id.lower().startswith("ghsa-"):
        return await vulns_repo.get_vulnerability_by_ghsa_id(db, vuln_id)
    else:
        raise HTTPException(status_code=400, detail="Invalid vulnerability ID")

async def get_ecosystems(db: AsyncIOMotorDatabase) -> List[str]:
    ecosystems = await vulns_repo.get_ecosystems(db)
    return ecosystems

async def get_vulns_by_ecosystem(db: AsyncIOMotorDatabase, ecosystem: str) -> List[OSVVulnerability]:
    return await vulns_repo.get_vulnerabilities_by_ecosystem(db, ecosystem)

async def get_ecosystem_packages(db: AsyncIOMotorDatabase, ecosystem: str) -> List[str]:
    return await vulns_repo.get_ecosystem_packages(db, ecosystem)