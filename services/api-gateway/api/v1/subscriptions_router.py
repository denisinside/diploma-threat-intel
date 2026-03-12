from fastapi import APIRouter, Request, HTTPException, Query, Depends
from models.requests.subscriptions_requests import (
    CreateSubscriptionRequest, UpdateSubscriptionRequest,
    CreateChannelRequest, UpdateChannelRequest,
)
from models.responses.common import MessageResponse
import services.subscriptions_service as subscriptions_service
from api.v1.dependencies import PaginationParams
from typing import List

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


# --- Subscriptions ---

@router.post("/")
async def create_subscription(body: CreateSubscriptionRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await subscriptions_service.create_subscription(db, body)


@router.get("/")
async def get_company_subscriptions(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await subscriptions_service.get_company_subscriptions(
        db, company_id, skip=pg.skip, limit=pg.limit,
    )


@router.get("/rules/{sub_id}")
async def get_subscription(sub_id: str, request: Request) -> dict:
    db = request.app.mongodb
    return await subscriptions_service.get_subscription(db, sub_id)


@router.put("/rules/{sub_id}")
async def update_subscription(
    sub_id: str, body: UpdateSubscriptionRequest, request: Request,
) -> dict:
    db = request.app.mongodb
    return await subscriptions_service.update_subscription(db, sub_id, body)


@router.delete("/rules/{sub_id}")
async def delete_subscription(sub_id: str, request: Request) -> MessageResponse:
    db = request.app.mongodb
    await subscriptions_service.delete_subscription(db, sub_id)
    return MessageResponse(message="Subscription deleted successfully")


# --- Notification Channels ---

@router.post("/channels")
async def create_channel(body: CreateChannelRequest, request: Request) -> dict:
    db = request.app.mongodb
    return await subscriptions_service.create_channel(db, body)


@router.get("/channels")
async def get_company_channels(
    request: Request,
    company_id: str = Query(..., description="Company ID"),
    pg: PaginationParams = Depends(PaginationParams),
) -> List[dict]:
    db = request.app.mongodb
    return await subscriptions_service.get_company_channels(
        db, company_id, skip=pg.skip, limit=pg.limit,
    )


@router.get("/channels/{channel_id}")
async def get_channel(channel_id: str, request: Request) -> dict:
    db = request.app.mongodb
    return await subscriptions_service.get_channel(db, channel_id)


@router.put("/channels/{channel_id}")
async def update_channel(
    channel_id: str, body: UpdateChannelRequest, request: Request,
) -> dict:
    db = request.app.mongodb
    return await subscriptions_service.update_channel(db, channel_id, body)


@router.delete("/channels/{channel_id}")
async def delete_channel(channel_id: str, request: Request) -> MessageResponse:
    db = request.app.mongodb
    await subscriptions_service.delete_channel(db, channel_id)
    return MessageResponse(message="Notification channel deleted successfully")


@router.post("/channels/{channel_id}/test")
async def test_channel(channel_id: str, request: Request) -> MessageResponse:
    db = request.app.mongodb
    rabbitmq = request.app.rabbitmq
    await subscriptions_service.send_test_notification(db, channel_id, rabbitmq)
    return MessageResponse(message="Test notification sent")
