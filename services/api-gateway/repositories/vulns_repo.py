from shared.models.OSVVulnerability import OSVVulnerability
import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

collection = "vulnerabilities"

async def get_vulnerability_by_id(db: AsyncIOMotorDatabase, id: str) -> Optional[OSVVulnerability]:
    return await mongo.find_one(db, collection, {"_id": ObjectId(id)})

async def get_vulnerability_by_ghsa_id(db: AsyncIOMotorDatabase, ghsa_id: str) -> Optional[OSVVulnerability]:
    return await mongo.find_one(db, collection, {"id": ghsa_id})

async def get_vulnerability_by_cve_id(db: AsyncIOMotorDatabase, cve_id: str) -> Optional[OSVVulnerability]:
    return await mongo.find_one(db, collection, {"aliases": {"$in": [cve_id]}})

async def get_vulnerabilities_by_ghsa_ids(db: AsyncIOMotorDatabase, ghsa_ids: List[str]) -> List[OSVVulnerability]:
    return await mongo.find_many(db, collection, {"id": {"$in": ghsa_ids}})

async def get_vulnerabilities_by_ecosystem(
    db: AsyncIOMotorDatabase, ecosystem: str, skip: int = 0, limit: int = 0,
) -> List[OSVVulnerability]:
    return await mongo.find_many(
        db, collection, {"affected": {"$elemMatch": {"package.ecosystem": ecosystem}}},
        skip=skip, limit=limit,
    )

async def get_ecosystems(db: AsyncIOMotorDatabase) -> List[str]:
    return await mongo.distinct(db, collection, "affected.package.ecosystem", {})

async def get_ecosystem_packages(db: AsyncIOMotorDatabase, ecosystem: str) -> List[str]:
    return await mongo.distinct(db, collection, "affected.package.name", {"affected": {"$elemMatch": {"package.ecosystem": ecosystem}}})

async def get_vulnerabilities_by_package(
    db: AsyncIOMotorDatabase, package: str, skip: int = 0, limit: int = 0,
) -> List[OSVVulnerability]:
    return await mongo.find_many(
        db, collection, {"affected": {"$elemMatch": {"package.name": package}}},
        skip=skip, limit=limit,
    )