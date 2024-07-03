import argparse
import sqlite3

import pandas as pd
from notion_client.helpers import collect_paginated_api

from constants import CATEGORY_CONFIG
from notion.helpers_notion import account_setup, read_db_id_from_file

NOTION, PREFIX, _ = account_setup()


def delete(bl_id: str, page_id: str, account_name: str):
    conn = sqlite3.connect("data/lego.db")
    cursor = conn.cursor()
    cursor.execute(
        f"DELETE FROM notion_mapping WHERE bl_id = '{bl_id}' AND page_id = '{page_id}' AND account_name = '{account_name}';"
    )
    conn.commit()
    # print("Total number of rows updated :", conn.total_changes)
    changes = conn.total_changes
    conn.close()
    return changes


def read_notion_db(db_type: str, category: str = None):
    print("Reading Notion DB...")
    cat = CATEGORY_CONFIG[category]["name"] if category is not None else None
    filters = (
        {
            "and": [
                {"property": "Category", "select": {"equals": cat}},
            ]
        }
        if cat is not None
        else None
    )

    all_results = collect_paginated_api(
        NOTION.databases.query,
        database_id=read_db_id_from_file(PREFIX, db_type),
        filter=filters,
    )
    print(f"There are {len(all_results)} {db_type} from {cat or 'all'} category")
    return [result for result in all_results]


def get_notion_mapping_from_sqlite(account_name: str, cat: str = None) -> pd.DataFrame:
    where = f"WHERE account_name = '{account_name}'"
    where = f"{where} AND bl_id LIKE '{cat}%'" if cat else where

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(
        f"SELECT page_id, bl_id FROM notion_mapping {where}",
        conn,
    )
    conn.close()
    return df


if __name__ == "__main__":
    """
    WARNING: only works for minifigs for now AND always use a category
    """
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
    cat = args.category
    types = args.type

    if cat is None:
        exit(r"/!\ Please specify a category!!!")

    existing_pages = read_notion_db(types, cat)

    # # REINSERT MISTAKENLY DELETED ENTRIES
    # tot = 0
    # for page in tqdm(existing_pages):
    #     r = insert_notion_mapping(
    #         page["id"], page["properties"]["Id"]["title"][0]["plain_text"], PREFIX
    #     )
    #     tot += r
    # print(f"Inserted {tot}")

    existing_page_ids = [p["id"] for p in existing_pages]
    existing_bl_ids = [
        p["properties"]["Id"]["title"][0]["plain_text"] for p in existing_pages
    ]

    print(f"Unique ones: {len(set(existing_bl_ids))}")
    seen = set()
    dupes = [p for p in existing_bl_ids if p in seen or seen.add(p)]
    print(f"Found {len(dupes)} duplicates: {dupes}")

    if len(dupes) == 0:
        exit()

    df = get_notion_mapping_from_sqlite(PREFIX, cat)  # In sql db
    print("\nThese are the Notion pages to KEEP (delete the other one):")
    print(df[df.bl_id.isin(dupes)])

    a = input("Enter DELETE to delete duplicates in SQL db:")
    if a != "DELETE":
        exit("Aborted")

    if len(dupes) > 0:
        tot = 0
        for _, df_row in df.iterrows():
            if df_row["page_id"] not in existing_page_ids:  # In notion db
                deletions = delete(df_row["bl_id"], df_row["page_id"], PREFIX)
                tot += deletions
        print(f"Deleted {tot} rows")
