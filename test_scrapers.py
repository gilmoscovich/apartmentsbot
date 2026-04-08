from scrapers.yad2 import Yad2Scraper
from scrapers.madlan import MadlanScraper


def run_all_scrapers():
    yad2 = Yad2Scraper()
    madlan = MadlanScraper()

    yad2_listings = yad2.fetch_listings()
    madlan_listings = madlan.fetch_listings()

    print("=== Yad2 Listings ===")
    for l in yad2_listings:
        print(l)

    print("\n=== Madlan Listings ===")
    for l in madlan_listings:
        print(l)

    print("\n=== Combined ===")
    all_listings = yad2_listings + madlan_listings
    print(f"Total listings: {len(all_listings)}")


if __name__ == "__main__":
    run_all_scrapers()