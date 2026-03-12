from __future__ import annotations

import requests


def send_slack_message(webhook_url: str, text: str, timeout: int) -> None:
    response = requests.post(webhook_url, json={"text": text}, timeout=timeout)
    response.raise_for_status()
