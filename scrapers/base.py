"""
Shared data model and base scraper for all scrapers.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Listing:
    """A single rental apartment listing."""

    source: str              # e.g. "yad2" | "madlan"
    url: str
    price: int               # ILS/month
    city: str
    rooms: float
    description: str
    images: list[str]        # URLs; must have at least one
    external_id: Optional[str] = None   # site-native ID if available

    # computed on post-init
    unique_id: str = field(init=False)

    def __post_init__(self) -> None:
        if self.external_id:
            self.unique_id = f"{self.source}:{self.external_id}"
        else:
            # fallback: hash of (source, url)
            digest = hashlib.md5(f"{self.source}|{self.url}".encode()).hexdigest()
            self.unique_id = f"{self.source}:{digest}"

    @property
    def first_image(self) -> Optional[str]:
        return self.images[0] if self.images else None

    def has_image(self) -> bool:
        return bool(self.images)

    def to_dict(self) -> dict:
        """Return the unified dict format used across the pipeline."""
        return {
            "id": self.unique_id,
            "title": self.description,
            "price": self.price,
            "location": self.city,
            "rooms": self.rooms,
            "link": self.url,
            "image_url": self.first_image or "",
            "source": self.source,
        }

    def __repr__(self) -> str:
        return (
            f"<Listing {self.unique_id} | {self.city} | "
            f"{self.rooms}r | ₪{self.price}>"
        )


class BaseScraper:
    """Abstract base class all site scrapers must inherit from."""

    SOURCE: str = ""

    def fetch_listings(self) -> list[dict]:
        """Return listings in the unified dict format."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement fetch_listings()"
        )
