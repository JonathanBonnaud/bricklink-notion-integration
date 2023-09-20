import argparse
from time import sleep, time

import requests
from bs4 import BeautifulSoup
from lxml import etree
from requests.exceptions import ProxyError, ConnectTimeout, SSLError
from tqdm import tqdm

from constants import HEADERS, CATEGORY_CONFIG, Bcolors
from exceptions import CategoryNotFound, NameNotFound, AvgPriceNotFound
from scraping.helpers import (
    get_proxies,
    scrape_price_guide_page,
    convert_raw_price,
    scrape_initial_values,
)
from helpers_sqlite import (
    read_sets_with_avg_price,
    read_sets_with_release_year,
    read_sets_database,
)
from notion.helpers_notion import read_owned, read_wanted
from sqlite import insert_set


# def get_minifigs_included(set_id: str, proxy: str = None) -> Optional[str]:
#     print("Scraping Minifigs Included...")
#     proxies = {"https": proxy} if proxy else None
#     page = requests.get(
#         f"https://www.bricklink.com/catalogItemInv.asp?S={set_id}&viewItemType=M",
#         headers=HEADERS,
#         proxies=proxies,
#         timeout=20,
#     )
#     soup = BeautifulSoup(page.text, "html.parser")
#     html = etree.HTML(str(soup))
#
#     xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[2]/tr/td/center/table/tr/td[3]/font/a[1]/text()'
#     set_list = html.xpath(xpath)
#     if appears_in_str := ",".join(set_list):
#         return appears_in_str
#     else:
#         print(f"{Bcolors.WARNING}Warning: No Minifigs Included found{Bcolors.ENDC}")
#         return None


def beautifulsoup_parse(
    set_id: str,
    proxy: str = None,
    scrape_all: bool = False,
    scrape_only_release_year: bool = False,
) -> None:
    url = f"https://www.bricklink.com/v2/catalog/catalogitem.page?S={set_id}#T=P"
    print(f"Scraping page for set {set_id}... [{url}]")

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
        xpath = '//*[@id="id_divBlock_Main"]/table[1]/tbody/tr[2]/td[2]/center/table/tbody/tr[1]/td/table/tbody/tr/td[1]/font/a/text()'
        release_year = int(html.xpath(xpath)[0])
    except IndexError:
        print(f"{Bcolors.WARNING}Info: No release year found{Bcolors.ENDC}")
        release_year = None

    avg_price_raw = ""
    if not scrape_only_release_year:
        avg_price_raw = scrape_price_guide_page("S", set_id, proxy=proxy)

    avg_price_raw, avg_price_pln, avg_price_eur = convert_raw_price(avg_price_raw)

    d = {
        "id": set_id,
        "name": name,
        "release_year": release_year,
        "image": None,
        "bricklink": None,
        "category": category,
        "sub_category": sub_category,
        "avg_price_raw": avg_price_raw,
        "avg_price_pln": avg_price_pln,
        "avg_price_eur": avg_price_eur,
        "minifigs_included": None,
    }
    # Write to sqlite db
    insert_set(d)
    sleep(5)
    print("\n========================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category",
        choices=CATEGORY_CONFIG.keys(),
        help="category of sets to scrape",
        type=str,
    )
    parser.add_argument("--with-proxy", help="Execute with proxy", action="store_true")
    parser.add_argument("--scrape-all", help="Scrape all fields", action="store_true")
    parser.add_argument(
        "--scrape-only-release-year",
        help="Scrape release year field",
        action="store_true",
    )
    parser.add_argument(
        "--sort-oldest",
        help="Scrape minifigs from the oldest to the newest",
        action="store_true",
    )
    args = parser.parse_args()
    print(f"Scraping sets info for category: {args.category}\n")

    if args.scrape_only_release_year:
        db_ids = read_sets_with_release_year(args.category)["id"].values
    else:
        # Get sets with avg_price to filer them out
        db_ids = read_sets_with_avg_price(args.category)["id"].values

    # Order of ids to scrape 1- owned > 2- wanted > 3- rest ordered by id
    owned = list(set(read_owned("sets", args.category)) - set(db_ids))
    wanted = list(
        set(read_wanted("sets", args.category)) - set(owned) - set(db_ids)
    )  # In case owned and forgot to uncheck wanted
    rest = list(
        set(read_sets_database(args.category)["id"].values)
        - set(owned)
        - set(wanted)
        - set(db_ids)
    )

    if args.sort_oldest:
        rest.sort()
    else:
        rest.sort(reverse=True)

    set_ids = owned + wanted + rest
    print(f"Number of sets to scrape: {len(set_ids)}\n")

    if args.with_proxy:
        proxies = get_proxies()
        proxy = next(proxies)
    else:
        proxy = None

    start = time()
    MAX_SCRAPE = 100  # len(set_ids)
    batch_size = 10
    try:
        for batch in tqdm(range(0, MAX_SCRAPE, batch_size)):
            print(f"Batch {int((batch/batch_size)+1)}")
            for minifig_id in set_ids[batch : batch + batch_size]:
                try:
                    beautifulsoup_parse(
                        minifig_id,
                        proxy,
                        args.scrape_all,
                        args.scrape_only_release_year,
                    )
                except (ProxyError, ConnectTimeout, SSLError) as e:
                    print(f"Error '{e}'\n")
                    if args.with_proxy:
                        proxy = next(proxies)
                        print(f"\ttrying another proxy... {proxy}")
                except AvgPriceNotFound as e:
                    end = time()
                    print(f"Time elapsed: {round(end - start, 2)}s")
                    exit()
            print("Sleeping for 30 seconds...")
            sleep(30)
    except KeyboardInterrupt:
        print("Interrupted manually")
        pass
    end = time()
    print(f"Time elapsed: {round(end - start, 2)}s")
