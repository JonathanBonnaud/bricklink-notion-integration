import argparse
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from lxml import etree

from constants import HEADERS, CATEGORY_CONFIG
from exceptions import BLQuotaExceeded
from helpers_sqlite import write_to_sql
from helpers import get_image_links_validity


def beautifulsoup_parse(arg_type: str, category: str, pg: int):
    bl_type = "M" if arg_type == "minifigs" else "S"
    bl_img_type = ("MN",) if arg_type == "minifigs" else ("ON", "SN")

    cat_id = CATEGORY_CONFIG[category]["cat_id"]
    page = requests.get(
        f"https://www.bricklink.com/catalogList.asp?pg={pg}&catString={cat_id}&catType={bl_type}",
        headers=HEADERS,
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

    # Get ids
    xpath = '/html/body/div[contains(@class, "catalog-list__body")]/form[@id="ItemEditForm"]/table/tr/td/table[contains(@class, "catalog-list__body-main--alternate-row")]/tr/td[2]/font/a[1]/text()'
    list_of_ids = html.xpath(xpath)

    # Get names
    xpath = '//*[@id="ItemEditForm"]/table[1]/tr/td/table/tr/td[3]/strong/text()'
    list_of_names = html.xpath(xpath)

    # Get subcategory
    xpath = '//*[@id="ItemEditForm"]/table[1]/tr/td/table/tr/td[3]/font'
    list_of_categories = html.xpath(xpath)
    list_of_subcategories = [
        " / ".join([elem.text for elem in font.iter("a")][3:])
        for font in list_of_categories
    ]

    # Get images
    if bl_type == "M":
        list_of_images = [
            f"https://img.bricklink.com/ItemImage/{bl_img_type[0]}/0/{x}.png"
            for x in list_of_ids
        ]
    else:
        default_urls, second_urls = map(
            list,
            zip(
                *[
                    (
                        f"https://img.bricklink.com/ItemImage/{bl_img_type[0]}/0/{x}.png",
                        f"https://img.bricklink.com/ItemImage/{bl_img_type[1]}/0/{x}.png",
                    )
                    for x in list_of_ids
                ]
            ),
        )
        list_of_images = [
            url1 if is_valid else url2
            for url1, is_valid, url2 in zip(
                default_urls, get_image_links_validity(default_urls), second_urls
            )
        ]

    data = {
        "id": list_of_ids,
        "name": list_of_names,
        "category": [CATEGORY_CONFIG[category]["name"] for _ in list_of_ids],
        "sub_category": list_of_subcategories,
        "image": list_of_images,
        "bricklink": [
            f"https://www.bricklink.com/v2/catalog/catalogitem.page?{bl_type}={x}"
            for x in list_of_ids
        ],
        "last_scraped_at": [
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") for _ in list_of_ids
        ],
    }

    rows_inserted = write_to_sql(arg_type, data)

    return data["id"], rows_inserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category",
        choices=CATEGORY_CONFIG.keys(),
        help="category of minifigs to scrape",
        type=str,
    )
    parser.add_argument(
        "type", choices=["minifigs", "sets"], help="type to scrape", type=str
    )
    args = parser.parse_args()
    print(f"Scraping {args.type} for category: {args.category} ...")

    page_number = 0
    list_all = []
    total_inserted = 0

    while True:
        try:
            page_number += 1
            page_ids_list, nb_inserted = beautifulsoup_parse(
                args.type, args.category, page_number
            )
            total_inserted += nb_inserted
            assert page_ids_list[0] not in list_all
            print(f"Page {page_number} done")
            list_all.extend(page_ids_list)
        except AssertionError:
            print("Last page:", page_number - 1)
            break  # exit `while` loop

    print(f"Total new inserted: {total_inserted}\n")
