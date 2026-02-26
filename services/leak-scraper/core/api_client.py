"""
API client for leak-scraper: check hash dedup and register new leak sources.
"""
import httpx
from datetime import datetime, timezone
from typing import Optional
from loguru import logger


async def check_hash_exists(api_url: str, sha256: str) -> bool:
    """Check if leak source with given sha256 already exists. Returns True if duplicate."""
    url = f"{api_url.rstrip('/')}/leaks/check-hash/{sha256}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url)
            if r.status_code == 200:
                data = r.json()
                return data.get("exists", False)
    except Exception as e:
        logger.warning(f"Check hash failed: {e}")
    return False


async def register_leak_source(
    api_url: str,
    channel_id: str,
    message_id: int,
    filename: str,
    size_bytes: int,
    sha256: str,
) -> Optional[dict]:
    """
    Register new leak source via API. Returns created source dict or None on failure.
    Raises no exception on 409 (duplicate) - caller should handle.
    """
    url = f"{api_url.rstrip('/')}/leaks/sources/telegram"
    payload = {
        "channel_id": channel_id,
        "message_id": message_id,
        "filename": filename,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url, json=payload)
            if r.status_code in (200, 201):
                return r.json()
            if r.status_code == 409:
                logger.info(f"Duplicate sha256 {sha256[:16]}... - skipped")
                return None
            logger.warning(f"API error {r.status_code}: {r.text}")
    except Exception as e:
        logger.error(f"Register leak source failed: {e}")
    return None
