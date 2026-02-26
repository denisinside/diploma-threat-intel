"""
Redis client for leak-scraper: separate keys for watcher and full_sync.
When full_sync message_id exceeds watcher's, writes to both keys.
"""
import redis
from typing import Optional
from loguru import logger
from config.config import settings


KEY_WATCHER = "leak_scraper:watcher:{channel_id}:last_msg"
KEY_FULL_SYNC = "leak_scraper:full_sync:{channel_id}:last_msg"


class LeakScraperRedis:
    """Redis client for leak-scraper state. Required - no fallback."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    def connect(self) -> None:
        """Initialize Redis connection. Raises on failure."""
        redis_config = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB,
            "decode_responses": True,
            "socket_connect_timeout": 5,
            "socket_timeout": 5,
        }
        if settings.REDIS_PASSWORD:
            redis_config["password"] = settings.REDIS_PASSWORD

        self.client = redis.Redis(**redis_config)
        self.client.ping()
        logger.info(f"Connected to Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")

    def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client is not None:
            self.client.close()
            logger.info("Disconnected from Redis")
            self.client = None

    def get_last_message_id_watcher(self, channel_id: str) -> int:
        """Get last processed message ID for watcher. Returns 0 if not set."""
        if self.client is None:
            raise RuntimeError("Redis not connected")
        try:
            val = self.client.get(KEY_WATCHER.format(channel_id=channel_id))
            return int(val) if val else 0
        except Exception as e:
            logger.warning(f"Error getting watcher last_msg from Redis: {e}")
            return 0

    def set_last_message_id_watcher(self, channel_id: str, message_id: int) -> None:
        """Set last processed message ID for watcher."""
        if self.client is None:
            raise RuntimeError("Redis not connected")
        try:
            self.client.set(KEY_WATCHER.format(channel_id=channel_id), str(message_id))
        except Exception as e:
            logger.warning(f"Error setting watcher last_msg in Redis: {e}")

    def get_last_message_id_full_sync(self, channel_id: str) -> int:
        """Get last processed message ID for full_sync. Returns 0 if not set."""
        if self.client is None:
            raise RuntimeError("Redis not connected")
        try:
            val = self.client.get(KEY_FULL_SYNC.format(channel_id=channel_id))
            return int(val) if val else 0
        except Exception as e:
            logger.warning(f"Error getting full_sync last_msg from Redis: {e}")
            return 0

    def set_last_message_id_full_sync(self, channel_id: str, message_id: int) -> None:
        """Set last processed message ID for full_sync."""
        if self.client is None:
            raise RuntimeError("Redis not connected")
        try:
            self.client.set(KEY_FULL_SYNC.format(channel_id=channel_id), str(message_id))
        except Exception as e:
            logger.warning(f"Error setting full_sync last_msg in Redis: {e}")

    def set_last_message_id(
        self, channel_id: str, message_id: int, mode: str
    ) -> None:
        """
        Set last message ID for the given mode.
        If mode is full_sync and message_id > watcher's value, also update watcher.
        """
        if mode == "watcher":
            self.set_last_message_id_watcher(channel_id, message_id)
        elif mode == "full_sync":
            self.set_last_message_id_full_sync(channel_id, message_id)
            watcher_val = self.get_last_message_id_watcher(channel_id)
            if message_id > watcher_val:
                self.set_last_message_id_watcher(channel_id, message_id)
        else:
            raise ValueError(f"Unknown mode: {mode}")


_redis: Optional[LeakScraperRedis] = None


def get_redis() -> LeakScraperRedis:
    """Get Redis client. Connects on first call. Raises if Redis unavailable."""
    global _redis
    if _redis is None:
        _redis = LeakScraperRedis()
        _redis.connect()
    return _redis
