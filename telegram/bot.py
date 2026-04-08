"""
Telegram sender.
Skeleton: real implementation in STEP 6.
"""
from __future__ import annotations

import logging

from scrapers.base import Listing

logger = logging.getLogger(__name__)


class TelegramSender:
    """Sends apartment listings to a Telegram chat."""

    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        # TODO: implement in STEP 6

    async def send_listing(self, listing: Listing) -> bool:
        """Send a single listing. Returns True on success."""
        # TODO: implement in STEP 6
        logger.info("Would send listing: %s", listing)
        return False
