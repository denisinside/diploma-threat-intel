from __future__ import annotations

import requests


def send_signal_message(
    base_url: str,
    number: str,
    recipients: list[str],
    text: str,
    timeout: int,
) -> None:
    endpoint = f"{base_url.rstrip('/')}/v2/send"
    payload = {
        "number": number,
        "recipients": recipients,
        "message": text,
    }
    response = requests.post(endpoint, json=payload, timeout=timeout)
    response.raise_for_status()
