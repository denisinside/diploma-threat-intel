from __future__ import annotations

import logging
import requests

logger = logging.getLogger(__name__)


def send_telegram_message(bot_token: str, chat_id: str, text: str, timeout: int) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": text},
        timeout=timeout,
    )
    if not response.ok:
        try:
            body = response.json()
            desc = body.get("description", response.text)
        except Exception:
            desc = response.text or response.reason_phrase
        logger.error(
            "Telegram API error: status=%s, description=%s",
            response.status_code,
            desc,
            extra={"response_text": response.text[:500]},
        )
        response.raise_for_status()
