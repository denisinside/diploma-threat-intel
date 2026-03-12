from __future__ import annotations

from bson.objectid import ObjectId
from pymongo.collection import Collection
from pymongo.database import Database


def get_subscriptions_collection(db: Database) -> Collection:
    return db["subscriptions"]


def get_channels_collection(db: Database) -> Collection:
    return db["notification_channels"]


def get_processed_events_collection(db: Database) -> Collection:
    return db["notification_processed_events"]


def ensure_indexes(db: Database) -> None:
    get_processed_events_collection(db).create_index("event_id", unique=True)


def get_company_subscriptions(db: Database, company_id: str) -> list[dict]:
    return list(get_subscriptions_collection(db).find({"company_id": company_id}))


def get_enabled_channels(db: Database, company_id: str) -> list[dict]:
    return list(
        get_channels_collection(db).find(
            {"company_id": company_id, "is_enabled": True}
        )
    )


def get_channel_by_id(db: Database, channel_id: str) -> dict | None:
    try:
        return get_channels_collection(db).find_one({"_id": ObjectId(channel_id)})
    except Exception:
        return None
