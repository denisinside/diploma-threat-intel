"""
Download files from mega.nz using mega.py library.
"""
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger


def _download_sync(url: str, dest_dir: str) -> Optional[str]:
    """Synchronous mega download (mega.py is blocking)."""
    from mega import Mega
    mega = Mega()
    m = mega.login()
    return m.download_url(url, dest_path=dest_dir)


async def download_mega(url: str, dest_dir: str) -> Optional[Path]:
    """
    Download file from mega.nz link.
    Returns local Path or None on failure.
    """
    try:
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, _download_sync, url, dest_dir)
        if result and Path(result).exists():
            logger.info(f"Mega downloaded: {result}")
            return Path(result)
    except Exception as e:
        logger.error(f"Mega download failed for {url}: {e}")
    return None
