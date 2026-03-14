from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from loguru import logger
from pymongo.database import Database

from core.config import settings
from providers.discord import send_discord_message
from providers.email import send_email
from providers.signal import send_signal_message
from providers.slack import send_slack_message
from providers.telegram import send_telegram_message
from providers.webhook import send_webhook_message
from repositories.subscriptions_repo import (
    get_channel_by_id,
    get_company_subscriptions,
    get_enabled_channels,
)
from shared.models.notification_event import NotificationEvent, NotificationEventType

SEVERITY_WEIGHT = {
    "critical": 5,
    "high": 4,
    "medium": 3,
    "low": 2,
    "info": 1,
    "unknown": 0,
}


def dispatch_event(db: Database, event: NotificationEvent) -> int:
    if event.event_type == NotificationEventType.CHANNEL_TEST:
        return _dispatch_channel_test(db, event)
    company_ids = _resolve_company_ids(db, event)
    # #region agent log
    try:
        import json, os
        _lp = os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug-09ba45.log")
        with open(_lp, "a", encoding="utf-8") as _f:
            _f.write(json.dumps({"hypothesisId":"B","location":"router.py:dispatch_event","message":"company_ids resolved","data":{"event_type":event.event_type.value,"event_id":event.event_id,"company_ids":company_ids,"company_count":len(company_ids)},"timestamp":int(__import__("time").time()*1000)}) + "\n")
    except Exception:
        pass
    # #endregion
    if event.event_type == NotificationEventType.VULN_DETECTED:
        _create_tickets_for_matching_vuln(db, event, company_ids)
    delivered = 0
    for company_id in company_ids:
        channels = get_enabled_channels(db, company_id)
        if not channels:
            continue
        message_text = _build_message(event)
        subject = f"[C.L.E.A.R.] {event.event_type.value}"
        for channel in channels:
            try:
                _send_to_channel(channel, message_text, subject)
                delivered += 1
            except Exception as exc:
                logger.warning(
                    f"Delivery failed event={event.event_id} channel={channel.get('_id')}: {exc}"
                )
    return delivered


def _dispatch_channel_test(db: Database, event: NotificationEvent) -> int:
    channel_id = event.data.get("channel_id")
    if not channel_id:
        logger.warning("channel.test event missing channel_id")
        return 0
    channel = get_channel_by_id(db, channel_id)
    if not channel or not channel.get("is_enabled"):
        logger.warning(f"channel.test: channel {channel_id} not found or disabled")
        return 0
    message_text = event.data.get("message", _build_message(event))
    subject = "[C.L.E.A.R.] Test notification"
    try:
        _send_to_channel(channel, message_text, subject)
        return 1
    except Exception as exc:
        logger.warning(f"channel.test delivery failed channel={channel_id}: {exc}")
        raise


def _resolve_company_ids(db: Database, event: NotificationEvent) -> list[str]:
    if event.company_scope:
        return event.company_scope
    result: list[str] = []
    companies = db["subscriptions"].distinct("company_id")
    for company_id in companies:
        rules = get_company_subscriptions(db, company_id)
        for rule in rules:
            matched = _event_matches_rule(event, rule)
            # #region agent log
            try:
                import json, os
                _lp = os.path.join(os.path.dirname(__file__), "..", "..", "..", "debug-09ba45.log")
                haystack = " ".join(str(x).lower() for x in [event.data.get("vuln_id"), event.data.get("summary"), event.data.get("aliases"), event.data.get("affected_packages", [])]) if event.event_type.value.startswith("vuln.") else ""
                with open(_lp, "a", encoding="utf-8") as _f:
                    _f.write(json.dumps({"hypothesisId":"C","location":"router.py:_resolve_company_ids","message":"rule check","data":{"company_id":company_id,"keyword":str(rule.get("keyword","")),"asset_id":str(rule.get("asset_id","")),"sub_type":rule.get("sub_type"),"matched":matched,"haystack_preview":haystack[:200] if haystack else "","event_type":event.event_type.value},"timestamp":int(__import__("time").time()*1000)}) + "\n")
            except Exception:
                pass
            # #endregion
            if matched:
                result.append(company_id)
                break
    return result


