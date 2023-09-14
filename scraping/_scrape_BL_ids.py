import argparse

import requests
from bs4 import BeautifulSoup
from lxml import etree

from constants import HEADERS, CATEGORY_CONFIG


def beautifulsoup_parse(bl_type: str, category: str, pg: int):
    print(f"Scraping page {pg}")

    cat_id = CATEGORY_CONFIG[category]["cat_id"]
    page = requests.get(
        f"https://www.bricklink.com/catalogList.asp?pg={pg}&catString={cat_id}&catType={bl_type}",
        headers=HEADERS,
    )

    soup = BeautifulSoup(page.text, "html.parser")
    xpath = '/html/body/div[contains(@class, "catalog-list__body")]/form[@id="ItemEditForm"]/table/tr/td/table[contains(@class, "catalog-list__body-main--alternate-row")]/tr/td[2]/font/a[1]/text()'
    html = etree.HTML(str(soup))
    list_of_minifigs = html.xpath(xpath)

    minifig_list = [minifig_id for minifig_id in list_of_minifigs]

    return minifig_list


def write_to_file(item_type: str, category: str, ids: list):
    with open(f"BL_list/{category}_{item_type}_ids.json", "w") as file:
        file.write(str(ids).replace("'", '"'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("category", choices=CATEGORY_CONFIG.keys(), help="category of minifigs to scrape", type=str)
    parser.add_argument("type", choices=['minifigs', 'sets'], help="type to scrape", type=str)
    args = parser.parse_args()
    print(f"Scraping category: {args.category}")

    bl_type = "M" if args.type == "minifigs" else "S"

    page_number = 0
    list_all = []

    while True:
        try:
            page_number += 1
            page_minifig_ids_list = beautifulsoup_parse(bl_type, args.category, page_number)
            assert page_minifig_ids_list[0] not in list_all
            list_all.extend(page_minifig_ids_list)
        except Exception as ex:
            print("Last page:", page_number - 1)
            break  # exit `while` loop

    # Finally write all ids to file
    write_to_file(args.type, args.category, list_all)  # TODO: instead write to table bl_ids[type, category, id]
