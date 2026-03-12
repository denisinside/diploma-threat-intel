from __future__ import annotations

import requests


def send_webhook_message(url: str, text: str, timeout: int) -> None:
    response = requests.post(url, json={"text": text}, timeout=timeout)
    response.raise_for_status()
