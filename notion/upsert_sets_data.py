import argparse

import pandas as pd
from notion_client import APIResponseError
from tqdm import tqdm

from helpers_sqlite import (
    read_sets_database,
    get_page_id_from_sqlite,
    get_bl_ids_from_sqlite,
)
from notion.helpers_notion import account_setup
from sqlite import insert_notion_mapping

NOTION, PREFIX, _ = account_setup()


def read_db_id_from_file() -> str:
    with open(f"notion/files/{PREFIX}_sets_database_id.txt", "r") as file:
        return str(file.read())


def upsert_set_page(row: pd.Series, db_id: str):
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
                "rich_text": [{"text": {"content": row["avg_price_raw"] or ""}}]
            },
            "Avg price PLN": {"number": row["avg_price_pln"]},
            "Avg price EUR": {"number": row["avg_price_eur"]},
            "Release Year": {"number": row["release_year"]},
            # # /!\ Need to be excluded not to update 'Minifigs Included' with empty values /!\
            # "Minifigs Included": {
            #     "relation": [
            #         # {
            #         #     "id": ""
            #         # }
            #     ],
            # },
        },
    }
    page_id = get_page_id_from_sqlite(row["id"], PREFIX)

    try:
        page = NOTION.pages.retrieve(page_id)
        NOTION.pages.update(page_id=page["id"], **data)
        return 1  # UPDATED
    except APIResponseError:
        page_created = NOTION.pages.create(database_id=db_id, **data)
        insert_notion_mapping(page_created["id"], row["id"], PREFIX)
        return 2  # INSERTED


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category", nargs="?", help="category of minifigs to send", type=str
    )
    parser.add_argument(
        "--insert", help="Only execute inserts of new", action="store_true"
    )
    parser.add_argument(
        "--update", help="Only execute update of existing", action="store_true"
    )
    args = parser.parse_args()
    category = args.category
    print(f"Sending sets for category: {category or 'all'}")

    if args.insert:
        bl_ids_df = get_bl_ids_from_sqlite(PREFIX)
        sets_df = read_sets_database(category)
        df = sets_df[~sets_df["id"].isin(bl_ids_df["bl_id"])]
    elif args.update:
        bl_ids_df = get_bl_ids_from_sqlite(PREFIX)
        sets_df = read_sets_database(category)
        df = sets_df[sets_df["id"].isin(bl_ids_df["bl_id"])]
    else:
        df = read_sets_database(category)

    print(f"Number of sets to process: {df.shape[0]}")

    inserted = 0
    updated = 0

    db_id = read_db_id_from_file()

    # Insert most recent first
    df = df.sort_values(by=["release_year", "id"], ascending=False)

    for _, df_row in tqdm(df.iterrows(), total=df.shape[0]):
        inserted_or_updated = upsert_set_page(df_row, db_id)
        if inserted_or_updated == 2:
            inserted += 1
        elif inserted_or_updated == 1:
            updated += 1

    print(f"Inserted: {inserted}, updated: {updated}")
