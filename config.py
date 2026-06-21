"""
Central configuration — loaded once at startup.
All secrets come from environment variables (or .env in dev).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "data" / "apartments.db"

# ── Telegram ─────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.environ.get("TELEGRAM_CHAT_ID", "")

if not TELEGRAM_BOT_TOKEN:
    raise EnvironmentError("TELEGRAM_BOT_TOKEN is not set. Add it as an environment variable or GitHub Actions secret.")
if not TELEGRAM_CHAT_ID:
    raise EnvironmentError("TELEGRAM_CHAT_ID is not set. Add it as an environment variable or GitHub Actions secret.")

# ── Filters ──────────────────────────────────────────────────────────────────
ALLOWED_CITIES: list[str] = [
    "פרדס חנה",   # Pardes Hanna
    "בנימינה",    # Binyamina
    "חדרה",       # Hadera
    "אור עקיבא",  # Or Akiva
    "הרצליה",     # Herzliya
    "אולגה",      # Olga
    "אור ים",     # Or Yam
]
MAX_PRICE: int = 4_800          # ILS
REQUIRED_ROOMS: float = 3.0     # exact match (3 rooms)

# ── Apify / Facebook ─────────────────────────────────────────────────────────
APIFY_API_TOKEN: str = os.environ.get("APIFY_API_TOKEN", "")
FACEBOOK_GROUP_URLS: list[str] = [
    u.strip() for u in os.environ.get("FACEBOOK_GROUP_URLS", "").split(",") if u.strip()
]

# ── Scheduler ─────────────────────────────────────────────────────────────────
SCRAPE_INTERVAL_HOURS: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "48"))

# ── Scraper behaviour ────────────────────────────────────────────────────────
REQUEST_TIMEOUT: int = 30       # seconds
PLAYWRIGHT_TIMEOUT: int = 60_000  # ms
MAX_RETRIES: int = 3
