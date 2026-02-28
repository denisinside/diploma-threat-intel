"""
Universal browser-based file downloader using Playwright (headless Chromium).
Works with any file hosting service: navigates to the page, finds download
buttons via common selectors, clicks them, and captures the resulting file.

Many file hosts show a countdown (e.g. "Download in 10 seconds") before the
actual download starts. We detect countdown and wait for it to finish.

Requires: pip install playwright && playwright install chromium
"""
import asyncio
import re
from pathlib import Path
from typing import Optional
from loguru import logger


DOWNLOAD_SELECTORS = [
    "#downloadButton",
    "#d_l",
    "[data-download]",
    "[data-action='download']",
    "a[href*='download']",
    "a:has-text('Download')",
    "button:has-text('Download')",
    "a:has-text('download')",
    "button:has-text('download')",
    "a:has-text('DOWNLOAD')",
    "button:has-text('DOWNLOAD')",
    "[class*='download' i]",
    ".download-btn",
    ".download-button",
    ".btn-download",
    "a[class*='download' i]",
    "button[class*='download' i]",
    # Gofile / generic: file row or card
    "[class*='file' i] button",
    "tr[class*='file' i] a",
]

# Selectors for countdown elements (e.g. "10", "9", "8" or "seconds remaining")
COUNTDOWN_SELECTORS = [
    "[class*='countdown' i]",
    "[id*='countdown' i]",
    "[class*='timer' i]",
    "[id*='timer' i]",
    "span:has-text('second')",
    "div:has-text('second')",
    "[class*='download-wait' i]",
]

PAGE_TIMEOUT_MS = 30_000
CLICK_WAIT_S = 10
MAX_ROUNDS = 4
COUNTDOWN_WAIT_S = 25  # Max seconds to wait for countdown to finish
COUNTDOWN_POLL_INTERVAL_S = 1

# Page states we skip: archived content, import prompts, etc. (no real download available)
SKIP_PAGE_PHRASES = [
    "archived content",
    "import to your account",
    "import to account",
    "content has been archived",
]


async def _should_skip_page(page) -> bool:
    """Check if page shows archived/import state — skip, no download available."""
    try:
        body = await page.locator("body").text_content()
        if not body:
            return False
        lower = body.lower()
        for phrase in SKIP_PAGE_PHRASES:
            if phrase in lower:
                return True
    except Exception:
        pass
    return False


async def _wait_for_countdown(page) -> bool:
    """
    Detect countdown on page and wait until it finishes.
    Returns True if countdown was detected and we waited, False otherwise.
    """
    for selector in COUNTDOWN_SELECTORS:
        try:
            loc = page.locator(selector).first
            if await loc.is_visible(timeout=500):
                logger.debug(f"Countdown detected (selector: {selector}), waiting up to {COUNTDOWN_WAIT_S}s")
                for _ in range(COUNTDOWN_WAIT_S):
                    await asyncio.sleep(COUNTDOWN_POLL_INTERVAL_S)
                    try:
                        text = await loc.text_content()
                        if text:
                            # Check if it's a number (countdown value)
                            num = re.search(r"\b(\d+)\b", text)
                            if num and int(num.group(1)) <= 1:
                                await asyncio.sleep(2)  # Let download trigger
                                break
                        if not await loc.is_visible(timeout=300):
                            break
                    except Exception:
                        break
                return True
        except Exception:
            continue
    return False


async def download_via_browser(url: str, dest_dir: str) -> Optional[Path]:
    """
    Download a file from any file hosting URL using headless Chromium.
    Tries common download-button selectors, captures the browser download event.
    Returns local file Path on success, None on failure.
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        logger.error("playwright not installed — run: pip install playwright && playwright install chromium")
        return None

    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    dest_abs = str(dest.resolve())
    logger.info(f"Browser download target: {dest_abs}")

    try:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context(accept_downloads=True)
            page = await context.new_page()

            captured_download = None
            dl_event = asyncio.Event()

            def _on_download(download):
                nonlocal captured_download
                if captured_download is None:
                    captured_download = download
                    dl_event.set()

            page.on("download", _on_download)

            logger.debug(f"Browser navigating to {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            try:
                await page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception:
                pass

            if await _should_skip_page(page):
                logger.info(f"Skipping {url}: archived/import-only content (no download available)")
                await browser.close()
                return None

            skip_requested = False
            for _round in range(MAX_ROUNDS):
                if captured_download or skip_requested:
                    break

                for selector in DOWNLOAD_SELECTORS:
                    if captured_download or skip_requested:
                        break
                    try:
                        locator = page.locator(selector).first
                        if not await locator.is_visible(timeout=1_500):
                            continue
                        logger.debug(f"Browser clicking selector: {selector}")
                        await locator.click()
                        await asyncio.sleep(2)  # Let modal/popup appear (e.g. "Archived Content")
                        if await _should_skip_page(page):
                            logger.info(f"Skipping {url}: archived/import-only content (no download available)")
                            skip_requested = True
                            break
                        try:
                            await asyncio.wait_for(dl_event.wait(), timeout=CLICK_WAIT_S - 2)
                        except asyncio.TimeoutError:
                            pass
                        if await _should_skip_page(page):
                            logger.info(f"Skipping {url}: archived/import-only content (no download available)")
                            skip_requested = True
                            break
                    except Exception:
                        continue

                if captured_download or skip_requested:
                    break

                # No download yet: maybe countdown started. Wait for it.
                countdown_found = await _wait_for_countdown(page)
                if not countdown_found:
                    # No countdown detected; wait anyway (some sites use JS delay)
                    await asyncio.sleep(5)
                try:
                    await page.wait_for_load_state("networkidle", timeout=10_000)
                except Exception:
                    pass

            local_path = None
            if captured_download:
                filename = captured_download.suggested_filename or "downloaded_file"
                local_path = dest / filename
                await captured_download.save_as(str(local_path))
                if local_path.exists() and local_path.stat().st_size > 0:
                    logger.info(f"Browser downloaded: {local_path} ({local_path.stat().st_size} bytes)")
                else:
                    logger.warning(f"Browser: file empty or missing after save for {url}")
                    local_path = None
            elif not skip_requested:
                logger.warning(f"Browser: no download button found at {url}")

            await browser.close()
            return local_path

    except Exception as e:
        logger.error(f"Browser download failed for {url}: {e}")
    return None
