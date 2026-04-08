"""
Yad2 scraper — uses Playwright (JS-heavy site).
Searches specific target cities only.
"""
from __future__ import annotations

import hashlib
import logging
import re

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from scrapers.base import BaseScraper, Listing

logger = logging.getLogger(__name__)

URLS = [
    "https://www.yad2.co.il/realestate/rent/coastal-north?area=16&city=1020",
    "https://www.yad2.co.il/realestate/rent/coastal-north?area=15&city=7800",
    "https://www.yad2.co.il/realestate/rent/coastal-north?area=15&city=6500",
    "https://www.yad2.co.il/realestate/rent/coastal-north?area=15&city=9800",
]


class Yad2Scraper(BaseScraper):
    """Scraper for yad2.co.il using Playwright."""

    SOURCE = "yad2"

    def fetch_listings(self) -> list[dict]:
        logger.info("[yad2] Fetching listings from %d URLs", len(URLS))
        try:
            listings = self._scrape_all_urls()
        except Exception as exc:
            logger.error("[yad2] Scraping failed: %s", exc, exc_info=True)
            listings = []
        logger.info("[yad2] Done — %d listings total", len(listings))
        return [l.to_dict() for l in listings]

    # ------------------------------------------------------------------
    # URL-loop orchestration
    # ------------------------------------------------------------------

    def _scrape_all_urls(self) -> list[Listing]:
        all_listings: list[Listing] = []
        seen_ids: set[str] = set()

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                locale="he-IL",
                viewport={"width": 1280, "height": 900},
            )

            page = context.new_page()
            try:
                for url in URLS:
                    logger.info("[yad2] Scraping URL: %s", url)
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)

                    try:
                        page.wait_for_selector(
                            "a[href*='/realestate/item']",
                            timeout=15000,
                        )
                    except PlaywrightTimeoutError:
                        logger.warning("[yad2] Listing selector not found within timeout, continuing anyway")

                    page.wait_for_timeout(2000)
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(2000)

                    raw_items = self._extract_items(page)
                    logger.info("[yad2] Found %d listings from URL", len(raw_items))

                    for raw in raw_items:
                        listing = self._parse_listing(raw)
                        if listing and listing.external_id not in seen_ids:
                            seen_ids.add(listing.external_id)
                            all_listings.append(listing)
            finally:
                page.close()
                context.close()
                browser.close()

        print(f"TOTAL RAW LISTINGS: {len(all_listings)}")
        return all_listings

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_items(self, page) -> list[dict]:
        """Find all listing links via href pattern, then pull data from their parent card."""
        link_elements = page.query_selector_all("a[href*='/realestate/item']")
        logger.info("[yad2] Found %d listing link elements", len(link_elements))

        results = []
        for el in link_elements:
            try:
                raw = self._extract_from_link(el)
                if raw:
                    results.append(raw)
            except Exception as exc:
                logger.debug("[yad2] Error extracting element: %s", exc)

        # Debug: show first 2 raw items
        for i, item in enumerate(results[:2]):
            logger.info("[yad2] Sample item %d: %s", i, item)

        return results

    def _extract_from_link(self, link_el) -> dict | None:
        href = link_el.get_attribute("href") or ""
        if not href:
            return None

        # Walk up to find the card container (up to 5 levels)
        card = link_el
        for _ in range(5):
            parent = card.query_selector("xpath=..")
            if parent is None:
                break
            card = parent
            # Stop if this parent looks like a feed card (has price info)
            text = card.inner_text() or ""
            if "₪" in text or "חדר" in text or "חדרים" in text:
                break

        full_text = ""
        try:
            full_text = card.inner_text() or ""
        except Exception:
            pass

        # Image from anywhere in the card
        img = ""
        try:
            img_el = card.query_selector("img[src]")
            if img_el:
                img = img_el.get_attribute("src") or ""
        except Exception:
            pass

        # Title: text inside the link itself
        title = ""
        try:
            title = link_el.inner_text().strip()
        except Exception:
            pass

        return {
            "href": href,
            "full_text": full_text,
            "title": title,
            "img": img,
        }

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_listing(self, raw: dict) -> Listing | None:
        try:
            href = raw.get("href", "")
            link = self._make_absolute(href)
            if not link:
                return None

            full_text = raw.get("full_text", "")

            # Clean title: strip price-drop noise, deduplicate lines, keep first 2
            raw_title = raw.get("title", "").strip()
            seen: set[str] = set()
            clean_lines = []
            for line in raw_title.splitlines():
                line = line.strip()
                if not line or line in seen:
                    continue
                # Remove "ירד ב-XXX ₪" (price-drop indicator)
                if re.search(r"ירד\s+ב", line):
                    continue
                # Remove price patterns like "₪ 8,500" or "8,500 ₪"
                line = re.sub(r"₪\s*[\d,]+|[\d,]+\s*₪", "", line).strip()
                if not line:
                    continue
                seen.add(line)
                clean_lines.append(line)
            title = " ".join(clean_lines[:2])

            price = self._extract_price(full_text)
            rooms = self._extract_rooms(full_text)
            city = self.extract_city_from_title(raw_title)
            if city in ("", "לא צוין"):
                city = "unknown"
            print(f"City from title: {city}")

            if not title:
                title = city if city != "unknown" else "דירה להשכרה"

            image = raw.get("img", "") or ""
            external_id = self._id_from_url(link)

            return Listing(
                source=self.SOURCE,
                url=link,
                price=price,
                city=city,
                rooms=rooms,
                description=title,
                images=[image] if image else [],
                external_id=external_id,
            )
        except Exception as exc:
            logger.debug("[yad2] Skipping item, parse error: %s | raw=%s", exc, raw)
            return None

    @staticmethod
    def _extract_price(text: str) -> int:
        # Collect ALL numbers adjacent to ₪, then return the largest.
        # This ignores "ירד ב-250 ₪" discount amounts and picks the actual rent price.
        candidates = re.findall(r"([\d,]+)\s*₪|₪\s*([\d,]+)", text)
        values = [int((a or b).replace(",", "")) for a, b in candidates]
        if values:
            return max(values)
        # fallback: any 4-5 digit number that looks like a rent
        m = re.search(r"\b([3-9]\d{3}|[1-2]\d{4})\b", text)
        if m:
            return int(m.group().replace(",", ""))
        return 0

    @staticmethod
    def _extract_rooms(text: str) -> float:
        # Hebrew: "3 חדרים" or "3.5 חד'"
        m = re.search(r"(\d+(?:[.,]\d)?)\s*(?:חדרים|חדר|חד)", text)
        if m:
            return float(m.group(1).replace(",", "."))
        return 0.0

    @staticmethod
    def extract_city_from_title(title: str) -> str:
        if not title:
            return ""

        # remove "מחוז ..." suffix
        if "מחוז" in title:
            title = title.split("מחוז")[0]

        parts = [p.strip() for p in title.split(",")]

        candidates = []
        for p in parts:
            if "₪" in p:
                continue
            if any(char.isdigit() for char in p):
                continue
            if len(p) < 2:
                continue
            candidates.append(p)

        print(f"Candidates: {candidates}")

        city = candidates[-1] if candidates else ""

        print(f"Final city: {city}")
        return city

    @staticmethod
    def _extract_location(text: str) -> str:
        # Skip lines that look like agent/company names
        agent_keywords = {"נכסים", "תיווך", "סוכנות", 'בע"מ', "מתווך", "קבוצת", "משרד"}
        for line in text.splitlines():
            line = line.strip()
            if not line or not re.search(r"[\u0590-\u05FF]", line):
                continue
            if re.search(r"\d", line):
                continue
            if len(line) < 3 or len(line) > 40:
                continue
            if any(kw in line for kw in agent_keywords):
                continue
            return line
        return ""

    @staticmethod
    def _make_absolute(href: str) -> str:
        if not href:
            return ""
        if href.startswith("http"):
            return href
        return "https://www.yad2.co.il" + href

    @staticmethod
    def _id_from_url(url: str) -> str:
        # URL pattern: /item/{region}/{id}  →  take the last path segment
        m = re.search(r"/item/(?:[^/?#]+/)*([^/?#]+)", url)
        if m:
            return m.group(1)
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def _generate_id(self, data: dict) -> str:
        key = f"{data.get('title', '')}|{data.get('price', '')}|{data.get('location', '')}"
        return hashlib.md5(key.encode()).hexdigest()


# ------------------------------------------------------------------
# Quick smoke-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    scraper = Yad2Scraper()
    listings = scraper.fetch_listings()
    print(json.dumps(listings, indent=2, ensure_ascii=False))
