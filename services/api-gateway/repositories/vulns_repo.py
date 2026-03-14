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

async def count_all(db: AsyncIOMotorDatabase) -> int:
    """Total vulnerability count in MongoDB"""
    return await db[collection].count_documents({})


async def get_stats_aggregation(db: AsyncIOMotorDatabase) -> dict:
    """Get severity, CVSS, by_year stats from MongoDB (all vulns)"""
    pipeline = [
        {"$facet": {
            "severity": [
                {"$match": {"database_specific.severity": {"$exists": True, "$ne": None}}},
                {"$group": {"_id": "$database_specific.severity", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
            ],
            "cvss": [
                {"$addFields": {
                    "cvss_score": {
                        "$ifNull": [
                            {"$convert": {"input": "$database_specific.cvss_severities.cvvs_3.score", "to": "double", "onError": None}},
                            {"$convert": {"input": "$database_specific.cvss_severities.cvvs_4.score", "to": "double", "onError": None}},
                            {
                                "$let": {
                                    "vars": {
                                        "sev": {"$arrayElemAt": [
                                            {"$filter": {
                                                "input": {"$ifNull": ["$severity", []]},
                                                "as": "s",
                                                "cond": {"$in": ["$$s.type", ["CVSS_V3", "CVSS_V4"]]}
                                            }},
                                            0
                                        ]}
                                    },
                                    "in": {"$cond": [
                                        {"$and": [
                                            {"$ne": ["$$sev", None]},
                                            {"$ne": ["$$sev.score", None]}
                                        ]},
                                        {"$convert": {"input": "$$sev.score", "to": "double", "onError": None}},
                                        None
                                    ]}
                                }
                            }
                        ]
                }}},
                {"$match": {"cvss_score": {"$exists": True, "$type": "number"}}},
                {"$bucket": {
                    "groupBy": "$cvss_score",
                    "boundaries": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                    "default": "other",
                    "output": {"count": {"$sum": 1}},
                }},
            ],
            "by_year": [
                {"$match": {"$or": [{"published": {"$exists": True, "$ne": None}}, {"modified": {"$exists": True, "$ne": None}}]}},
                {"$addFields": {
                    "pub_date": {"$toDate": {"$ifNull": ["$published", "$modified"]}}
                }},
                {"$group": {"_id": {"$year": "$pub_date"}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ],
            "total": [{"$count": "value"}],
        }},
    ]
    cursor = db[collection].aggregate(pipeline)
    results = await cursor.to_list(length=1)
    if not results:
        return {"severity_distribution": [], "cvss_distribution": [], "by_year": [], "total": 0}
    facet = results[0]

    severity_order = ["CRITICAL", "HIGH", "MODERATE", "LOW"]
    severity_buckets = facet.get("severity", [])
    severity_map = {b["_id"]: b["count"] for b in severity_buckets}
    severity_distribution = [
        {"name": s, "value": severity_map.get(s, 0)}
        for s in severity_order
        if severity_map.get(s, 0) > 0
    ]
    for b in severity_buckets:
        if b["_id"] not in severity_order:
            severity_distribution.append({"name": str(b["_id"]), "value": b["count"]})

    cvss_buckets = facet.get("cvss", [])
    cvss_map = {}
    for b in cvss_buckets:
        bid = b.get("_id")
        if bid != "other" and isinstance(bid, (int, float)):
            cvss_map[int(bid)] = b.get("count", 0)
    cvss_distribution = [
        {"range": f"{i}-{i+1}", "value": cvss_map.get(i, 0)}
        for i in range(9)
    ] + [{"range": "9+", "value": sum(cvss_map.get(k, 0) for k in range(9, 20))}]

    by_year = [
        {"year": str(b["_id"]), "value": b["count"]}
        for b in facet.get("by_year", [])
    ]

    total_val = facet.get("total", [{}])[0].get("value", 0) if facet.get("total") else 0

    return {
        "severity_distribution": severity_distribution,
        "cvss_distribution": cvss_distribution,
        "by_year": by_year,
        "total": total_val,
    }


async def search_packages_by_prefix(
    db: AsyncIOMotorDatabase, prefix: str, limit: int = 20,
) -> List[dict]:
    """Search packages by prefix, sorted by vuln count descending"""
    if not prefix or len(prefix.strip()) < 2:
        return []
    import re
    pattern = re.escape(prefix.strip())
    pipeline = [
        {"$unwind": "$affected"},
        {"$match": {"affected.package.name": {"$regex": f"^{pattern}", "$options": "i"}}},
        {"$group": {"_id": "$affected.package.name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {"name": "$_id", "count": 1, "_id": 0}},
    ]
    cursor = db[collection].aggregate(pipeline)
    return await cursor.to_list(length=limit)


async def get_vulnerabilities_by_package(
    db: AsyncIOMotorDatabase, package: str, skip: int = 0, limit: int = 0,
) -> List[OSVVulnerability]:
    return await mongo.find_many(
        db, collection, {"affected": {"$elemMatch": {"package.name": package}}},
        skip=skip, limit=limit,
    )


async def get_vulnerabilities_by_ticket_ids(
    db: AsyncIOMotorDatabase, vulnerability_ids: List[str],
) -> List[dict]:
    if not vulnerability_ids:
        return []
    query = {
        "$or": [
            {"id": {"$in": vulnerability_ids}},
            {"aliases": {"$in": vulnerability_ids}},
        ]
    }
    projection = {
        "_id": 0,
        "id": 1,
        "aliases": 1,
        "affected.package.name": 1,
        "severity": 1,
        "database_specific.severity": 1,
        "database_specific.epss.percentage": 1,
        "database_specific.cvss_severities.cvvs_3.score": 1,
        "database_specific.cvss_severities.cvvs_4.score": 1,
    }
    return await db[collection].find(query, projection).to_list(None)