import asyncio
import ssl
import unicodedata
from typing import Optional, Tuple

import aiohttp
import certifi
import requests
from bs4 import BeautifulSoup
from currency_converter import CurrencyConverter
from lxml import etree
from tqdm.asyncio import tqdm

from constants import HEADERS, Bcolors
from exceptions import BLQuotaExceeded, CategoryNotFound, NameNotFound

cc = CurrencyConverter()


def get_proxies():
    with open(f"http.txt", "r") as file:
        for line in file:
            yield line.strip()


async def check_image_validity(url: str, ssl_context) -> bool:
    async with aiohttp.ClientSession() as session:
        resp = await session.get(url, headers=HEADERS, ssl=ssl_context)
    return resp.status == 200


async def async_run_image_checks(links: list):
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    tasks = [
        asyncio.ensure_future(
            check_image_validity(url, ssl_context)
        )  # creating task starts coroutine
        for url in links
    ]
    return await tqdm.gather(*tasks)  # asyncio.gather


def get_image_links_validity(links: list) -> list[bool]:
    print("Checking image links...")
    return asyncio.run(async_run_image_checks(links))


def scrape_price_guide_page(
    item_type: str, item_id: str, proxy: str = None
) -> Tuple[Optional[str], bool]:
    print("Scraping price...")
    proxies = {"https": proxy} if proxy else None
    page = requests.get(
        f"https://www.bricklink.com/catalogPG.asp?{item_type}={item_id}&ColorID=0&viewExclude=Y",  # cID=Y
        headers=HEADERS,
        proxies=proxies,
        timeout=20,
    )
    soup = BeautifulSoup(page.text, "html.parser")
    html = etree.HTML(str(soup))

    try:
        xpath_error = '//*[@id="blErrorTitle"]'
        assert not html.xpath(
            xpath_error
        )  # Check that error message "Quota Exceeded" is not present
    except AssertionError:
        raise BLQuotaExceeded()

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
        return unicodedata.normalize("NFKD", price[0]), False
    else:
        print(f"{Bcolors.FAIL}Warning: No price found{Bcolors.ENDC}")
        # raise AvgPriceNotFound()
        return "", True


def convert_raw_price(raw_price: str) -> Tuple:
    try:
        avg_price = float(
            raw_price.replace(" ", "")
            .replace("PLN", "")
            .replace("EUR", "")
            .replace("US $", "")
            .replace(",", "")
        )
        if "PLN" in raw_price:
            avg_price_pln = avg_price
            avg_price_eur = round(cc.convert(avg_price, "PLN", "EUR"), 2)
        elif "EUR" in raw_price:
            avg_price_eur = avg_price
            avg_price_pln = round(cc.convert(avg_price, "EUR", "PLN"), 2)
        elif "US $" in raw_price:
            avg_price_eur = round(cc.convert(avg_price, "USD", "EUR"), 2)
            avg_price_pln = round(cc.convert(avg_price, "USD", "PLN"), 2)
        else:
            raise ValueError("Other currency")
    except (ValueError, AttributeError):
        raw_price = None
        avg_price_pln = None
        avg_price_eur = None
    return raw_price, avg_price_pln, avg_price_eur


def scrape_initial_values(html) -> Tuple[str, str, str]:
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

    return name, category, sub_category
