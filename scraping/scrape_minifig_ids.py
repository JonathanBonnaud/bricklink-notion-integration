import argparse

import requests
from bs4 import BeautifulSoup
from lxml import etree

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:12.0) Gecko/20100101 Firefox/12.0",
    "Accept-Encoding": "br, gzip, deflate",
    "Accept": "test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CATEGORY_CONFIG = {
    "sw": {
        "cat_id": "65",
    },
    "sh": {
        "cat_id": "768",
    },
    "avt": {
        "cat_id": "1236",
    },
    "hp": {
        "cat_id": "227",
    },
    "hfw": {
        "cat_id": "1227",
    },
}


def beautifulsoup_parse(category: str, pg: int):
    print(f"Scraping page {pg}")

    cat_id = CATEGORY_CONFIG[category]["cat_id"]
    page = requests.get(
        f"https://www.bricklink.com/catalogList.asp?pg={pg}&catString={cat_id}&catType=M",
        headers=HEADERS,
    )

    soup = BeautifulSoup(page.text, "html.parser")
    xpath = '/html/body/div[contains(@class, "catalog-list__body")]/form[@id="ItemEditForm"]/table/tr/td/table[contains(@class, "catalog-list__body-main--alternate-row")]/tr/td[2]/font/a[1]/text()'
    html = etree.HTML(str(soup))
    list_of_minifigs = html.xpath(xpath)

    minifig_list = [minifig_id for minifig_id in list_of_minifigs]

    return minifig_list


def write_to_file(category: str, ids: list):
    with open(f"bl_fig_list/{category}_minifig_ids.json", "w") as file:
        file.write(str(ids).replace("'", '"'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("category", help="category of minifigs to scrape", type=str)
    args = parser.parse_args()
    print(f"Scraping category: {args.category}")

    page_number = 0
    list_all = []

    while True:
        try:
            page_number += 1
            page_minifig_ids_list = beautifulsoup_parse(args.category, page_number)
            assert page_minifig_ids_list[0] not in list_all
            list_all.extend(page_minifig_ids_list)
        except Exception as ex:
            print("Last page:", page_number - 1)
            break  # exit `while` loop

    # Finally write all ids to file
    write_to_file(args.category, list_all)
