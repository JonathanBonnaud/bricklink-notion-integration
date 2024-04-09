import sqlite3
from typing import Optional, Tuple

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


def read_minifigs_where_failed(category: str) -> pd.DataFrame:
    """
    Minifigs that failed to scrape are:
    - figs without Appears In because they are from sets that we don't scrape (magazines, advent calendars, etc.)
    - figs without some values because they are newly added to BL, and we need to wait for BL to update them
    - figs marked for deletion in BL (e.g. sh585 split into sh585a and sh585b)
    """
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )
    condition = "datetime('now') < datetime(last_scraped_at, '+'||POWER(2,failed_count)||' day')"
    where = (  # today < last_scraped_at + timedelta(days=2 ** failed_count)
        f"{where} AND {condition}" if where else f"WHERE {condition}"
    )
    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} minifigs from database (with backoff delay)")
    return df


def read_minifigs_to_scrape(category: str) -> pd.DataFrame:
    """
    Minifigs ordered by last_scraped_at
    """
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )
    order = f"ORDER BY last_scraped_at ASC"
    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where} {order}", conn)
    conn.close()
    print(f"Read {df.shape[0]} minifigs from database (ordered by last_scraped_at ASC)")
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


def read_minifigs_with_filter(
    category: Optional[str], column: str = None
) -> pd.DataFrame:
    where = (
        f"WHERE category = '{CATEGORY_CONFIG[category]['name']}'" if category else ""
    )
    if column:
        where = (
            f"{where} AND {column} IS NOT NULL"
            if where
            else f"WHERE {column} IS NOT NULL"
        )

    conn = sqlite3.connect("data/lego.db")
    df = pd.read_sql_query(f"SELECT * FROM minifigs {where}", conn)
    conn.close()
    print(f"Read {df.shape[0]} minifigs from database (where {column} not null)")
    return df


"""
Read notion_mapping table
"""


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
    row = await async_get_notion_mapping_from_bl_id(bl_id, account_name)
    return row[0]


async def async_get_notion_mapping_from_bl_id(bl_id: str, account_name: str) -> Tuple:
    async with aiosqlite.connect("data/lego.db") as conn:
        async with conn.execute(
            f"SELECT * FROM notion_mapping WHERE bl_id = '{bl_id}' AND account_name = '{account_name}'"
        ) as cursor:
            try:
                (
                    page_id,
                    _bl_id,
                    _account_name,
                    last_updated_at,
                ) = await cursor.fetchone()
                return page_id, _bl_id, _account_name, last_updated_at
            except TypeError:  # no mapping found in table
                return None, None, None, None


async def async_insert_notion_mapping(page_id: str, bl_id: str, account_name: str):
    async with aiosqlite.connect("data/lego.db") as conn:
        await conn.execute(
            "INSERT INTO notion_mapping VALUES (?,?,?,datetime('now'))",
            (page_id, bl_id, account_name),
        )
        await conn.commit()


async def async_update_notion_mapping(page_id: str, bl_id: str, account_name: str):
    async with aiosqlite.connect("data/lego.db") as conn:
        await conn.execute(
            f"""UPDATE notion_mapping SET last_updated_at=datetime('now') 
            WHERE page_id='{page_id}' AND bl_id='{bl_id}' AND account_name='{account_name}'"""
        )
        await conn.commit()


# ONLY used for BL downloaded file processing
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
