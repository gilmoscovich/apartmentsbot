from scrapers.yad2 import Yad2Scraper
from scrapers.madlan import MadlanScraper
from scrapers.facebook import FacebookScraper


def run_all_scrapers():
    yad2 = Yad2Scraper()
    madlan = MadlanScraper()
    facebook = FacebookScraper(results_limit=10, newer_than="3 days")

    yad2_listings = yad2.fetch_listings()
    madlan_listings = madlan.fetch_listings()
    facebook_listings = facebook.fetch_listings()

    print("=== Yad2 Listings ===")
    for l in yad2_listings:
        print(l)

    print("\n=== Madlan Listings ===")
    for l in madlan_listings:
        print(l)

    print("\n=== Facebook Listings ===")
    for l in facebook_listings:
        print(l)

    print("\n=== Combined ===")
    all_listings = yad2_listings + madlan_listings + facebook_listings
    print(f"Total listings: {len(all_listings)}")


if __name__ == "__main__":
    run_all_scrapers()