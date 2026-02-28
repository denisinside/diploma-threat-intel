"""
Leak Scraper - Telegram combo list file collector.
Modes: watcher, full-sync, full-sync-then-watcher.
"""
import os
import sys
import asyncio

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from loguru import logger

from config.config import settings
from core.client import create_client, ensure_authorized
from core.scraper import run_watcher_cycle, run_full_sync
from core.queue import get_publisher
from database.redis import get_redis


async def _watcher_job():
    """Single watcher cycle."""
    client = None
    try:
        client = await create_client(
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
            settings.TELEGRAM_SESSION_NAME,
            settings.TELEGRAM_SESSION_PATH or "",
        )
        if not await ensure_authorized(client):
            logger.error("Authorization failed")
            return
        redis = get_redis()
        publisher = get_publisher(settings.RABBITMQ_URL)
        await run_watcher_cycle(
            client,
            channels=settings.channels_list,
            storage_path=settings.STORAGE_PATH,
            allowed_extensions=settings.allowed_extensions_set,
            api_url=settings.API_GATEWAY_URL,
            max_concurrent=settings.MAX_CONCURRENT_DOWNLOADS,
            redis=redis,
            publisher=publisher,
            batch_delay_seconds=settings.MESSAGE_BATCH_DELAY_SECONDS,
            batch_size=settings.MESSAGE_BATCH_SIZE,
            channel_delay_seconds=settings.CHANNEL_DELAY_SECONDS,
        )
    finally:
        if client:
            await client.disconnect()


async def _full_sync_once():
    """Run full sync once."""
    client = None
    try:
        client = await create_client(
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH,
            settings.TELEGRAM_SESSION_NAME,
            settings.TELEGRAM_SESSION_PATH or "",
        )
        if not await ensure_authorized(client):
            logger.error("Authorization failed")
            return
        redis = get_redis()
        publisher = get_publisher(settings.RABBITMQ_URL)
        await run_full_sync(
            client,
            channels=settings.channels_list,
            storage_path=settings.STORAGE_PATH,
            allowed_extensions=settings.allowed_extensions_set,
            api_url=settings.API_GATEWAY_URL,
            max_concurrent=settings.MAX_CONCURRENT_DOWNLOADS,
            redis=redis,
            publisher=publisher,
            batch_delay_seconds=settings.MESSAGE_BATCH_DELAY_SECONDS,
            batch_size=settings.MESSAGE_BATCH_SIZE,
            channel_delay_seconds=settings.CHANNEL_DELAY_SECONDS,
        )
    finally:
        if client:
            await client.disconnect()


async def _watcher_loop(interval_minutes: int):
    """Run watcher in a loop with interval."""
    while True:
        await _watcher_job()
        logger.info(f"Next check in {interval_minutes} minute(s)")
        await asyncio.sleep(interval_minutes * 60)


def _run_reset(channel_ids: list):
    """Reset full_sync checkpoint to 0 for given channels (or all if empty)."""
    redis = get_redis()
    channels = channel_ids if channel_ids else settings.channels_list
    if not channels:
        logger.error("No channels to reset. Provide channel IDs or set LEAK_SCRAPER_CHANNELS.")
        sys.exit(1)
    for cid in channels:
        redis.set_last_message_id_full_sync(cid, 0)
        logger.info(f"Reset full_sync checkpoint to 0 for channel {cid}")
    logger.info(f"Reset done for {len(channels)} channel(s)")


def _run_set_from(channel_id: str, message_id: int):
    """Set full_sync checkpoint for channel to start from given message."""
    redis = get_redis()
    redis.set_last_message_id_full_sync(channel_id, message_id)
    logger.info(f"Set full_sync checkpoint for {channel_id} to message {message_id}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Leak Scraper - Telegram combo file collector")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["watcher", "full-sync", "full-sync-then-watcher"],
        default=os.getenv("LEAK_SCRAPER_MODE", "watcher"),
        help="Mode: watcher, full-sync, or full-sync-then-watcher",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=settings.WATCHER_INTERVAL_MINUTES,
        help="Watcher interval in minutes (default from config)",
    )
    parser.add_argument(
        "--reset",
        nargs="*",
        metavar="CHANNEL_ID",
        default=None,
        help="Reset full_sync checkpoint to 0. No args = all channels from config, or list channel IDs",
    )
    parser.add_argument(
        "--setFrom",
        nargs=2,
        metavar=("CHANNEL_ID", "MESSAGE_ID"),
        default=None,
        help="Set full_sync checkpoint: channel_id message_id (full_sync will start from that message)",
    )
    args = parser.parse_args()

    try:
        get_redis()
    except Exception as e:
        logger.error(f"Redis connection failed (required): {e}")
        sys.exit(1)

    if args.reset is not None:
        _run_reset(args.reset)
        return

    if args.setFrom is not None:
        channel_id, msg_id_str = args.setFrom
        try:
            msg_id = int(msg_id_str)
        except ValueError:
            logger.error(f"Invalid message_id: {msg_id_str}")
            sys.exit(1)
        _run_set_from(channel_id, msg_id)
        return

    if not settings.channels_list:
        logger.error("LEAK_SCRAPER_CHANNELS is empty. Set comma-separated channel IDs in .env")
        sys.exit(1)

    logger.info(f"Starting leak-scraper in '{args.mode}' mode, channels: {settings.channels_list}")

    if args.mode == "watcher":
        try:
            asyncio.run(_watcher_loop(args.interval))
        except KeyboardInterrupt:
            logger.info("Stopping watcher...")

    elif args.mode == "full-sync":
        asyncio.run(_full_sync_once())
        logger.info("Full sync completed")

    elif args.mode == "full-sync-then-watcher":
        logger.info("Running full sync first...")
        asyncio.run(_full_sync_once())
        logger.info("Full sync done, starting watcher...")
        try:
            asyncio.run(_watcher_loop(args.interval))
        except KeyboardInterrupt:
            logger.info("Stopping watcher...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal: {e}")
        sys.exit(1)
