"""
Entry point — wires all components together.
Full implementation in STEP 7; skeleton wires the imports.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time

import config
from db.database import Database
from filters.filter import ListingFilter
from dedup.deduplicator import Deduplicator
from scrapers.yad2 import Yad2Scraper
from scrapers.madlan import MadlanScraper
from telegram.bot import TelegramBot, send_message
from scheduler.scheduler import BotScheduler

# --- Daily summary state ---
_daily_stats = {"scraped": 0, "filtered": 0, "new": 0}
_last_summary_day: int | None = None  # calendar day (0–6) when last summary was sent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def _maybe_send_daily_summary() -> None:
    """Send a daily summary once per calendar day, then reset counters."""
    import datetime
    global _last_summary_day
    today = datetime.date.today().toordinal()
    if _last_summary_day == today:
        return
    _last_summary_day = today
    s = _daily_stats
    lines = [
        "📊 Daily Summary\n",
        f"Total scraped: {s['scraped']}",
        f"After filter: {s['filtered']}",
        f"New listings: {s['new']}",
    ]
    if s["new"] == 0:
        lines.append("No new apartments today 👍")
    send_message("\n".join(lines))
    s["scraped"] = s["filtered"] = s["new"] = 0


def run_pipeline() -> list[dict]:
    """
    Full scrape → filter → dedup → DB-check pipeline.

    Returns only listings that are new (not previously seen in the DB).
    Every new listing is inserted into the DB so subsequent runs skip it.
    """
    scraper1 = Yad2Scraper()

    listings = scraper1.fetch_listings()
    
    listing_filter = ListingFilter()
    dedup = Deduplicator()
    db = Database()

    # 1. Fetch from all sources
    listings = scraper1.fetch_listings()
    print(f"Fetched: {len(listings)} listings")
    _daily_stats["scraped"] += len(listings)

    # 2. Filter by business rules (location / price / rooms)
    print("\n=== ALL LOCATIONS ===")
    for l in listings:
        print(l.get("location"))
    listings = listing_filter.filter_listings(listings)
    print(f"After filter: {len(listings)} listings")
    _daily_stats["filtered"] += len(listings)

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

    _daily_stats["new"] += len(new_listings)

    # 5. Send new listings to Telegram
    print(f"NEW LISTINGS COUNT: {len(new_listings)}")
    if new_listings:
        bot = TelegramBot(token=config.TELEGRAM_BOT_TOKEN, chat_id=config.TELEGRAM_CHAT_ID)
        for listing in new_listings:
            ok = bot.send_listing(listing)
            status = "sent" if ok else "FAILED"
            print(f"[Telegram {status}] {listing['link']}")

    # 6. Report results
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
    while True:
        try:
            run_pipeline()
        except Exception as e:
            print(f"Error occurred: {e}")

        _maybe_send_daily_summary()
        print("Sleeping for 2 hours...")
        time.sleep(60 * 60 * 2)
