import numpy as np
import pandas as pd
import sqlite3
import argparse
from constants import CATEGORY_CONFIG


def process_tsv_file(cat_id: int):
    with open("data/Minifigures.txt", "r", encoding="utf-8") as f:
        df = pd.read_csv(f, delimiter="\t")
        print(f"Number of all minifigs: {df.shape[0]}")

    # Clean and rename columns
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df.rename(columns={"number": "id", "category_name": "category", "year_released": "release_year"}, inplace=True)
    print(f"Cleaned columns: {list(df.columns)}")

    # Transform data
    df["sub_category"] = df.agg(lambda x: ' / '.join(x["category"].split(" / ")[1:]), axis=1)
    df["category"] = df["category"].str.split(" / ").str[0].str.strip()
    df["image"] = df.agg(lambda x: f"https://img.bricklink.com/ItemImage/MN/0/{x['id']}.png", axis=1)
    df["bricklink"] = df.agg(lambda x: f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={x['id']}", axis=1)
    df[df["release_year"] == "?"] = np.NaN

    df["appears_in"] = ["[]" for _ in range(len(df.index))]

    # Filter data by category
    df = df[df["category_id"] == cat_id]

    # Drop unnecessary columns
    df.drop(columns=["category_id"], inplace=True)
    print(f"Filtered minifigs: {df.shape[0]}")
    return df


def insert_to_sqlite(df: pd.DataFrame):
    try:
        assert pd.Series(df["id"]).is_unique
        conn = sqlite3.connect('data/lego.db')
        df.to_sql("minifigs", conn, if_exists='append', index=False)
        print(f"Data inserted to sqlite: {df.shape[0]}")
    except AssertionError:
        print("Cannot insert to DB: IDs are not unique")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("category", help="category of minifigs to scrape", type=str)
    args = parser.parse_args()
    print(f"Scraping category: {args.category}")

    category_id = CATEGORY_CONFIG[args.category]["cat_id"]

    data = process_tsv_file(int(category_id))
    insert_to_sqlite(data)
