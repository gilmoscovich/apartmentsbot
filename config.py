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
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID")

# ── Filters ──────────────────────────────────────────────────────────────────
ALLOWED_CITIES: list[str] = [
    "פרדס חנה",   # Pardes Hanna
    "בנימינה",    # Binyamina
    "חדרה",       # Hadera
    "אור עקיבא",  # Or Akiva
    "הרצליה"      # רק לבדיקה
]
MAX_PRICE: int = 4_800          # ILS
REQUIRED_ROOMS: float = 3.0     # exact match (3 rooms)

# ── Scheduler ─────────────────────────────────────────────────────────────────
SCRAPE_INTERVAL_HOURS: int = int(os.getenv("SCRAPE_INTERVAL_HOURS", "48"))

# ── Scraper behaviour ────────────────────────────────────────────────────────
REQUEST_TIMEOUT: int = 30       # seconds
PLAYWRIGHT_TIMEOUT: int = 60_000  # ms
MAX_RETRIES: int = 3
