import numpy as np
import pandas as pd
import sqlite3
import argparse
from constants import CATEGORY_CONFIG

TYPE_CONFIG = {
    "minifigs": {
        "file_name": "Minifigures.txt",
        "table_name": "minifigs",
    },
    "sets": {
        "file_name": "Sets.txt",
        "table_name": "sets",
    }
}


def process_tsv_file(type_val: str, cat_id: int):
    file_name = TYPE_CONFIG[type_val]["file_name"]
    with open(f"data/{file_name}", "r", encoding="utf-8") as f:
        df = pd.read_csv(f, delimiter="\t")
        print(f"Number of items in file: {df.shape[0]}")

    # Clean and rename columns
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df.rename(columns={"number": "id", "category_name": "category", "year_released": "release_year"}, inplace=True)
    print(f"Cleaned columns: {list(df.columns)}")

    # Filter data by category
    df = df[df["category_id"] == cat_id]
    df.drop(columns=["category_id"], inplace=True)  # Drop unnecessary columns
    print(f"Filtered by category: {df.shape[0]}")

    if type_val == "minifigs":
        df["appears_in"] = ["[]" for _ in range(len(df.index))]
        df["image"] = df.agg(lambda x: f"https://img.bricklink.com/ItemImage/MN/0/{x['id']}.png", axis=1)
        df["bricklink"] = df.agg(lambda x: f"https://www.bricklink.com/v2/catalog/catalogitem.page?M={x['id']}", axis=1)
    elif type_val == "sets":
        df = df[df["id"].str.startswith("7")]  # Filter IDs not starting with 7

        df["minifigs_included"] = ["TBD" for _ in range(len(df.index))]
        df["image"] = df.agg(lambda x: f"https://img.bricklink.com/ItemImage/ON/0/{x['id']}.png", axis=1)
        df["bricklink"] = df.agg(lambda x: f"https://www.bricklink.com/v2/catalog/catalogitem.page?S={x['id']}", axis=1)

    # Transform data
    df["sub_category"] = df.agg(lambda x: ' / '.join(x["category"].split(" / ")[1:]), axis=1)
    df["category"] = df["category"].str.split(" / ").str[0].str.strip()
    df[df["release_year"] == "?"] = np.NaN

    return df


def insert_to_sqlite(table_name: str, df: pd.DataFrame):
    try:
        assert pd.Series(df["id"]).is_unique
        conn = sqlite3.connect('data/lego.db')
        rows_affected = df.to_sql(table_name, conn, if_exists='append', index=False)
        print(f"Data inserted to sqlite: {rows_affected}")
    except AssertionError:
        print("Cannot insert to DB: IDs are not unique")


if __name__ == '__main__':
    """
    Script used to process the downloaded files from BrickLink:
        https://www.bricklink.com/catalogDownload.asp
    
    Input:
        The files need to be downloaded manually and placed in the data/ folder as such 'Sets.txt' and 'Minifigures.txt'
        The files only contain [id, name, category, category_id, year_released]
    
    Result:
        Inserts the data into the sqlite database.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("category", help="category to scrape", type=str)
    parser.add_argument("type", choices=['minifigs', 'sets'], help="type to scrape", type=str)
    args = parser.parse_args()
    print(f"Scraping category: {args.category}")
    print(f"Scraping type: {args.type}")

    category_id = CATEGORY_CONFIG[args.category]["cat_id"]

    data = process_tsv_file(args.type, int(category_id))
    table = TYPE_CONFIG[args.type]["table_name"]
    insert_to_sqlite(table, data)
