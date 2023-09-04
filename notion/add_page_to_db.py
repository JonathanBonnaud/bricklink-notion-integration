import argparse
import json
import sqlite3

import numpy as np
import pandas as pd
import requests
from tqdm import tqdm

from notion.private_secrets import NOTION_LEGO_COLLECTION_SECRET
from constants import CATEGORY_MAPPING

HEADERS = {
    "Authorization": f"Bearer {NOTION_LEGO_COLLECTION_SECRET}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def read_minifig_database(category: str) -> pd.DataFrame:
    where = f"WHERE category = '{CATEGORY_MAPPING[category]}'" if category else ""

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where}", conn)
    df["avg_price_pln"].fillna(0, inplace=True)

    print(f"Read {df.shape[0]} minifigs from database")
    return df


def read_db_id_from_file() -> str:
    with open(f"notion/database_id.txt", "r") as file:
        return str(file.read())


def create_minifig_page(db_id: str, row: pd.Series):
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
                "rich_text": [{"text": {"content": row["avg_price_raw"]}}]
            },
            "Avg price PLN": {"number": avg_price_pln},
            "Release Year": {"number": row["release_year"]},
            "Appears In": {"rich_text": [{"text": {"content": row["appears_in"]}}]},
        },
    }
    #         "Store availability": {
    #             "multi_select": [
    #                 {'name': 'Duc Loi Market', 'color': 'blue'},
    #                 {'name': 'Rainbow Grocery', 'color': 'gray'}
    #             ]
    #         },

    res = requests.post(
        "https://api.notion.com/v1/pages/", data=json.dumps(data), headers=HEADERS
    )
    try:
        res.raise_for_status()
    except Exception:
        print(json.dumps(res.json(), sort_keys=True, indent=4))
        # print(res.json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category", nargs="?", help="category of minifigs to send", type=str
    )
    args = parser.parse_args()
    print(f"Sending minifigs for category: {args.category or 'all'}")

    database_id = read_db_id_from_file()
    print(f"Writing to database '{database_id}'")

    df = read_minifig_database(args.category)
    for _, df_row in tqdm(df.iterrows(), total=df.shape[0]):
        create_minifig_page(database_id, df_row)
