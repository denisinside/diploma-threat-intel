from __future__ import annotations

import json
from datetime import datetime, timezone

import pika
from loguru import logger
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from core.config import settings
from dispatch.router import dispatch_event
from repositories.subscriptions_repo import ensure_indexes, get_processed_events_collection
from shared.models.notification_event import NotificationEvent


def run_consumer() -> None:
    mongo_client = MongoClient(settings.MONGODB_URI)
    db = mongo_client[settings.MONGODB_DB_NAME]
    ensure_indexes(db)

    params = pika.URLParameters(settings.RABBITMQ_URL)
    params.heartbeat = 600
    params.blocked_connection_timeout = 600
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(
        exchange=settings.RABBITMQ_EXCHANGE,
        exchange_type="topic",
        durable=True,
    )
    channel.queue_declare(queue=settings.RABBITMQ_QUEUE, durable=True)
    channel.queue_declare(queue=settings.RABBITMQ_DLQ, durable=True)
    for routing_key in (
        "leak.source.registered",
        "vuln.detected",
        "auth.password_reset_requested",
        "channel.test",
    ):
        channel.queue_bind(
            exchange=settings.RABBITMQ_EXCHANGE,
            queue=settings.RABBITMQ_QUEUE,
            routing_key=routing_key,
        )

    channel.basic_qos(prefetch_count=10)

    def on_message(ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))
            event = NotificationEvent.model_validate(payload)
            if _is_processed(db, event.event_id):
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            delivered = dispatch_event(db, event)
            _mark_processed(db, event.event_id, delivered)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as exc:
            retry_count = int((properties.headers or {}).get("x-retry-count", 0))
            if retry_count >= settings.RABBITMQ_MAX_RETRIES:
                ch.basic_publish(
                    exchange="",
                    routing_key=settings.RABBITMQ_DLQ,
                    body=body,
                    properties=pika.BasicProperties(
                        delivery_mode=2,
                        headers={"x-error": str(exc), "x-retry-count": retry_count},
                    ),
                )
                logger.error(f"Message moved to DLQ after retries: {exc}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            ch.basic_publish(
                exchange=settings.RABBITMQ_EXCHANGE,
                routing_key=method.routing_key,
                body=body,
                properties=pika.BasicProperties(
                    delivery_mode=2,
                    headers={"x-retry-count": retry_count + 1},
                ),
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=settings.RABBITMQ_QUEUE, on_message_callback=on_message)
    logger.info("notification-service is waiting for events")
    try:
        channel.start_consuming()
    finally:
        try:
            connection.close()
        except Exception:
            pass
        mongo_client.close()


def _is_processed(db, event_id: str) -> bool:
    collection = get_processed_events_collection(db)
    return collection.find_one({"event_id": event_id}) is not None


def _mark_processed(db, event_id: str, delivered: int) -> None:
    collection = get_processed_events_collection(db)
    try:
        collection.insert_one(
            {
                "event_id": event_id,
                "delivered_count": delivered,
                "processed_at": datetime.now(timezone.utc),
            }
        )
    except DuplicateKeyError:
        return
