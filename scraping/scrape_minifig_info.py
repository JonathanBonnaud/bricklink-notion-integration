import argparse
import json
import unicodedata
from time import sleep

import requests
from bs4 import BeautifulSoup
from lxml import etree
from tqdm import tqdm

from exceptions import CategoryNotFound, NameNotFound
from sqlite import insert_minifig

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0",
    "Accept-Encoding": "br, gzip, deflate",
    "Accept": "test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get_price(minifig_id: str) -> str:
    page = requests.get(
        f"https://www.bricklink.com/catalogPG.asp?M={minifig_id}&ColorID=0",
        headers=HEADERS,
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
    print(
        current_used_avg_price,
        last_used_avg_price,
        current_new_avg_price,
        last_new_avg_price,
    )

    price = (
        current_used_avg_price
        or last_used_avg_price
        or current_new_avg_price
        or last_new_avg_price
        or [""]
    )
    return unicodedata.normalize("NFKD", price[0])


def get_appears_in(minifig_id: str) -> list:
    page = requests.get(
        f"https://www.bricklink.com/catalogItemIn.asp?M={minifig_id}&in=S",
        headers=HEADERS,
    )
    soup = BeautifulSoup(page.text, "html.parser")
    html = etree.HTML(str(soup))

    xpath = '//*[@id="id-main-legacy-table"]/tr/td/table[2]/tr/td/center/table/tr/td[3]/font/a[1]/text()'
    set_list = html.xpath(xpath)
    return set_list


def beautifulsoup_parse(minifig_id: str) -> dict:
    print(f"Scraping page for minifig {minifig_id}...")
    url = f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={minifig_id}#T=P"
    print(url)
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
        release_year = html.xpath(xpath)[0]
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

    avg_price_raw = get_price(minifig_id)
    try:
        assert "PLN" in avg_price_raw
        avg_price_pln = float(avg_price_raw.replace(" ", "").replace("PLN", ""))
    except (AssertionError, ValueError):
        avg_price_pln = None

    appears_in = get_appears_in(minifig_id)

    d = {
        "id": minifig_id,
        "name": name,
        "release_year": int(release_year),
        "image": image_link,
        "bricklink": bl_link,
        "category": category,
        "sub_category": sub_category,
        "avg_price_raw": avg_price_raw,
        "avg_price_pln": avg_price_pln,
        "appears_in": str(appears_in),
    }
    # Write to db
    insert_minifig(d)
    return d


def read_from_file(category: str):
    with open(f"bl_fig_list/{category}_minifig_ids.json", "r") as file:
        ids = file.read()
    ids = json.loads(ids)
    return ids


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("category", help="category of minifigs to scrape", type=str)
    args = parser.parse_args()
    print(f"Scraping minifig info for category: {args.category}")

    # TODO: get list of ids from db to scrape only new ones

    minifig_ids = read_from_file(args.category)
    print(f"Total number of minifigs: {len(minifig_ids)}")

    batch_size = 10
    for batch in tqdm(range(0, len(minifig_ids), batch_size)):
        print(f"Batch {int((batch/batch_size)+1)}")
        for minifig_id in minifig_ids[batch : batch + batch_size]:
            try:
                minifig_dict = beautifulsoup_parse(minifig_id)
            except Exception as ex:
                print(f"An exception occurred: {ex}")
        print("Sleeping for 30 seconds...")
        sleep(30)
