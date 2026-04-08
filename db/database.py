import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path="data.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id          TEXT PRIMARY KEY,
                title       TEXT,
                price       INTEGER,
                location    TEXT,
                rooms       REAL,
                link        TEXT,
                image_url   TEXT,
                source      TEXT,
                first_seen  TIMESTAMP,
                last_seen   TIMESTAMP,
                sent        BOOLEAN DEFAULT 0
            )
        """)
        self.conn.commit()

    def insert_listing(self, listing: dict):
        now = datetime.utcnow()

        if self.listing_exists(listing["id"]):
            logger.debug("Skipping duplicate listing: %s", listing["id"])
            self.conn.execute(
                "UPDATE listings SET last_seen = ? WHERE id = ?",
                (now, listing["id"]),
            )
        else:
            logger.info("Inserting new listing: %s (%s)", listing["id"], listing.get("title", ""))
            self.conn.execute(
                """
                INSERT INTO listings
                    (id, title, price, location, rooms, link, image_url, source, first_seen, last_seen, sent)
                VALUES
                    (:id, :title, :price, :location, :rooms, :link, :image_url, :source, :first_seen, :last_seen, 0)
                """,
                {**listing, "first_seen": now, "last_seen": now},
            )

        self.conn.commit()

    def listing_exists(self, listing_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM listings WHERE id = ?", (listing_id,)
        ).fetchone()
        return row is not None

    def mark_as_sent(self, listing_id: str):
        logger.info("Marking listing as sent: %s", listing_id)
        self.conn.execute(
            "UPDATE listings SET sent = 1 WHERE id = ?", (listing_id,)
        )
        self.conn.commit()

    def get_unsent_listings(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM listings WHERE sent = 0"
        ).fetchall()
        return [dict(row) for row in rows]

    def close(self):
        self.conn.close()
