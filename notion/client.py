from notion_client import Client
from notion.private_secrets import NOTION_LEGO_COLLECTION_SECRET, NOTION_JONATHAN_SECRET

from tqdm import tqdm
from notion_client.helpers import iterate_paginated_api, collect_paginated_api
from notion_client import APIErrorCode, APIResponseError
from sqlite import insert_notion_mapping
import argparse
from helpers_sqlite import read_minifig_database, get_page_id_from_sqlite, get_bl_ids_from_sqlite

notion = Client(auth=NOTION_JONATHAN_SECRET)


def read_db_id_from_file() -> str:
    with open(f"notion/database_id.txt", "r") as file:
        return str(file.read())


def main(row):
    db_id = read_db_id_from_file()

    try:
        assert row["avg_price_pln"] != 0
        avg_price_pln = float(row["avg_price_pln"])
    except AssertionError:
        avg_price_pln = None

    data = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {"rich_text": [{"text": {"content": row["name"]}}]},
            "Id": {"title": [{"text": {"content": row["id"]}}]},
            "Category": {"select": {"name": row["category"]}},
            "Sub Category": {
                "rich_text": [{"text": {"content": row["sub_category"] or ""}}]
            },
            "Image": {
                "files": [{"name": row["image"], "external": {"url": row["image"]}}]
            },
            "BrickLink": {"url": row["bricklink"]},
            "Avg price raw": {
                "rich_text": [{"text": {"content": row["avg_price_raw"] or ""}}]  # FIXME: normalize before inserting to sqlite (currently "" and None)
            },
            "Avg price PLN": {"number": avg_price_pln},
            "Release Year": {"number": row["release_year"]},
            "Appears In": {"rich_text": [{"text": {"content": row["appears_in"]}}]},
        },
    }
    page_id = get_page_id_from_sqlite(row["id"])

    try:
        page = notion.pages.retrieve(page_id)
        notion.pages.update(page_id=page["id"], **data)
        return 1  # UPDATED
    except APIResponseError:
        page_created = notion.pages.create(database_id=db_id, **data)
        insert_notion_mapping(page_created["id"], row["id"])
        return 2  # INSERTED


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category", nargs="?", help="category of minifigs to send", type=str
    )
    parser.add_argument("--insert", help="Only execute inserts of new", action="store_true")
    args = parser.parse_args()
    category = args.category
    print(f"Sending minifigs for category: {category or 'all'}")

    if args.insert:
        bl_ids_df = get_bl_ids_from_sqlite()
        minifig_df = read_minifig_database(category)
        df = minifig_df[~minifig_df["id"].isin(bl_ids_df["bl_id"])]
    else:
        df = read_minifig_database(category)

    print(f"Number of minifigs to process: {df.shape[0]}")

    inserted = 0
    updated = 0

    for _, df_row in tqdm(df.iterrows(), total=df.shape[0]):
        inserted_or_updated = main(df_row)
        if inserted_or_updated == 2:
            inserted += 1
        elif inserted_or_updated == 1:
            updated += 1

    print(f"Inserted: {inserted}, updated: {updated}")
