"""
Entry point — wires all components together.
Full implementation in STEP 7; skeleton wires the imports.
"""
from __future__ import annotations

import asyncio
import logging
import sys

import config
from db.database import Database
from filters.filter import ListingFilter
from dedup.deduplicator import Deduplicator
from scrapers.yad2 import Yad2Scraper
from scrapers.madlan import MadlanScraper
from telegram.bot import TelegramSender
from scheduler.scheduler import BotScheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_pipeline() -> list[dict]:
    """
    Full scrape → filter → dedup → DB-check pipeline.

    Returns only listings that are new (not previously seen in the DB).
    Every new listing is inserted into the DB so subsequent runs skip it.
    """
    scraper1 = Yad2Scraper()
    scraper2 = MadlanScraper()
    listing_filter = ListingFilter()
    dedup = Deduplicator()
    db = Database()

    # 1. Fetch from all sources
    listings = scraper1.fetch_listings() + scraper2.fetch_listings()
    print(f"Fetched: {len(listings)} listings")

    # 2. Filter by business rules (location / price / rooms)
    listings = listing_filter.filter_listings(listings)
    print(f"After filter: {len(listings)} listings")

    # 3. In-memory deduplication (cross-source fuzzy duplicates)
    listings = dedup.deduplicate(listings)
    print(f"After dedup: {len(listings)} listings")

    # 4. Persistent deduplication via DB
    #    - already seen → skip
    #    - new → insert and keep
    new_listings = []
    for listing in listings:
        if db.listing_exists(listing["id"]):
            print(f"Already seen: {listing['link']}")
            continue

        db.insert_listing(listing)
        new_listings.append(listing)

    # 5. Report results
    print("\n=== NEW LISTINGS ===")
    for listing in new_listings:
        print(listing)

    print(f"\nNew: {len(new_listings)}")

    db.close()
    return new_listings


# ---------------------------------------------------------------------------
# Async skeleton — full wiring in STEP 7
# ---------------------------------------------------------------------------

async def run_once() -> None:
    """Single scrape → filter → dedup → send cycle."""
    logger.info("=== Starting apartment scan ===")

    # TODO: full implementation in STEP 7
    scrapers = [Yad2Scraper(), MadlanScraper()]
    all_listings = []
    for scraper in scrapers:
        results = await scraper.scrape()
        all_listings.extend(results)

    logger.info("Total raw listings: %d", len(all_listings))
    # filter, dedup, send — wired in STEP 7
    logger.info("=== Scan complete ===")


def main() -> None:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = Database(config.DB_PATH)
    db.setup()

    scheduler = BotScheduler(config.SCRAPE_INTERVAL_HOURS)
    scheduler.start(run_once)

    asyncio.run(run_once())   # also run immediately on startup


if __name__ == "__main__":
    run_pipeline()
