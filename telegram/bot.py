"""
Telegram sender — sends apartment listings to a Telegram chat.
"""
from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

_SEND_MESSAGE = "https://api.telegram.org/bot{token}/sendMessage"
_SEND_PHOTO   = "https://api.telegram.org/bot{token}/sendPhoto"


def _format_caption(listing: dict) -> str:
    return (
        f"🏠 {listing.get('title', 'N/A')}\n"
        f"📍 {listing.get('location', 'N/A')}\n"
        f"💰 {listing.get('price', 'N/A')} ₪\n"
        f"🛏️ {listing.get('rooms', 'N/A')} rooms\n\n"
        f"🔗 {listing.get('link', '')}"
    )


class TelegramBot:
    """Sends apartment listings to a Telegram chat."""

    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id

    def send_listing(self, listing: dict) -> bool:
        """Send a single listing. Returns True on success."""
        text = _format_caption(listing)
        image_url = listing.get("image_url", "")

        if image_url:
            return self._send_photo(image_url, text)
        return self._send_text(text)

    def _send_text(self, text: str) -> bool:
        url = _SEND_MESSAGE.format(token=self.token)
        payload = {
            "chat_id": self.chat_id,
            "text": text,
        }
        resp = requests.post(url, json=payload, timeout=15)
        if not resp.ok:
            logger.error("sendMessage failed: %s", resp.text)
            return False
        return True

    def _send_photo(self, image_url: str, caption: str) -> bool:
        url = _SEND_PHOTO.format(token=self.token)
        payload = {
            "chat_id": self.chat_id,
            "photo": image_url,
            "caption": caption,
        }
        resp = requests.post(url, json=payload, timeout=15)
        if not resp.ok:
            logger.warning(
                "sendPhoto failed (%s), falling back to text", resp.status_code
            )
            return self._send_text(caption)
        return True


# Backward-compatible alias kept for existing imports
TelegramSender = TelegramBot
