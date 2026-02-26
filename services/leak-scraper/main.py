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
        await run_watcher_cycle(
            client,
            channels=settings.channels_list,
            storage_path=settings.STORAGE_PATH,
            allowed_extensions=settings.allowed_extensions_set,
            api_url=settings.API_GATEWAY_URL,
            max_concurrent=settings.MAX_CONCURRENT_DOWNLOADS,
            redis=redis,
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
        await run_full_sync(
            client,
            channels=settings.channels_list,
            storage_path=settings.STORAGE_PATH,
            allowed_extensions=settings.allowed_extensions_set,
            api_url=settings.API_GATEWAY_URL,
            max_concurrent=settings.MAX_CONCURRENT_DOWNLOADS,
            redis=redis,
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
    args = parser.parse_args()

    if not settings.channels_list:
        logger.error("LEAK_SCRAPER_CHANNELS is empty. Set comma-separated channel IDs in .env")
        sys.exit(1)

    try:
        get_redis()
    except Exception as e:
        logger.error(f"Redis connection failed (required): {e}")
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
