"""
Extract cloud storage URLs from message text.
Supported: mega.nz, gofile.io, mediafire.com, upload.ee.
Easy to extend: just add a new entry to CLOUD_PATTERNS.
"""
import re
from typing import List, Tuple

CLOUD_PATTERNS = {
    "mega": re.compile(r"https?://mega\.nz/(?:file|folder)/[A-Za-z0-9_#!-]+"),
    "gofile": re.compile(r"https?://gofile\.io/d/[A-Za-z0-9]+"),
    "mediafire": re.compile(r"https?://(?:www\.)?mediafire\.com/file/[A-Za-z0-9]+(?:/[^\s)\"]*)?"),
    "upload_ee": re.compile(r"https?://(?:www\.)?upload\.ee/files/[0-9]+/[^\s)\"]+"),
    "anonfiles": re.compile(r"https?://(?:www\.)?anonfiles\.com/[A-Za-z0-9]+(?:/[^\s)\"]*)?"),
    "pixeldrain": re.compile(r"https?://pixeldrain\.com/u/[A-Za-z0-9]+"),
    "krakenfiles": re.compile(r"https?://krakenfiles\.com/view/[A-Za-z0-9]+/file\.html"),
    "sendspace": re.compile(r"https?://(?:www\.)?sendspace\.com/file/[A-Za-z0-9]+"),
}


def extract_cloud_links(text: str) -> List[Tuple[str, str]]:
    """
    Extract cloud links from text.
    Returns list of (service_name, url) tuples.
    """
    if not text:
        return []
    results = []
    for service, pattern in CLOUD_PATTERNS.items():
        for match in pattern.finditer(text):
            results.append((service, match.group(0)))
    return results
