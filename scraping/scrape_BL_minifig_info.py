import argparse
from time import sleep, time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from lxml import etree
from requests.exceptions import ProxyError, ConnectTimeout, SSLError
from tqdm import tqdm

from constants import HEADERS, CATEGORY_CONFIG, Bcolors
from exceptions import BLQuotaExceeded
from scraping.helpers import (
    get_proxies,
    scrape_price_guide_page,
    convert_raw_price,
    scrape_initial_values,
)
from helpers_sqlite import (
    read_minifigs_with_avg_price,
    read_minifigs_with_appears_in,
    read_minifig_database,
)
from notion.helpers_notion import read_owned, read_wanted
from notion_client.errors import HTTPResponseError
from sqlite import insert_minifig


def get_appears_in(minifig_id: str, proxy: str = None) -> Optional[str]:
    print("Scraping Appears In...")
    proxies = {"https": proxy} if proxy else None
    page = requests.get(
        f"https://www.bricklink.com/catalogItemIn.asp?M={minifig_id}&in=S",
        headers=HEADERS,
        proxies=proxies,
        timeout=20,
    )
    soup = BeautifulSoup(page.text, "html.parser")
    html = etree.HTML(str(soup))

    xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[2]/tr/td/center/table/tr/td[3]/font/a[1]/text()'
    set_list = html.xpath(xpath)
    if appears_in_str := ",".join(set_list):
        return appears_in_str
    else:
        print(f"{Bcolors.WARNING}Warning: No Appears In found{Bcolors.ENDC}")
        return None


def beautifulsoup_parse(
    minifig_id: str, proxy: str = None, scrape_all: bool = False
) -> None:
    url = f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={minifig_id}#T=P"
    print(f"Scraping page for minifig {minifig_id}... [{url}]")

    page = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(page.text, "html.parser")
    html = etree.HTML(str(soup))

    # Only scrape name, category and sub-category if scrape_all is True
    # This data is by default extracted on the initial scrape
    name = category = sub_category = None
    if scrape_all:
        name, category, sub_category = scrape_initial_values(html)

    # Then scrape the missing info
    try:
        xpath = '//*[@id="yearReleasedSec"]/text()'
        release_year = int(html.xpath(xpath)[0])
    except IndexError:
        print(f"{Bcolors.WARNING}Info: No release year found{Bcolors.ENDC}")
        release_year = None

    avg_price_raw = scrape_price_guide_page("M", minifig_id, proxy=proxy)
    avg_price_raw, avg_price_pln, avg_price_eur = convert_raw_price(avg_price_raw)

    appears_in = get_appears_in(minifig_id, proxy=proxy)

    d = {
        "id": minifig_id,
        "name": name,
        "release_year": release_year,
        "image": None,
        "bricklink": None,
        "category": category,
        "sub_category": sub_category,
        "avg_price_raw": avg_price_raw,
        "avg_price_pln": avg_price_pln,
        "avg_price_eur": avg_price_eur,
        "appears_in": appears_in,
    }
    # Write to sqlite db
    insert_minifig(d)
    sleep(5)
    print("\n========================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category",
        choices=CATEGORY_CONFIG.keys(),
        help="category of minifigs to scrape",
        type=str,
    )
    parser.add_argument("--with-proxy", help="Execute with proxy", action="store_true")
    parser.add_argument("--scrape-all", help="Scrape all fields", action="store_true")
    parser.add_argument(
        "--get-appears-in",
        help="Focus on getting missing appears_in",
        action="store_true",
    )
    parser.add_argument(
        "--sort-oldest",
        help="Scrape minifigs from the oldest to the newest",
        action="store_true",
    )
    args = parser.parse_args()
    print(f"Scraping minifig info for category: {args.category}\n")

    if args.get_appears_in:
        # Get minifigs with appears_in to filer them out
        db_ids = read_minifigs_with_appears_in(args.category)["id"].values
    else:
        # Get minifigs with avg_price to filer them out
        db_ids = read_minifigs_with_avg_price(args.category)["id"].values

    # Order of ids to scrape 1- owned > 2- wanted > 3- most recent
    owned = wanted = []
    try:
        owned = list(set(read_owned("minifigs", args.category)) - set(db_ids))
        wanted = list(
            set(read_wanted("minifigs", args.category)) - set(owned) - set(db_ids)
        )  # In case owned and forgot to uncheck wanted
    except HTTPResponseError as e:
        print(e)
    rest = list(
        set(read_minifig_database(args.category)["id"].values)
        - set(owned)
        - set(wanted)
        - set(db_ids)
    )

    if args.sort_oldest:
        rest.sort()
    else:
        rest.sort(reverse=True)

    minifig_ids = owned + wanted + rest
    print(f"Number of minifigs to scrape: {len(minifig_ids)}\n")

    if args.with_proxy:
        proxies = get_proxies()
        proxy = next(proxies)
    else:
        proxy = None

    start = time()

    batch_size = 10
    try:
        for batch in tqdm(range(0, len(minifig_ids), batch_size)):
            print(f"Batch {int((batch/batch_size)+1)}")
            for minifig_id in minifig_ids[batch : batch + batch_size]:
                try:
                    beautifulsoup_parse(minifig_id, proxy, args.scrape_all)
                except (ProxyError, ConnectTimeout, SSLError) as e:
                    print(f"Error '{e}'\n")
                    if args.with_proxy:
                        proxy = next(proxies)
                        print(f"\ttrying another proxy... {proxy}")
                except BLQuotaExceeded:
                    end = time()
                    print(f"{Bcolors.FAIL}Error: BL Quota Exceeded{Bcolors.ENDC}")
                    print(f"Time elapsed: {round(end - start, 2)}s")
                    exit()
            print("Sleeping for 30 seconds...")
            sleep(30)
    except KeyboardInterrupt:
        print("Interrupted manually")
        pass
    end = time()
    print(f"Time elapsed: {round(end - start, 2)}s")
