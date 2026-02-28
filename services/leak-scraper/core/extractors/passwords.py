"""
Extract archive passwords from message text.
Common patterns: PASS: xxx, PASSWORD: xxx, pass: xxx, пароль: xxx
"""
import re
from typing import Optional


PASSWORD_PATTERNS = [
    re.compile(r"(?:PASS(?:WORD)?|pass(?:word)?|Pass(?:word)?)\s*[:\-=]\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:пароль|Пароль|ПАРОЛЬ)\s*[:\-=]\s*(.+)", re.IGNORECASE),
    re.compile(r"(?:pwd|PWD|Pwd)\s*[:\-=]\s*(.+)", re.IGNORECASE),
]


def extract_password(text: str) -> Optional[str]:
    """Extract archive password from message text. Returns first match or None."""
    if not text:
        return None
    for pattern in PASSWORD_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1).strip()
    return None
