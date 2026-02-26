"""
Core scraping logic: process messages, download files, dedup via API, register sources.
Respects Telegram rate limits: FloodWaitError handling, batch delays.
State stored in Redis: separate keys for watcher and full_sync.
"""
import asyncio
from telethon.tl.types import MessageMediaDocument
from telethon.errors import FloodWaitError
from loguru import logger

from .client import get_entity
from .downloader import download_file, is_allowed_extension, get_file_extension
from .api_client import check_hash_exists, register_leak_source


async def process_message(
    client,
    message,
    channel_id: str,
    storage_path: str,
    allowed_extensions: set,
    api_url: str,
    semaphore: asyncio.Semaphore,
) -> bool:
    """
    Process single message: download if document with allowed ext, check dedup, register.
    Returns True if new file was registered.
    """
    if not message.media or not isinstance(message.media, MessageMediaDocument):
        return False

    ext = get_file_extension(message)
    if not is_allowed_extension(ext, allowed_extensions):
        return False

    async with semaphore:
        result = await download_file(
            message, channel_id, storage_path, allowed_extensions
        )
        if not result:
            return False

        local_path, sha256, size_bytes = result
        filename = local_path.name

        # Check dedup via API
        if await check_hash_exists(api_url, sha256):
            logger.debug(f"Duplicate {sha256[:16]}... - skipping")
            return False

        # Register
        source = await register_leak_source(
            api_url,
            channel_id=channel_id,
            message_id=message.id,
            filename=filename,
            size_bytes=size_bytes,
            sha256=sha256,
        )
        if source:
            logger.info(f"Registered leak source: {filename} ({size_bytes} bytes)")
            return True
        return False


async def scrape_channel(
    client,
    channel_id: str,
    offset_id: int,
    storage_path: str,
    allowed_extensions: set,
    api_url: str,
    max_concurrent: int,
    redis,
    mode: str,
    batch_delay_seconds: float = 2.0,
    batch_size: int = 50,
) -> int:
    """
    Scrape channel from offset_id. Returns last processed message_id.
    mode: "watcher" or "full_sync" - uses separate Redis keys.
    When full_sync passes watcher (higher msg_id), writes to both keys.
    """
    entity = await get_entity(client, channel_id)
    semaphore = asyncio.Semaphore(max_concurrent)
    last_id = offset_id
    next_offset = offset_id
    processed_count = 0

    while True:
        try:
            async for message in client.iter_messages(
                entity, offset_id=next_offset, reverse=True
            ):
                if not message:
                    continue
                last_id = message.id
                await process_message(
                    client, message, channel_id, storage_path,
                    allowed_extensions, api_url, semaphore,
                )
                redis.set_last_message_id(channel_id, last_id, mode)
                processed_count += 1

                if batch_size > 0 and processed_count % batch_size == 0:
                    logger.debug(f"Batch pause: {batch_delay_seconds}s after {processed_count} msgs")
                    await asyncio.sleep(batch_delay_seconds)
            break
        except FloodWaitError as e:
            logger.warning(f"FloodWait: waiting {e.seconds}s (Telegram rate limit)")
            await asyncio.sleep(e.seconds)
            next_offset = last_id
            continue

    return last_id


async def run_watcher_cycle(
    client,
    channels: list,
    storage_path: str,
    allowed_extensions: set,
    api_url: str,
    max_concurrent: int,
    redis,
    batch_delay_seconds: float = 2.0,
    batch_size: int = 50,
    channel_delay_seconds: float = 3.0,
) -> None:
    """One watcher cycle: check new messages in all channels."""
    for i, channel_id in enumerate(channels):
        if i > 0:
            await asyncio.sleep(channel_delay_seconds)
        try:
            last_id = redis.get_last_message_id_watcher(channel_id)
            logger.info(f"Checking channel {channel_id} from msg {last_id}")
            await scrape_channel(
                client, channel_id, last_id, storage_path,
                allowed_extensions, api_url, max_concurrent,
                redis, "watcher",
                batch_delay_seconds=batch_delay_seconds,
                batch_size=batch_size,
            )
        except Exception as e:
            logger.error(f"Channel {channel_id}: {e}")


async def run_full_sync(
    client,
    channels: list,
    storage_path: str,
    allowed_extensions: set,
    api_url: str,
    max_concurrent: int,
    redis,
    batch_delay_seconds: float = 2.0,
    batch_size: int = 50,
    channel_delay_seconds: float = 3.0,
) -> None:
    """Full sync: resume from last full_sync checkpoint, or 0 if first run."""
    for i, channel_id in enumerate(channels):
        if i > 0:
            await asyncio.sleep(channel_delay_seconds)
        try:
            offset_id = redis.get_last_message_id_full_sync(channel_id)
            logger.info(f"Full sync channel {channel_id} from msg {offset_id}")
            await scrape_channel(
                client, channel_id, offset_id, storage_path,
                allowed_extensions, api_url, max_concurrent,
                redis, "full_sync",
                batch_delay_seconds=batch_delay_seconds,
                batch_size=batch_size,
            )
        except Exception as e:
            logger.error(f"Channel {channel_id}: {e}")
