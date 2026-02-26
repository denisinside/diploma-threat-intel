"""
Download files from Telegram messages with extension filter and SHA-256 hashing.
"""
import asyncio
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from telethon.tl.types import MessageMediaDocument, MessageMediaWebPage
from telethon.errors import FloodWaitError
from loguru import logger


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of file (chunked for large files)."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


def get_file_extension(message) -> Optional[str]:
    """Extract file extension from MessageMediaDocument. Returns None if not a document."""
    if not message.media or isinstance(message.media, MessageMediaWebPage):
        return None
    if not isinstance(message.media, MessageMediaDocument):
        return None
    ext = getattr(message.file, "ext", None) if message.file else None
    if ext:
        return ext.lower().lstrip(".")
    # Fallback from filename
    name = getattr(message.file, "name", None) if message.file else None
    if name:
        return Path(name).suffix.lstrip(".").lower()
    return None


def is_allowed_extension(ext: Optional[str], allowed: set) -> bool:
    """Check if extension is in allowed list."""
    if not ext:
        return False
    return ext.lower() in allowed


async def download_file(
    message,
    channel_id: str,
    storage_path: str,
    allowed_extensions: set,
    max_retries: int = 3,
) -> Optional[Tuple[Path, str, int]]:
    """
    Download file from message if it matches allowed extensions.
    Returns (local_path, sha256, size_bytes) or None.
    """
    ext = get_file_extension(message)
    if not is_allowed_extension(ext, allowed_extensions):
        logger.debug(f"Message {message.id}: skipped extension {ext}")
        return None

    channel_dir = Path(storage_path) / channel_id.replace("-", "_")
    channel_dir.mkdir(parents=True, exist_ok=True)

    original_name = getattr(message.file, "name", None) if message.file else f"document.{ext}"
    base_name = Path(original_name).stem
    suffix = Path(original_name).suffix or f".{ext}"
    unique_filename = f"{message.id}-{base_name}{suffix}"
    local_path = channel_dir / unique_filename

    if local_path.exists():
        sha = compute_sha256(local_path)
        size = local_path.stat().st_size
        return (local_path, sha, size)

    for attempt in range(max_retries):
        try:
            downloaded = await message.download_media(file=str(local_path))
            if downloaded and Path(downloaded).exists():
                sha = compute_sha256(Path(downloaded))
                size = Path(downloaded).stat().st_size
                return (Path(downloaded), sha, size)
        except FloodWaitError as e:
            logger.warning(f"FloodWait: sleeping {e.seconds}s")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2**attempt)
    return None
