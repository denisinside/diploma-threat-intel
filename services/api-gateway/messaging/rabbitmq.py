from __future__ import annotations

import json
from typing import Optional

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message, RobustChannel, RobustConnection
from loguru import logger

from shared.models.notification_event import NotificationEvent


class RabbitMQPublisher:
    def __init__(self, url: str, exchange_name: str = "notifications.events"):
        self.url = url
        self.exchange_name = exchange_name
        self.connection: Optional[RobustConnection] = None
        self.channel: Optional[RobustChannel] = None
        self.exchange: Optional[aio_pika.abc.AbstractRobustExchange] = None

    async def connect(self) -> None:
        self.connection = await aio_pika.connect_robust(self.url)
        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=50)
        self.exchange = await self.channel.declare_exchange(
            self.exchange_name,
            ExchangeType.TOPIC,
            durable=True,
        )
        logger.info(f"RabbitMQ publisher connected: exchange={self.exchange_name}")

    async def close(self) -> None:
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            logger.info("RabbitMQ publisher disconnected")
        self.connection = None
        self.channel = None
        self.exchange = None

    async def publish_event(self, event: NotificationEvent) -> None:
        if not self.exchange:
            raise RuntimeError("RabbitMQ publisher is not initialized")

        body = json.dumps(event.model_dump(mode="json")).encode("utf-8")
        message = Message(
            body=body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=event.event_id,
            type=event.event_type.value,
            headers={"schema_version": event.version},
        )
        await self.exchange.publish(message, routing_key=event.event_type.value)
