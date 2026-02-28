"""
RabbitMQ publisher: sends events when new leak source is registered.
combo-parser consumes these events to process files.
"""
import json
import pika
from typing import Optional
from loguru import logger

QUEUE_NAME = "leak_sources_pending"

HEARTBEAT = 1000 
BLOCKED_TIMEOUT = 1000


class LeakQueuePublisher:
    """Publishes leak source events to RabbitMQ. Auto-reconnects on connection loss."""

    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel = None

    def _ensure_connected(self) -> bool:
        """Ensure connection is open. Reconnect if closed. Returns True if ready to publish."""
        try:
            if self.connection and not self.connection.is_closed and self.channel and self.channel.is_open:
                return True
        except Exception:
            pass
        self.disconnect()
        self.connect()
        return self.channel is not None

    def connect(self) -> None:
        params = pika.URLParameters(self.rabbitmq_url)
        params.heartbeat = HEARTBEAT
        params.blocked_connection_timeout = BLOCKED_TIMEOUT
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=QUEUE_NAME, durable=True)
        logger.info("RabbitMQ publisher connected")

    def disconnect(self) -> None:
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ publisher disconnected")
        except Exception:
            pass
        self.connection = None
        self.channel = None

    def publish(self, source_id: str, local_path: str, password: Optional[str] = None) -> None:
        """Publish event for combo-parser to consume."""
        if not self.channel:
            logger.warning("RabbitMQ not connected, skipping publish")
            return
        message = {
            "source_id": source_id,
            "local_path": local_path,
        }
        if password:
            message["password"] = password
        try:
            self.channel.basic_publish(
                exchange="",
                routing_key=QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2),  # persistent
            )
            logger.debug(f"Published to queue: source_id={source_id}")
        except Exception as e:
            logger.warning(f"Publish failed, reconnecting: {e}")
            if self._ensure_connected():
                try:
                    self.channel.basic_publish(
                        exchange="",
                        routing_key=QUEUE_NAME,
                        body=json.dumps(message),
                        properties=pika.BasicProperties(delivery_mode=2),
                    )
                    logger.debug(f"Published to queue (retry): source_id={source_id}")
                except Exception as retry_e:
                    logger.warning(f"Publish retry failed: {retry_e}")


_publisher: Optional[LeakQueuePublisher] = None


def get_publisher(rabbitmq_url: str) -> LeakQueuePublisher:
    """Get or create publisher singleton."""
    global _publisher
    if _publisher is None:
        _publisher = LeakQueuePublisher(rabbitmq_url)
        _publisher.connect()
    return _publisher
