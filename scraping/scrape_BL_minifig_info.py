import argparse
import json
import unicodedata
from time import sleep
from typing import Optional
import requests
from bs4 import BeautifulSoup
from lxml import etree
from tqdm import tqdm
from requests.exceptions import ProxyError, ConnectTimeout, SSLError

from exceptions import CategoryNotFound, NameNotFound, AvgPriceNotFound
from sqlite import insert_minifig
from helpers_sqlite import read_minifigs_with_avg_price
from constants import HEADERS
from currency_converter import CurrencyConverter

cc = CurrencyConverter()


def get_price(minifig_id: str, proxy: str = None) -> Optional[str]:
    print("Scraping price...")
    proxies = {"https": proxy} if proxy else None
    page = requests.get(
        f"https://www.bricklink.com/catalogPG.asp?M={minifig_id}&ColorID=0",
        headers=HEADERS,
        proxies=proxies, timeout=10
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
    # print(
    #     current_used_avg_price,
    #     last_used_avg_price,
    #     current_new_avg_price,
    #     last_new_avg_price,
    # )

    price = (
        current_used_avg_price
        or last_used_avg_price
        or current_new_avg_price
        or last_new_avg_price
        or None
    )
    return unicodedata.normalize("NFKD", price[0]) if price else ""


def get_appears_in(minifig_id: str) -> str:
    print("Scraping Appears In...")
    page = requests.get(
        f"https://www.bricklink.com/catalogItemIn.asp?M={minifig_id}&in=S",
        headers=HEADERS,
    )
    soup = BeautifulSoup(page.text, "html.parser")
    html = etree.HTML(str(soup))

    xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[2]/tr/td/center/table/tr/td[3]/font/a[1]/text()'
    set_list = html.xpath(xpath)
    return ','.join(set_list)


def beautifulsoup_parse(minifig_id: str, proxy: str = None) -> dict:
    print(f"Scraping page for minifig {minifig_id}...")
    url = f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={minifig_id}#T=P"
    # print(url)
    page = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(page.text, "html.parser")
    html = etree.HTML(str(soup))

    try:
        xpath = '//*[@id="item-name-title"]/text()'
        name = html.xpath(xpath)[0]
    except IndexError:
        raise NameNotFound("No name found")

    try:
        xpath = '//*[@id="yearReleasedSec"]/text()'
        release_year = int(html.xpath(xpath)[0])
    except IndexError:
        print("No release year found")
        release_year = None

    try:
        xpath = '//*[@id="content"]/div/table/tr/td[1]/a[3]/text()'
        category = html.xpath(xpath)[0]
    except IndexError:
        raise CategoryNotFound("No category found")

    try:
        xpath = '//*[@id="content"]/div/table/tr/td[1]/a[4]/text()'
        sub_category = html.xpath(xpath)[0]
    except IndexError:
        print("No sub-category found")
        sub_category = None

    image_link = f"https://img.bricklink.com/ItemImage/MN/0/{minifig_id}.png"

    bl_link = f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={minifig_id}"

    avg_price_raw = get_price(minifig_id, proxy)
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
            avg_price_eur = round(cc.convert(avg_price, 'PLN', 'EUR'), 2)
        elif "EUR" in avg_price_raw:
            avg_price_eur = avg_price
            avg_price_pln = round(cc.convert(avg_price, 'EUR', 'PLN'), 2)
        elif "US $" in avg_price_raw:
            avg_price_eur = round(cc.convert(avg_price, 'USD', 'EUR'), 2)
            avg_price_pln = round(cc.convert(avg_price, 'USD', 'PLN'), 2)
        else:
            raise ValueError("Other currency")
    except (ValueError, AttributeError):
        # raise AvgPriceNotFound("No avg price found")
        avg_price_pln = None
        avg_price_eur = None

    appears_in = get_appears_in(minifig_id)

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
    # Write to db
    insert_minifig(d)
    return d


def read_from_file(category: str):
    with open(f"bl_fig_list/{category}_minifig_ids.json", "r") as file:
        ids = file.read()
    ids = json.loads(ids)
    return ids


def get_proxies():
    with open(f"http.txt", "r") as file:
        for line in file:
            yield line.strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("category", help="category of minifigs to scrape", type=str)
    parser.add_argument("--with-proxy", help="Execute with proxy", action="store_true")
    args = parser.parse_args()
    print(f"Scraping minifig info for category: {args.category}\n")

    # Get list of ids from db to scrape only new ones
    db_ids = read_minifigs_with_avg_price(args.category)

    minifig_ids = list(set(read_from_file(args.category)) - set(db_ids))
    print(f"Number of minifigs to scrape: {len(minifig_ids)}\n")

    if args.with_proxy:
        proxies = get_proxies()
        proxy = next(proxies)
    else:
        proxy = None
    batch_size = 10
    for batch in tqdm(range(0, len(minifig_ids), batch_size)):
        print("Sleeping for 5 seconds...")
        sleep(5)
        print(f"Batch {int((batch/batch_size)+1)}")
        for minifig_id in minifig_ids[batch: batch + batch_size]:
            try:
                minifig_dict = beautifulsoup_parse(minifig_id, proxy)
            except (ProxyError, AvgPriceNotFound, ConnectTimeout, SSLError) as e:
                print(f"Error '{e}'\n")
                if args.with_proxy:
                    proxy = next(proxies)
                    print(f"\ttrying another proxy... {proxy}")
