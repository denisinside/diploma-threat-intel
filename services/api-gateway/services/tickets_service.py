import repositories.tickets_repo as tickets_repo
from models.requests.tickets_requests import CreateTicketRequest, UpdateTicketRequest
from models.enums import TicketStatus
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import List, Optional
from datetime import datetime, timezone


async def create_ticket(db: AsyncIOMotorDatabase, request: CreateTicketRequest) -> dict:
    ticket_data = request.model_dump()
    ticket_data["status"] = TicketStatus.OPEN.value
    ticket_data["detected_at"] = datetime.now(timezone.utc)
    ticket_data["resolved_at"] = None
    ticket_data["created_at"] = datetime.now(timezone.utc)
    ticket_data["updated_at"] = datetime.now(timezone.utc)
    return await tickets_repo.create_ticket(db, ticket_data)


async def get_ticket(db: AsyncIOMotorDatabase, ticket_id: str) -> dict:
    ticket = await tickets_repo.get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


async def get_company_tickets(
    db: AsyncIOMotorDatabase,
    company_id: str,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 0,
) -> List[dict]:
    if status:
        return await tickets_repo.get_tickets_by_status(
            db, company_id, status, skip=skip, limit=limit,
        )
    return await tickets_repo.get_tickets_by_company(
        db, company_id, skip=skip, limit=limit,
    )


async def get_tickets_by_asset(
    db: AsyncIOMotorDatabase, asset_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await tickets_repo.get_tickets_by_asset(db, asset_id, skip=skip, limit=limit)


async def get_tickets_by_vulnerability(
    db: AsyncIOMotorDatabase, vulnerability_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await tickets_repo.get_tickets_by_vulnerability(
        db, vulnerability_id, skip=skip, limit=limit,
    )


async def update_ticket(
    db: AsyncIOMotorDatabase, ticket_id: str, request: UpdateTicketRequest,
) -> dict:
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc)

    # Auto-set resolved_at when status changes to resolved
    if update_data.get("status") == TicketStatus.RESOLVED.value:
        update_data["resolved_at"] = datetime.now(timezone.utc)

    ticket = await tickets_repo.update_ticket(db, ticket_id, update_data)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


async def delete_ticket(db: AsyncIOMotorDatabase, ticket_id: str) -> bool:
    deleted = await tickets_repo.delete_ticket(db, ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return True


async def count_tickets(
    db: AsyncIOMotorDatabase, company_id: str, status: Optional[str] = None,
) -> int:
    return await tickets_repo.count_tickets_by_company(db, company_id, status=status)
