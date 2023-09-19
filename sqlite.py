import sqlite3

import pandas as pd

"""
SQLite documentation: https://docs.python.org/3/library/sqlite3.html

https://www.sqlite.org/draft/lang_UPSERT.html
"""


def sql_database():
    conn = sqlite3.connect("data/lego.db")  # Opens Connection to SQLite database file.
    conn.execute(
        """CREATE TABLE IF NOT EXISTS minifigs
                (id              TEXT NOT NULL,
                name             TEXT NOT NULL,
                category         TEXT NOT NULL,
                sub_category     TEXT NULL,
                image            TEXT NOT NULL,
                appears_in       BLOB NULL,
                avg_price_raw    TEXT NULL,
                avg_price_pln    REAL NULL,
                avg_price_eur    REAL NULL,
                bricklink        TEXT NOT NULL,
                release_year     INTEGER NULL,
                UNIQUE(id) ON CONFLICT IGNORE
                );"""
    )  # Creates the table
    conn.commit()  # Commits the entries to the database

    conn.execute(
        """CREATE TABLE IF NOT EXISTS notion_mapping
                (page_id              TEXT NOT NULL,
                bl_id             TEXT NOT NULL,
                account_name             TEXT NOT NULL,
                UNIQUE(page_id, bl_id) ON CONFLICT IGNORE
                );"""
    )
    conn.commit()

    conn.execute(
        """CREATE TABLE IF NOT EXISTS sets
                (id              TEXT NOT NULL,
                name             TEXT NOT NULL,
                category         TEXT NOT NULL,
                sub_category     TEXT,
                image            TEXT NOT NULL,
                minifigs_included       BLOB NULL,
                avg_price_raw    TEXT NULL,
                avg_price_pln    REAL NULL,
                avg_price_eur    REAL NULL,
                bricklink        TEXT NOT NULL,
                release_year     INTEGER NULL,
                UNIQUE(id) ON CONFLICT IGNORE
                );"""
    )
    conn.commit()

    conn.close()


def insert_minifig(minifig_dict: dict):
    conn = sqlite3.connect("data/lego.db")
    cursor = conn.cursor()
    params = [
        minifig_dict["id"],
        minifig_dict["name"],
        minifig_dict["category"],
        minifig_dict["sub_category"],
        minifig_dict["image"],
        minifig_dict["appears_in"],
        minifig_dict["avg_price_raw"],
        minifig_dict["avg_price_pln"],
        minifig_dict["avg_price_eur"],
        minifig_dict["bricklink"],
        minifig_dict["release_year"],
    ]

    df = pd.read_sql_query(
        f"SELECT * FROM minifigs WHERE id = '{minifig_dict['id']}'", conn
    )

    if df.shape[0] == 0:
        cursor.execute("INSERT INTO minifigs VALUES (?,?,?,?,?,?,?,?,?,?,?)", params)
    else:
        db_values = df.iloc[0].to_dict()  # update only if the values are not None
        avg_price_raw = (
            f"'{minifig_dict['avg_price_raw']}'"
            if minifig_dict["avg_price_raw"]
            else f"'{db_values['avg_price_raw']}'"
        )
        appears_in = (
            f"'{minifig_dict['appears_in']}'"
            if minifig_dict["appears_in"]
            else f"'{db_values['appears_in']}'"
        )
        cursor.execute(
            f"""UPDATE minifigs 
            SET appears_in={appears_in}, 
            avg_price_raw={avg_price_raw}, 
            avg_price_pln={minifig_dict['avg_price_pln'] or db_values['avg_price_pln'] or "NULL"},
            avg_price_eur={minifig_dict['avg_price_eur'] or db_values['avg_price_eur'] or "NULL"},
            release_year={minifig_dict['release_year'] or db_values['release_year'] or "NULL"}
            WHERE id='{minifig_dict['id']}'
            """
        )
    conn.commit()
    print("Minifig saved to db")
    conn.close()


def insert_notion_mapping(page_id: str, bl_id: str, account_name: str):
    conn = sqlite3.connect("data/lego.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notion_mapping VALUES (?,?,?)", (page_id, bl_id, account_name)
    )
    conn.commit()
    changes = conn.total_changes
    conn.close()
    return changes


if __name__ == "__main__":
    """Execute to create the database and table"""
    sql_database()
