import sqlite3
from typing import Optional

import aiosqlite
import pandas as pd

from constants import CATEGORY_CONFIG


def read_minifig_database(category: Optional[str]) -> pd.DataFrame:
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} minifigs from database")
    return df


def read_sets_database(category: Optional[str]) -> pd.DataFrame:
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM sets {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} sets from database")
    return df


def read_minifigs_with_avg_price(category: str) -> pd.DataFrame:
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )
    where = (
        f"{where} AND avg_price_pln IS NOT NULL"
        if where
        else "WHERE avg_price_pln IS NOT NULL"
    )

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} minifigs from database (where avg_price not null)")
    return df


def read_sets_with_avg_price(category: str) -> pd.DataFrame:
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )
    where = (
        f"{where} AND avg_price_pln IS NOT NULL"
        if where
        else "WHERE avg_price_pln IS NOT NULL"
    )

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM sets {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} sets from database (where avg_price not null)")
    return df


def read_sets_with_release_year(category: str) -> pd.DataFrame:
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )
    where = (
        f"{where} AND release_year IS NOT NULL"
        if where
        else "WHERE release_year IS NOT NULL"
    )

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM sets {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} sets from database (where release_year not null)")
    return df


def read_minifigs_with_appears_in(category: str) -> pd.DataFrame:
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )
    where = (
        f"{where} AND appears_in IS NOT NULL"
        if where
        else "WHERE appears_in IS NOT NULL"
    )

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} minifigs from database (where appears_in not null)")
    return df


"""
Read notion_mapping table
"""


def get_page_id_from_sqlite(bl_id: str, account_name: str) -> Optional[str]:
    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(
        f"SELECT * FROM notion_mapping WHERE bl_id = '{bl_id}' AND account_name = '{account_name}'",
        conn,
    )
    conn.close()
    # print(f"Read {df.shape[0]} mapping from database")
    try:
        return str(df["page_id"].values[0])
    except IndexError:
        return None


def get_bl_ids_from_sqlite(account_name: str) -> pd.DataFrame:
    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(
        f"SELECT bl_id FROM notion_mapping WHERE account_name = '{account_name}'", conn
    )
    conn.close()
    return df


"""
Async methods
"""


async def async_get_page_id_from_sqlite(bl_id: str, account_name: str) -> Optional[str]:
    async with aiosqlite.connect("data/lego.db") as conn:
        async with conn.execute(
            f"SELECT * FROM notion_mapping WHERE bl_id = '{bl_id}' AND account_name = '{account_name}'"
        ) as cursor:
            try:
                rows = await cursor.fetchone()
                return str(rows[0])
            except (TypeError, IndexError):
                return None


async def async_insert_notion_mapping(page_id: str, bl_id: str, account_name: str):
    async with aiosqlite.connect("data/lego.db") as conn:
        await conn.execute(
            "INSERT INTO notion_mapping VALUES (?,?,?)", (page_id, bl_id, account_name)
        )
        await conn.commit()


def insert_to_sqlite(table_name: str, df: pd.DataFrame):
    try:
        assert pd.Series(df["id"]).is_unique
        conn = sqlite3.connect("data/lego.db")
        rows_affected = df.to_sql(table_name, conn, if_exists="append", index=False)
        print(f"Data inserted to sqlite: {rows_affected}")
        conn.close()
    except AssertionError:
        print("Cannot insert to DB: IDs are not unique")


def write_to_sql(table_name: str, data: dict) -> int:
    df = pd.DataFrame(data)
    conn = sqlite3.connect("data/lego.db")
    rows_affected = df.to_sql(table_name, conn, if_exists="append", index=False)
    # print(f"Data inserted to sqlite: {rows_affected}")
    conn.close()
    return rows_affected
