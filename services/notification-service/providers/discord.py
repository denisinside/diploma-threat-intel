from __future__ import annotations

import requests


def send_discord_message(webhook_url: str, text: str, timeout: int) -> None:
    response = requests.post(webhook_url, json={"content": text}, timeout=timeout)
    response.raise_for_status()
