import requests
from typing import Optional, Tuple
from constants import HEADERS
from bs4 import BeautifulSoup
from lxml import etree
import unicodedata
from constants import Bcolors
from exceptions import CategoryNotFound, NameNotFound, AvgPriceNotFound
from currency_converter import CurrencyConverter

cc = CurrencyConverter()


def get_proxies():
    with open(f"../http.txt", "r") as file:
        for line in file:
            yield line.strip()


def scrape_price_guide_page(
    item_type: str, item_id: str, proxy: str = None
) -> Optional[str]:
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
        raise AvgPriceNotFound()
        # return ""


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
