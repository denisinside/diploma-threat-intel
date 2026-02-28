"""
Download files from mediafire.com by scraping the download page.
"""
import re
import httpx
from pathlib import Path
from typing import Optional
from loguru import logger


async def download_mediafire(url: str, dest_dir: str) -> Optional[Path]:
    """
    Download file from mediafire.com link.
    Scrapes page HTML for the direct download link.
    Returns local Path or None on failure.
    """
    try:
        Path(dest_dir).mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(
            timeout=120.0, follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        ) as client:
            page_resp = await client.get(url)
            if page_resp.status_code != 200:
                logger.warning(f"Mediafire page returned {page_resp.status_code}")
                return None

            html = page_resp.text
            # Find download button href
            match = re.search(
                r'id="downloadButton"[^>]*href="([^"]+)"',
                html,
            )
            if not match:
                # Fallback: aria-label pattern
                match = re.search(
                    r'aria-label="Download file"[^>]*href="([^"]+)"',
                    html,
                )
            if not match:
                logger.warning(f"Mediafire: cannot find download link in {url}")
                return None

            direct_url = match.group(1)
            # Extract filename from URL
            filename = direct_url.split("/")[-1]
            if not filename or filename == "":
                filename = "mediafire_download"
            from urllib.parse import unquote
            filename = unquote(filename)

            local_path = Path(dest_dir) / filename

            resp = await client.get(direct_url)
            if resp.status_code == 200:
                local_path.write_bytes(resp.content)
                logger.info(f"Mediafire downloaded: {local_path}")
                return local_path
            logger.warning(f"Mediafire download returned {resp.status_code}")
    except Exception as e:
        logger.error(f"Mediafire download failed for {url}: {e}")
    return None
