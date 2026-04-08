"""
APScheduler wrapper.
Skeleton: real implementation in STEP 8.
"""
from __future__ import annotations

import logging
from typing import Callable, Awaitable

logger = logging.getLogger(__name__)


class BotScheduler:
    """Schedules periodic scrape-and-send runs."""

    def __init__(self, interval_hours: int) -> None:
        self.interval_hours = interval_hours
        # TODO: implement in STEP 8

    def start(self, job: Callable[[], Awaitable[None]]) -> None:
        """Register *job* and start the scheduler."""
        # TODO: implement in STEP 8
        logger.info("Scheduler stub — interval: %dh", self.interval_hours)
