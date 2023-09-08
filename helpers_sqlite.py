import pandas as pd
from constants import CATEGORY_MAPPING
import sqlite3
from typing import Optional


def read_minifig_database(category: Optional[str]) -> pd.DataFrame:
    where = f"WHERE category = '{CATEGORY_MAPPING[category]}'" if category else ""

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where}", conn)

    print(f"Read {df.shape[0]} minifigs from database")
    return df


def read_sets_database(category: Optional[str]) -> pd.DataFrame:
    where = f"WHERE category = '{CATEGORY_MAPPING[category]}'" if category else ""

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM sets {where}", conn)

    print(f"Read {df.shape[0]} sets from database")
    return df


def read_minifigs_with_avg_price(category: str) -> list:
    where = f"WHERE category = '{CATEGORY_MAPPING[category]}'" if category else ""
    where = f"{where} AND avg_price_pln IS NOT NULL" if where else "WHERE avg_price_pln IS NOT NULL"

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT id FROM minifigs {where}", conn)
    print(f"Read {df.shape[0]} minifigs from database")
    return df["id"].values


def get_page_id_from_sqlite(bl_id: str) -> Optional[str]:
    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM notion_mapping WHERE bl_id = '{bl_id}'", conn)
    # print(f"Read {df.shape[0]} mapping from database")
    try:
        return str(df["page_id"].values[0])
    except IndexError:
        return None


def get_bl_ids_from_sqlite() -> pd.DataFrame:
    conn = sqlite3.connect("data/lego.db")
    return pd.read_sql_query(f"SELECT bl_id FROM notion_mapping", conn)