import argparse

import numpy as np
import pandas as pd
from notion_client import APIResponseError
from notion_client import Client
from tqdm import tqdm

from helpers_sqlite import (
    read_minifig_database,
    get_page_id_from_sqlite,
    get_bl_ids_from_sqlite,
    read_minifigs_with_appears_in,
    read_minifigs_with_avg_price,
)
from notion.private_secrets import NOTION_JONATHAN_SECRET
from sqlite import insert_notion_mapping

notion = Client(auth=NOTION_JONATHAN_SECRET)


def read_db_id_from_file() -> str:
    with open(f"notion/minifigs_database_id.txt", "r") as file:
        return str(file.read())


def get_relations(appears_in: str) -> list:
    relations = []
    try:
        for set_id in appears_in.split(","):
            if page_id := get_page_id_from_sqlite(set_id):
                relations.append({"id": page_id})
    except AttributeError:  # appears_in is None
        pass
    return relations


def upsert_minifig_page(row: pd.Series, db_id: str):
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
            "Avg price PLN": {
                "number": row["avg_price_pln"]
                if not np.isnan(row["avg_price_pln"])
                else None
            },
            "Avg price EUR": {
                "number": row["avg_price_eur"]
                if not np.isnan(row["avg_price_eur"])
                else None
            },
            "Release Year": {
                "number": row["release_year"]
                if not np.isnan(row["release_year"])
                else None
            },
            "Appears In": {"relation": get_relations(row["appears_in"])},
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
    parser.add_argument(
        "--avg-price", help="Focus on getting missing avg_price", action="store_true"
    )
    parser.add_argument(
        "--appears-in", help="Focus on getting missing appears_in", action="store_true"
    )
    args = parser.parse_args()
    category = args.category
    print(f"Sending minifigs for category: {category or 'all'}")

    if args.insert:
        bl_ids_df = get_bl_ids_from_sqlite()
        minifig_df = read_minifig_database(category)
        df = minifig_df[~minifig_df["id"].isin(bl_ids_df["bl_id"])]
    elif args.update:
        bl_ids_df = get_bl_ids_from_sqlite()
        if args.avg_price:
            minifig_df = read_minifigs_with_avg_price(category)
        elif args.appears_in:
            minifig_df = read_minifigs_with_appears_in(category)
        else:
            minifig_df = read_minifig_database(category)
        df = minifig_df[minifig_df["id"].isin(bl_ids_df["bl_id"])]
    else:
        df = read_minifig_database(category)

    print(f"Number of minifigs to process: {df.shape[0]}")

    inserted = 0
    updated = 0

    db_id = read_db_id_from_file()

    # Insert most recent first
    df = df.sort_values(by=["release_year", "id"], ascending=False)

    for _, df_row in tqdm(df.iterrows(), total=df.shape[0]):
        inserted_or_updated = upsert_minifig_page(df_row, db_id)
        if inserted_or_updated == 2:
            inserted += 1
        elif inserted_or_updated == 1:
            updated += 1

    print(f"Inserted: {inserted}, updated: {updated}")
