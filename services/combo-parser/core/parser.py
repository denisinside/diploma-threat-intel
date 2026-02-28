"""
Parse combo/leak files and extract records.
Supports formats:
  - email:password
  - user:password
  - url|login|password  (pipe-separated, stealer logs)
  - url:login:password  (colon-separated, ULP style - url can be https://, android://...@host/, etc.)
"""
import re
from typing import Iterator, Optional
from loguru import logger

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Simple combo: login:password
COMBO_LINE_REGEX = re.compile(r"^([^\s:]+):(.+)$")


def _looks_like_url(s: str) -> bool:
    """Check if string looks like a URL: protocol, domain, android package, or path."""
    if not s or len(s) < 4:
        return False
    if "://" in s:
        return True
    if "@" in s and "." in s:
        return True
    # Domain-like: example.com, sub.example.com, accounts.spotify.com/path
    if "." in s and "/" in s:
        return True
    # Android package: com.xiaomi.account, com.app.name
    if re.match(r"^[a-z][a-z0-9_]*(\.[a-z0-9_]+)+", s, re.I):
        return True
    # Domain with TLD: metamask.io, example.com (has dot, looks like host)
    if "." in s and re.search(r"\.[a-z]{2,}(/|$)", s, re.I):
        return True
    return False


def _extract_domain(email: str) -> Optional[str]:
    if "@" in email:
        return email.split("@", 1)[1].lower()
    return None


def parse_line(line: str) -> Optional[dict]:
    """
    Parse a single combo line. Returns dict with fields or None.
    """
    line = line.strip()
    if not line or len(line) < 5:
        return None

    # Pipe format: url|login|password
    if "|" in line:
        parts = line.split("|", 2)
        if len(parts) == 3 and _looks_like_url(parts[0]):
            url_val, login, pwd = parts[0], parts[1], parts[2]
            record = {"password": pwd, "url": url_val, "leaktype": "stealer"}
            if EMAIL_REGEX.match(login):
                record["email"] = login
                record["domain"] = _extract_domain(login)
            else:
                record["username"] = login
            return record

    # Colon format: url:login:password (ULP, stealer logs)
    # Use rsplit so URL/password can contain colons; login is the middle part (no colons)
    if line.count(":") >= 2:
        parts = line.rsplit(":", 2)
        if len(parts) == 3:
            url_val, login, pwd = parts[0].strip(), parts[1].strip(), parts[2].strip()
            if url_val and login and pwd and _looks_like_url(url_val):
                record = {"password": pwd, "url": url_val, "leaktype": "stealer"}
                if EMAIL_REGEX.match(login):
                    record["email"] = login
                    record["domain"] = _extract_domain(login)
                else:
                    record["username"] = login
                return record

    # Simple combo: email:password or user:password
    m = COMBO_LINE_REGEX.match(line)
    if m:
        login, pwd = m.group(1), m.group(2)
        record = {"password": pwd, "leaktype": "combo"}
        if EMAIL_REGEX.match(login):
            record["email"] = login
            record["domain"] = _extract_domain(login)
        else:
            record["username"] = login
        return record

    return None


def _record_digest(record: dict) -> str:
    """Generate unique digest for record deduplication (email|user|password|url)."""
    import hashlib
    parts = [
        record.get("email") or record.get("username") or "",
        record.get("password") or "",
        record.get("url") or "",
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8", errors="replace")).hexdigest()


def parse_lines(lines: list, source_id: str) -> list:
    """
    Parse a list of lines. Returns list of ES-ready records.
    Used for parallel parsing (each worker gets a chunk of lines).
    """
    records = []
    for line in lines:
        record = parse_line(line)
        if record:
            record["leak_source_ids"] = [source_id]
            records.append(record)
    return records


def parse_text(text: str, source_id: str) -> Iterator[dict]:
    """
    Parse text content (combo file) line by line.
    Yields ES-ready documents with leak_source_ids: [source_id].
    """
    for line in text.splitlines():
        record = parse_line(line)
        if record:
            record["leak_source_ids"] = [source_id]
            yield record
