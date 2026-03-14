import repositories.subscriptions_repo as subscriptions_repo
from models.requests.subscriptions_requests import (
    CreateSubscriptionRequest, UpdateSubscriptionRequest,
    CreateChannelRequest, UpdateChannelRequest,
    validate_channel_config,
)
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException
from typing import TYPE_CHECKING, List
from datetime import datetime, timezone
import httpx
from models.enums import ChannelType
from shared.models.notification_event import (
    NotificationEvent,
    NotificationEventType,
    NotificationSeverity,
)

if TYPE_CHECKING:
    from messaging.rabbitmq import RabbitMQPublisher


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
    return _normalize_channel(channel)


def _normalize_channel(doc: dict) -> dict:
    """Ensure channel has expected keys for API response (handles legacy/migrated data)."""
    return {
        **doc,
        "name": doc.get("name") or doc.get("channel_name") or "",
        "channel_type": doc.get("channel_type") or "",
        "config": doc.get("config") if doc.get("config") is not None else {},
    }


async def get_company_channels(
    db: AsyncIOMotorDatabase, company_id: str, skip: int = 0, limit: int = 0,
) -> List[dict]:
    channels = await subscriptions_repo.get_channels_by_company(
        db, company_id, skip=skip, limit=limit,
    )
    return [_normalize_channel(c) for c in channels]


async def update_channel(
    db: AsyncIOMotorDatabase, channel_id: str, request: UpdateChannelRequest,
) -> dict:
    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "config" in update_data or "channel_type" in update_data:
        existing = await subscriptions_repo.get_channel_by_id(db, channel_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Notification channel not found")
        effective_channel_type = update_data.get("channel_type", existing["channel_type"])
        effective_config = update_data.get("config", existing.get("config", {}))
        validate_channel_config(ChannelType(effective_channel_type), effective_config)

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


async def send_test_notification(
    db: AsyncIOMotorDatabase, channel_id: str, rabbitmq: "RabbitMQPublisher",
) -> None:
    channel = await get_channel(db, channel_id)
    if not channel.get("is_enabled"):
        raise HTTPException(status_code=400, detail="Channel is disabled. Enable it first.")
    err = await _send_test_direct(channel)
    if err:
        raise HTTPException(status_code=502, detail=err)


async def _send_test_direct(channel: dict) -> str | None:
    """Send test message directly and return error string if failed, else None."""
    channel_type = channel.get("channel_type")
    config = channel.get("config") or {}
    text = "Test notification from C.L.E.A.R. platform"
    timeout = 15.0

    if channel_type == "telegram":
        bot_token = config.get("bot_token")
        chat_id = config.get("chat_id")
        if not bot_token or not chat_id:
            return "Telegram config missing: bot_token and chat_id are required."
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": str(chat_id), "text": text},
                    timeout=timeout,
                )
                body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                if not r.is_success:
                    desc = body.get("description", r.text or r.reason_phrase)
                    return f"Telegram API error ({r.status_code}): {desc}"
        except httpx.TimeoutException:
            return "Telegram API timeout. Check bot token and network."
        except httpx.RequestError as e:
            return f"Telegram request failed: {e!s}"
        except Exception as e:
            return f"Telegram error: {e!s}"
        return None

    if channel_type == "slack":
        url = config.get("webhook_url")
        if not url:
            return "Slack config missing: webhook_url required."
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json={"text": text}, timeout=timeout)
                if not r.is_success:
                    return f"Slack webhook error ({r.status_code}): {r.text[:200]}"
        except httpx.TimeoutException:
            return "Slack webhook timeout."
        except httpx.RequestError as e:
            return f"Slack request failed: {e!s}"
        return None

    if channel_type == "discord":
        url = config.get("webhook_url")
        if not url:
            return "Discord config missing: webhook_url required."
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json={"content": text}, timeout=timeout)
                if not r.is_success:
                    body = r.json() if "application/json" in (r.headers.get("content-type") or "") else {}
                    msg = body.get("message", r.text)[:200]
                    return f"Discord webhook error ({r.status_code}): {msg}"
        except httpx.TimeoutException:
            return "Discord webhook timeout."
        except httpx.RequestError as e:
            return f"Discord request failed: {e!s}"
        return None

    if channel_type == "webhook":
        url = config.get("url")
        if not url:
            return "Webhook config missing: url required."
        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json={"message": text, "test": True}, timeout=timeout)
                if not r.is_success:
                    return f"Webhook error ({r.status_code}): {r.text[:200]}"
        except httpx.TimeoutException:
            return "Webhook timeout."
        except httpx.RequestError as e:
            return f"Webhook request failed: {e!s}"
        return None

    return f"Sync test not implemented for channel type: {channel_type}. Use async delivery."
