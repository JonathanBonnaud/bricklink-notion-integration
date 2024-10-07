import argparse
from time import sleep, time
from typing import Optional, Tuple

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
    read_minifigs_with_filter,
    read_minifig_database,
    read_minifigs_where_failed,
    read_minifigs_to_scrape,
)
from notion.helpers_notion import read_owned, read_wanted
from notion_client.errors import HTTPResponseError
from sqlite import upsert_minifig, insert_minifig_price


def get_appears_in(minifig_id: str, proxy: str = None) -> Tuple[Optional[str], bool]:
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
        return appears_in_str, False
    else:
        print(f"{Bcolors.WARNING}Warning: No Appears In found{Bcolors.ENDC}")
        return None, True


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
        failed_release_year = False
        release_year = int(html.xpath(xpath)[0])
    except IndexError:
        print(f"{Bcolors.WARNING}Info: No release year found{Bcolors.ENDC}")
        failed_release_year = True
        release_year = None

    avg_price_raw, failed_avg_price_raw = scrape_price_guide_page(
        "M", minifig_id, proxy=proxy
    )
    avg_price_raw, avg_price_pln, avg_price_eur = convert_raw_price(avg_price_raw)

    appears_in, failed_appears_in = get_appears_in(minifig_id, proxy=proxy)

    failed = any([failed_release_year, failed_appears_in, failed_avg_price_raw])
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
        "failed": failed,
    }
    # Write to sqlite db
    upsert_minifig(d)
    try:
        assert avg_price_raw is not None
        insert_minifig_price(
            {
                "id": minifig_id,
                "avg_price_raw": avg_price_raw,
                "avg_price_pln": avg_price_pln,
                "avg_price_eur": avg_price_eur,
            }
        )
    except AssertionError:
        pass
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
        "--sort-oldest",
        help="Scrape minifigs from the oldest to the newest",
        action="store_true",
    )
    parser.add_argument(
        "-id",
        "--bl_id",
        type=str,
        help="Scrape one minifig",
    )
    args = parser.parse_args()
    print(f"Scraping minifig info for category: {args.category}\n")

    if args.bl_id:
        print(f"BL ID passed: {args.bl_id}\n")
        beautifulsoup_parse(args.bl_id)
        exit()

    # Get minifigs to filer them out (these already have values, so we don't need to scrape them)
    db_ids_appears_in = read_minifigs_with_filter(args.category, "appears_in")[
        "id"
    ].values
    db_ids_avg_price = read_minifigs_with_filter(args.category, "avg_price_pln")[
        "id"
    ].values
    db_ids_release_year = read_minifigs_with_filter(args.category, "release_year")[
        "id"
    ].values
    # Get minifigs with backoff delay that we don't want to scrape again
    db_ids_failed = read_minifigs_where_failed(args.category)["id"].values

    # We don't need to scrape figs that have all values OR figs that failed
    db_ids = (
        set(db_ids_appears_in)
        .intersection(set(db_ids_avg_price), set(db_ids_release_year))
        .union(set(db_ids_failed))
    )

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

    routine_scraping = read_minifigs_to_scrape(args.category)["id"].values.tolist()

    minifig_ids = owned + wanted + rest
    print(
        f"Number of minifigs to scrape: {len(owned)}+{len(wanted)}+{len(rest)}={len(minifig_ids)}, then {len(routine_scraping)}\n"
    )
    minifig_ids += routine_scraping

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
