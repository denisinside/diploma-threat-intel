"""
Core scraping logic: process messages, download files, dedup via API, register sources.
Handles TG attachments and cloud links (mega via library, others via Playwright browser).
Respects Telegram rate limits: FloodWaitError handling, batch delays.
State stored in Redis: separate keys for watcher and full_sync.
"""
import asyncio
from pathlib import Path
from telethon.tl.types import MessageMediaDocument
from telethon.errors import FloodWaitError
from loguru import logger

from .client import get_entity
from .downloader import download_file, is_allowed_extension, get_file_extension, compute_sha256
from .api_client import check_hash_exists, register_leak_source
from .extractors.links import extract_cloud_links
from .extractors.passwords import extract_password
from .extractors.cloud import CLOUD_DOWNLOADERS, DEFAULT_CLOUD_DOWNLOADER


async def _register_and_log(
    api_url: str,
    channel_id: str,
    message_id: int,
    local_path: Path,
    sha256: str,
    size_bytes: int,
    publisher=None,
    source: str = "attachment",
    original_url: str = None,
    password: str = None,
) -> bool:
    """Dedup check + register via API + publish to RabbitMQ. Returns True if new source was registered."""
    if await check_hash_exists(api_url, sha256):
        logger.debug(f"Duplicate {sha256[:16]}... - skipping")
        local_path.unlink(missing_ok=True)
        return False
    abs_path = str(Path(local_path).resolve())
    result = await register_leak_source(
        api_url,
        channel_id=channel_id,
        message_id=message_id,
        filename=local_path.name,
        size_bytes=size_bytes,
        sha256=sha256,
        source=source,
        original_url=original_url,
        password=password,
        local_path=abs_path,
    )
    if result and result.get("duplicate"):
        logger.debug(f"Duplicate (409) {sha256[:16]}...")
        local_path.unlink(missing_ok=True)
        return False
    if result:
        logger.info(f"Registered [{source}]: {local_path.name} ({size_bytes} bytes)")
        source_id = result.get("_id", "")
        if publisher and source_id:
            try:
                publisher.publish(source_id, abs_path, password=password)
            except Exception as e:
                logger.warning(f"Failed to publish to queue: {e}")
        return True
    return False


async def _process_attachment(
    message,
    channel_id: str,
    storage_path: str,
    allowed_extensions: set,
    api_url: str,
    publisher=None,
) -> bool:
    """Process a TG file attachment."""
    ext = get_file_extension(message)
    if not is_allowed_extension(ext, allowed_extensions):
        return False
    result = await download_file(message, channel_id, storage_path, allowed_extensions)
    if not result:
        return False
    local_path, sha256, size_bytes = result
    password = extract_password(message.message or "")
    return await _register_and_log(
        api_url, channel_id, message.id, local_path, sha256, size_bytes,
        publisher=publisher, source="attachment", password=password,
    )


async def _process_cloud_links(
    message,
    channel_id: str,
    storage_path: str,
    allowed_extensions: set,
    api_url: str,
    publisher=None,
) -> bool:
    """Extract cloud links from text, download files, register."""
    text = message.message or ""
    links = extract_cloud_links(text)
    if not links:
        return False

    password = extract_password(text)
    any_registered = False
    dest_dir = str(Path(storage_path) / channel_id.replace("-", "_"))

    for service, url in links:
        downloader = CLOUD_DOWNLOADERS.get(service, DEFAULT_CLOUD_DOWNLOADER)
        try:
            await asyncio.sleep(2)
            local_path = await downloader(url, dest_dir)
            if not local_path or not local_path.exists():
                continue

            ext = local_path.suffix.lstrip(".").lower()
            if not is_allowed_extension(ext, allowed_extensions):
                logger.debug(f"Cloud file {local_path.name}: extension {ext} not allowed, removing")
                local_path.unlink(missing_ok=True)
                continue

            sha256 = compute_sha256(local_path)
            size_bytes = local_path.stat().st_size
            registered = await _register_and_log(
                api_url, channel_id, message.id, local_path, sha256, size_bytes,
                publisher=publisher, source="url", original_url=url, password=password,
            )
            if registered:
                any_registered = True
        except Exception as e:
            logger.error(f"Cloud download [{service}] {url}: {e}")
    return any_registered


async def process_message(
    client,
    message,
    channel_id: str,
    storage_path: str,
    allowed_extensions: set,
    api_url: str,
    semaphore: asyncio.Semaphore,
    publisher=None,
) -> bool:
    """
    Process single message: handle attachment OR cloud links.
    Returns True if at least one new file was registered.
    """
    async with semaphore:
        # 1) TG attachment
        if message.media and isinstance(message.media, MessageMediaDocument):
            result = await _process_attachment(
                message, channel_id, storage_path, allowed_extensions, api_url,
                publisher=publisher,
            )
            if result:
                return True

        # 2) Cloud links in message text
        return await _process_cloud_links(
            message, channel_id, storage_path, allowed_extensions, api_url,
            publisher=publisher,
        )


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
    publisher=None,
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
                    publisher=publisher,
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
    publisher=None,
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
            if last_id == 0:
                entity = await get_entity(client, channel_id)
                latest = await client.get_messages(entity, limit=1)
                if latest and latest[0]:
                    last_id = latest[0].id
                    redis.set_last_message_id_watcher(channel_id, last_id)
                    logger.info(f"First watcher run: set checkpoint to latest msg {last_id} for {channel_id}")
                else:
                    logger.info(f"Channel {channel_id} is empty, skipping")
                    continue
            logger.info(f"Checking channel {channel_id} from msg {last_id}")
            await scrape_channel(
                client, channel_id, last_id, storage_path,
                allowed_extensions, api_url, max_concurrent,
                redis, "watcher", publisher=publisher,
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
    publisher=None,
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
                redis, "full_sync", publisher=publisher,
                batch_delay_seconds=batch_delay_seconds,
                batch_size=batch_size,
            )
        except Exception as e:
            logger.error(f"Channel {channel_id}: {e}")
