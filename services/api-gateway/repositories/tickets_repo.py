import database.mongo as mongo
from typing import List, Optional
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

collection = "tickets"


async def create_ticket(db: AsyncIOMotorDatabase, ticket: dict) -> dict:
    return await mongo.insert_one_entity(db, collection, ticket)


async def get_ticket_by_id(db: AsyncIOMotorDatabase, ticket_id: str) -> Optional[dict]:
    return await mongo.find_one_entity(db, collection, {"_id": ObjectId(ticket_id)})


async def get_tickets_by_company(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"company_id": company_id}, skip=skip, limit=limit,
    )


async def get_tickets_by_status(
    db: AsyncIOMotorDatabase, company_id: str, status: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"company_id": company_id, "status": status}, skip=skip, limit=limit,
    )


async def get_tickets_by_asset(
    db: AsyncIOMotorDatabase, asset_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"asset_id": asset_id}, skip=skip, limit=limit,
    )


async def get_tickets_by_vulnerability(
    db: AsyncIOMotorDatabase, vulnerability_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await mongo.find_many_entities(
        db, collection, {"vulnerability_id": vulnerability_id}, skip=skip, limit=limit,
    )


async def update_ticket(db: AsyncIOMotorDatabase, ticket_id: str, update_data: dict) -> Optional[dict]:
    return await mongo.update_one_entity(
        db, collection, {"_id": ObjectId(ticket_id)}, {"$set": update_data},
    )


async def delete_ticket(db: AsyncIOMotorDatabase, ticket_id: str) -> bool:
    return await mongo.delete_one_entity(db, collection, {"_id": ObjectId(ticket_id)})


async def count_tickets_by_company(
    db: AsyncIOMotorDatabase, company_id: str, status: str = None,
) -> int:
    query = {"company_id": company_id}
    if status:
        query["status"] = status
    return await mongo.count_documents(db, collection, query)


async def get_tickets_by_company_statuses(
    db: AsyncIOMotorDatabase, company_id: str, statuses: List[str],
) -> List[dict]:
    if not statuses:
        return []
    projection = {
        "_id": 1,
        "asset_id": 1,
        "vulnerability_id": 1,
        "status": 1,
        "detected_at": 1,
        "resolved_at": 1,
    }
    docs = await db[collection].find(
        {"company_id": company_id, "status": {"$in": statuses}},
        projection,
    ).to_list(None)
    for doc in docs:
        if "_id" in doc:
            doc["_id"] = str(doc["_id"])
    return docs
