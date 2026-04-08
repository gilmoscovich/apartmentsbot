# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (requires Python 3.11+)
pip install -r requirements.txt
playwright install chromium

# Run the main pipeline loop (scrape → filter → dedup → send)
python main.py

# Test scrapers in isolation
python test_scrapers.py

# Smoke-test individual modules
python scrapers/yad2.py
python filters/filter.py
python dedup/deduplicator.py
```

## Architecture

The bot is a periodic scrape-filter-notify pipeline with no web server. `main.py` is the entry point; it runs `run_pipeline()` in an infinite loop (2-hour sleep between iterations).

**Pipeline stages (in order):**

1. **Scrapers** (`scrapers/`) — each scraper extends `BaseScraper` and implements `fetch_listings() → list[dict]`. The unified dict format (id, title, price, location, rooms, link, image_url, source) is defined in `BaseScraper.Listing.to_dict()`.
   - `Yad2Scraper`: uses Playwright (sync API) to scrape JS-rendered pages. Iterates over `URLS` list (hardcoded city-specific Yad2 URLs), extracts listings by finding `a[href*='/realestate/item']` anchors and walking up the DOM to find card containers.
   - `MadlanScraper`: currently returns mock data only — real scraping not yet implemented.

2. **Filter** (`filters/filter.py`) — `ListingFilter` checks city (exact match against `allowed_locations`), price (≤ `max_price`), and rooms (± 0.1 tolerance).

3. **Dedup** (`dedup/deduplicator.py`) — in-memory fuzzy deduplication across sources. Two listings are duplicates if location is a substring match, price differs ≤ 200 ILS, and rooms differ < 0.2.

4. **Database** (`db/database.py`) — SQLite (`data.db` by default) for persistent deduplication. `listing_exists()` and `insert_listing()` are the key methods. Also tracks `sent` flag via `mark_as_sent()`.

5. **Telegram** (`telegram/bot.py`) — `TelegramBot` sends listings via Bot API. Uses `sendPhoto` when an image URL is available, falls back to `sendMessage`.

**Config** (`config.py`): all settings loaded from `.env`. Target cities, price cap, and room count are hardcoded constants there (and duplicated in `ListingFilter.__init__` — keep in sync).

**Note:** `scheduler/scheduler.py` and the async `run_once()` path in `main.py` are stubs (not yet wired). The active code path is the synchronous `run_pipeline()` / `__main__` loop.

## Environment

Copy `.env.example` to `.env` and fill in:
- `TELEGRAM_BOT_TOKEN` — from BotFather
- `TELEGRAM_CHAT_ID` — the target chat/channel ID
- `SCRAPE_INTERVAL_HOURS` — optional, defaults to 48

## Deployment

`Procfile` defines a single `worker` dyno: `python3 main.py`. Intended for Railway or Render (no HTTP port needed).
