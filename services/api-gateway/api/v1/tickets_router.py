from fastapi import APIRouter, Request, HTTPException, Query, Depends
from models.requests.tickets_requests import CreateTicketRequest, UpdateTicketRequest
from models.enums import TicketStatus
from models.responses.common import MessageResponse
import services.tickets_service as tickets_service
from api.v1.dependencies import PaginationParams
from typing import List, Optional

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/")
async def create_ticket(body: CreateTicketRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await tickets_service.create_ticket(db, body)


@router.get("/")
async def get_company_tickets(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    status_value = status.value if status else None
    return await tickets_service.get_company_tickets(
        db, company_id, status=status_value, skip=pg.skip, limit=pg.limit,
    )


@router.get("/asset/{asset_id}")
async def get_tickets_by_asset(
    asset_id: str, request: Request, pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await tickets_service.get_tickets_by_asset(
        db, asset_id, skip=pg.skip, limit=pg.limit,
    )


@router.get("/vulnerability/{vulnerability_id}")
async def get_tickets_by_vulnerability(
    vulnerability_id: str, request: Request, pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await tickets_service.get_tickets_by_vulnerability(
        db, vulnerability_id, skip=pg.skip, limit=pg.limit,
    )


@router.get("/count")
async def count_tickets(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
) -> dict:
    db = request.app.mongodb
    status_value = status.value if status else None
    count = await tickets_service.count_tickets(db, company_id, status=status_value)
    return {"company_id": company_id, "status": status_value, "count": count}


@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, request: Request) -> dict:
    db = request.app.mongodb
    return await tickets_service.get_ticket(db, ticket_id)


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: str, body: UpdateTicketRequest, request: Request,
) -> dict:
    db = request.app.mongodb
    return await tickets_service.update_ticket(db, ticket_id, body)


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: str, request: Request) -> MessageResponse:
    db = request.app.mongodb
    await tickets_service.delete_ticket(db, ticket_id)
    return MessageResponse(message="Ticket deleted successfully")