def _event_matches_rule(event: NotificationEvent, rule: dict[str, Any]) -> bool:
    sub_type = rule.get("sub_type")
    keyword = str(rule.get("keyword", "")).strip().lower()
    if not keyword:
        return False

    if sub_type == "leak" and event.event_type.value.startswith("leak."):
        haystack = " ".join(
            str(x).lower()
            for x in [
                event.data.get("name"),
                event.data.get("origin_url"),
                event.data.get("sha256"),
                event.data.get("metadata"),
            ]
        )
        return keyword in haystack

    if sub_type == "vulnerability" and event.event_type.value.startswith("vuln."):
        if not _is_severity_allowed(event.severity.value, str(rule.get("min_severity", "low"))):
            return False
        haystack = " ".join(
            str(x).lower()
            for x in [
                event.data.get("vuln_id"),
                event.data.get("summary"),
                event.data.get("aliases"),
                event.data.get("affected_packages", []),
            ]
        )
        return keyword in haystack

    return False


def _is_severity_allowed(event_severity: str, min_severity: str) -> bool:
    return SEVERITY_WEIGHT.get(event_severity, 0) >= SEVERITY_WEIGHT.get(min_severity, 0)


def _severity_to_priority(severity: str) -> str:
    return severity if severity in ("critical", "high", "medium", "low") else "medium"


def _create_tickets_for_matching_vuln(
    db: Database, event: NotificationEvent, company_ids: list[str],
) -> None:
    vuln_id = event.data.get("vuln_id")
    if not vuln_id:
        return
    priority = _severity_to_priority(event.severity.value)
    now = datetime.now(timezone.utc)
    for company_id in company_ids:
        rules = get_company_subscriptions(db, company_id)
        for rule in rules:
            if not _event_matches_rule(event, rule):
                continue
            asset_id = rule.get("asset_id")
            if not asset_id:
                continue
            existing = db["tickets"].find_one({
                "company_id": company_id,
                "asset_id": asset_id,
                "vulnerability_id": vuln_id,
            })
            if existing:
                continue
            try:
                db["tickets"].insert_one({
                    "company_id": company_id,
                    "asset_id": asset_id,
                    "vulnerability_id": vuln_id,
                    "status": "open",
                    "priority": priority,
                    "detected_at": now,
                    "resolved_at": None,
                    "created_at": now,
                    "updated_at": now,
                })
                logger.info(f"Auto-created ticket company={company_id} asset={asset_id} vuln={vuln_id}")
            except Exception as exc:
                logger.warning(f"Failed to create ticket for vuln={vuln_id}: {exc}")


def _format_datetime(dt: datetime) -> str:
    return dt.strftime("%d %b %Y, %H:%M UTC")


def _build_message(event: NotificationEvent) -> str:
    occurred = _format_datetime(event.occurred_at)
    if event.event_type == NotificationEventType.LEAK_SOURCE_REGISTERED:
        data = {k: v for k, v in event.data.items() if k not in ("sha256", "metadata")}
        return (
            f"Event: {event.event_type.value}\n"
            f"Source: {event.source}\n"
            f"Occurred at: {occurred}\n"
            f"Data: {data}"
        )
    return (
        f"Event: {event.event_type.value}\n"
        f"Severity: {event.severity.value}\n"
        f"Source: {event.source}\n"
        f"Occurred at: {occurred}\n"
        f"Data: {event.data}"
    )


def _send_to_channel(channel: dict[str, Any], text: str, subject: str) -> None:
    channel_type = channel.get("channel_type")
    config = channel.get("config") or {}
    timeout = settings.REQUEST_TIMEOUT_SECONDS

    if channel_type == "slack":
        send_slack_message(str(config["webhook_url"]), text, timeout)
        return

    if channel_type == "discord":
        send_discord_message(str(config["webhook_url"]), text, timeout)
        return

    if channel_type == "telegram":
        send_telegram_message(str(config["bot_token"]), str(config["chat_id"]), text, timeout)
        return

    if channel_type == "email":
        recipient = str(config["recipient_email"])
        send_email(
            smtp_host=settings.SMTP_HOST,
            smtp_port=settings.SMTP_PORT,
            smtp_username=settings.SMTP_USERNAME,
            smtp_password=settings.SMTP_PASSWORD,
            smtp_from_email=settings.SMTP_FROM_EMAIL,
            use_tls=settings.SMTP_USE_TLS,
            recipient_email=recipient,
            subject=subject,
            body=text,
        )
        return

    if channel_type == "signal":
        send_signal_message(
            base_url=str(config["base_url"]),
            number=str(config["number"]),
            recipients=[str(x) for x in config.get("recipients", [])],
            text=text,
            timeout=timeout,
        )
        return

    if channel_type == "webhook":
        send_webhook_message(str(config["url"]), text, timeout)
        return

    raise ValueError(f"Unsupported channel type: {channel_type}")
