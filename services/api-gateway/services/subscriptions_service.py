import repositories.subscriptions_repo as subscriptions_repo
from models.requests.subscriptions_requests import (
    CreateSubscriptionRequest, UpdateSubscriptionRequest,
    CreateChannelRequest, UpdateChannelRequest,
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import List
from datetime import datetime, timezone


# --- Subscriptions ---

async def create_subscription(db: AsyncIOMotorDatabase, request: CreateSubscriptionRequest) -> dict:
    sub_data = request.model_dump()
    sub_data["created_at"] = datetime.now(timezone.utc)
    sub_data["updated_at"] = datetime.now(timezone.utc)
    return await subscriptions_repo.create_subscription(db, sub_data)


async def get_subscription(db: AsyncIOMotorDatabase, sub_id: str) -> dict:
    sub = await subscriptions_repo.get_subscription_by_id(db, sub_id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


async def get_company_subscriptions(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await subscriptions_repo.get_subscriptions_by_company(
        db, company_id, skip=skip, limit=limit,
    )


async def update_subscription(
    db: AsyncIOMotorDatabase, sub_id: str, request: UpdateSubscriptionRequest,
) -> dict:
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc)
    sub = await subscriptions_repo.update_subscription(db, sub_id, update_data)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


async def delete_subscription(db: AsyncIOMotorDatabase, sub_id: str) -> bool:
    deleted = await subscriptions_repo.delete_subscription(db, sub_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return True


# --- Notification Channels ---

async def create_channel(db: AsyncIOMotorDatabase, request: CreateChannelRequest) -> dict:
    channel_data = request.model_dump()
    channel_data["is_enabled"] = True
    channel_data["created_at"] = datetime.now(timezone.utc)
    channel_data["updated_at"] = datetime.now(timezone.utc)
    return await subscriptions_repo.create_channel(db, channel_data)


async def get_channel(db: AsyncIOMotorDatabase, channel_id: str) -> dict:
    channel = await subscriptions_repo.get_channel_by_id(db, channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    return channel


async def get_company_channels(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    return await subscriptions_repo.get_channels_by_company(
        db, company_id, skip=skip, limit=limit,
    )


async def update_channel(
    db: AsyncIOMotorDatabase, channel_id: str, request: UpdateChannelRequest,
) -> dict:
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    update_data["updated_at"] = datetime.now(timezone.utc)
    channel = await subscriptions_repo.update_channel(db, channel_id, update_data)
    if not channel:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    return channel


async def delete_channel(db: AsyncIOMotorDatabase, channel_id: str) -> bool:
    deleted = await subscriptions_repo.delete_channel(db, channel_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification channel not found")
    return True
