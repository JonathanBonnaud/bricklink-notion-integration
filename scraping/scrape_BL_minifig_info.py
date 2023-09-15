import argparse
import unicodedata
from time import sleep, time
from typing import Optional

import requests
from bs4 import BeautifulSoup
from currency_converter import CurrencyConverter
from lxml import etree
from requests.exceptions import ProxyError, ConnectTimeout, SSLError
from tqdm import tqdm

from constants import HEADERS, CATEGORY_CONFIG
from exceptions import CategoryNotFound, NameNotFound, AvgPriceNotFound
from helpers import Bcolors, get_proxies
from helpers_sqlite import (
    read_minifigs_with_avg_price,
    read_minifigs_with_appears_in,
    read_minifig_database,
)
from notion.helpers_notion import read_owned_minifigs
from sqlite import insert_minifig

cc = CurrencyConverter()


def get_price(minifig_id: str, proxy: str = None) -> Optional[str]:
    print("Scraping price...")
    proxies = {"https": proxy} if proxy else None
    page = requests.get(
        f"https://www.bricklink.com/catalogPG.asp?M={minifig_id}&ColorID=0",  # cID=Y
        headers=HEADERS,
        proxies=proxies,
        timeout=20,
    )
    soup = BeautifulSoup(page.text, "html.parser")
    html = etree.HTML(str(soup))

    xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[3]/tr[3]/td[4]/table/tr/td/table/tr[4]/td[2]/b/text()'
    current_used_avg_price = html.xpath(xpath)

    xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[3]/tr[3]/td[2]/table/tr/td/table/tr[4]/td[2]/b/text()'
    last_used_avg_price = html.xpath(xpath)

    xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[3]/tr[3]/td[3]/table/tr/td/table/tr[4]/td[2]/b/text()'
    current_new_avg_price = html.xpath(xpath)

    xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[3]/tr[3]/td[1]/table/tr/td/table/tr[4]/td[2]/b/text()'
    last_new_avg_price = html.xpath(xpath)

    price = (
        current_used_avg_price
        or last_used_avg_price
        or current_new_avg_price
        or last_new_avg_price
        or None
    )
    if price:
        return unicodedata.normalize("NFKD", price[0])
    else:
        print(f"{Bcolors.FAIL}Warning: No price found{Bcolors.ENDC}")
        return ""


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
        try:
            xpath = '//*[@id="item-name-title"]/text()'
            name = html.xpath(xpath)[0]
        except IndexError:
            raise NameNotFound(f"{Bcolors.FAIL}Warning: No name found{Bcolors.ENDC}")

        try:
            xpath = '//*[@id="content"]/div/table/tr/td[1]/a[3]/text()'
            category = html.xpath(xpath)[0]
        except IndexError:
            raise CategoryNotFound(
                f"{Bcolors.FAIL}Warning: No category found{Bcolors.ENDC}"
            )

        try:
            xpath = '//*[@id="content"]/div/table/tr/td[1]/a[4]/text()'
            sub_category = html.xpath(xpath)[0]
        except IndexError:
            print(f"{Bcolors.WARNING}Info: No sub-category found{Bcolors.ENDC}")
            sub_category = None

    # Then scrape the missing info
    image_link = f"https://img.bricklink.com/ItemImage/MN/0/{minifig_id}.png"
    bl_link = f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={minifig_id}"

    try:
        xpath = '//*[@id="yearReleasedSec"]/text()'
        release_year = int(html.xpath(xpath)[0])
    except IndexError:
        print(f"{Bcolors.WARNING}Info: No release year found{Bcolors.ENDC}")
        release_year = None

    avg_price_raw = get_price(minifig_id, proxy=proxy)
    try:
        avg_price = float(
            avg_price_raw.replace(" ", "")
            .replace("PLN", "")
            .replace("EUR", "")
            .replace("US $", "")
            .replace(",", "")
        )
        if "PLN" in avg_price_raw:
            avg_price_pln = avg_price
            avg_price_eur = round(cc.convert(avg_price, "PLN", "EUR"), 2)
        elif "EUR" in avg_price_raw:
            avg_price_eur = avg_price
            avg_price_pln = round(cc.convert(avg_price, "EUR", "PLN"), 2)
        elif "US $" in avg_price_raw:
            avg_price_eur = round(cc.convert(avg_price, "USD", "EUR"), 2)
            avg_price_pln = round(cc.convert(avg_price, "USD", "PLN"), 2)
        else:
            raise ValueError("Other currency")
    except (ValueError, AttributeError):
        avg_price_raw = None
        avg_price_pln = None
        avg_price_eur = None

    appears_in = get_appears_in(minifig_id, proxy=proxy)

    d = {
        "id": minifig_id,
        "name": name,
        "release_year": release_year,
        "image": image_link,
        "bricklink": bl_link,
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
        "--from-collec",
        help="Focus on getting missing values from the user's collection",
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

    if args.from_collec:
        minifig_ids = list(set(read_owned_minifigs(args.category)) - set(db_ids))
    else:
        minifig_ids = list(
            set(read_minifig_database(args.category)["id"].values) - set(db_ids)
        )

    if args.sort_oldest:
        minifig_ids.sort()
    else:
        minifig_ids.sort(reverse=True)
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
                except (ProxyError, AvgPriceNotFound, ConnectTimeout, SSLError) as e:
                    print(f"Error '{e}'\n")
                    if args.with_proxy:
                        proxy = next(proxies)
                        print(f"\ttrying another proxy... {proxy}")
            print("Sleeping for 30 seconds...")
            sleep(30)
    except KeyboardInterrupt:
        print("Interrupted manually")
        pass
    end = time()
    print(f"Time elapsed: {round(end - start, 2)}s")
