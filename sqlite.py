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
                last_scraped_at  TEXT NOT NULL,
                failed_count  INTEGER DEFAULT 0 NOT NULL,
                UNIQUE(id) ON CONFLICT IGNORE
                );"""
    )  # Creates the table
    conn.commit()  # Commits the entries to the database

    conn.execute(
        """CREATE TABLE IF NOT EXISTS notion_mapping
                (page_id              TEXT NOT NULL,
                bl_id             TEXT NOT NULL,
                account_name             TEXT NOT NULL,
                last_updated_at  TEXT NOT NULL,
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
                last_scraped_at  TEXT NOT NULL,
                UNIQUE(id) ON CONFLICT IGNORE
                );"""
    )
    conn.commit()

    conn.execute(
        """CREATE TABLE IF NOT EXISTS minifigs_price_history
                (id              TEXT NOT NULL,
                scraped_at  TEXT NOT NULL,
                avg_price_raw    TEXT NULL,
                avg_price_pln    REAL NULL,
                avg_price_eur    REAL NULL,
                UNIQUE(id, scraped_at) ON CONFLICT IGNORE
                );"""
    )
    conn.commit()

    conn.close()


def upsert_minifig(minifig_dict: dict):
    conn = sqlite3.connect("data/lego.db")
    cursor = conn.cursor()

    df = pd.read_sql_query(
        f"SELECT * FROM minifigs WHERE id = '{minifig_dict['id']}'", conn
    )
    failed_count = 0
    if df.shape[0] == 0:
        # Insert new row
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
        cursor.execute(
            "INSERT INTO minifigs VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'),0)",
            params,
        )
    else:
        # Update existing row
        db_values = df.iloc[0].to_dict()  # update only if the values are not None
        avg_price_raw = (
            f"'{minifig_dict['avg_price_raw']}'"
            if minifig_dict["avg_price_raw"]
            else (
                f"'{db_values['avg_price_raw']}'"
                if db_values["avg_price_raw"]
                else "NULL"
            )
        )
        appears_in = (
            f"'{minifig_dict['appears_in']}'"
            if minifig_dict["appears_in"]
            else (f"'{db_values['appears_in']}'" if db_values["appears_in"] else "NULL")
        )
        failed_count = db_values["failed_count"] + 1 if minifig_dict["failed"] else 0

        cursor.execute(
            f"""UPDATE minifigs 
            SET appears_in={appears_in}, 
            avg_price_raw={avg_price_raw}, 
            avg_price_pln={minifig_dict['avg_price_pln'] or db_values['avg_price_pln'] or "NULL"},
            avg_price_eur={minifig_dict['avg_price_eur'] or db_values['avg_price_eur'] or "NULL"},
            release_year={minifig_dict['release_year'] or db_values['release_year'] or "NULL"},
            last_scraped_at=datetime('now'),
            failed_count={failed_count}
            WHERE id='{minifig_dict['id']}'
            """
        )
    conn.commit()
    print(
        f"Minifig(id={minifig_dict['id']},failed_count={failed_count}) saved to db"  # [{conn.total_changes} change(s)]"
    )
    conn.close()


def should_record_price(current_price: float, previous_price: float) -> bool:
    # Calculate the absolute difference between the current and previous prices
    difference = abs(current_price - previous_price)

    # Determine the threshold based on the previous price
    if previous_price <= 3:
        threshold = 0.75 * previous_price  # 75% change for prices less than 3 EUR
    elif 4 <= previous_price <= 6:
        threshold = 0.50 * previous_price  # 50% change for prices between 4 and 6 EUR
    elif 7 <= previous_price <= 10:
        threshold = 0.40 * previous_price  # 40% change for prices between 7 and 10 EUR
    elif 11 <= previous_price <= 20:
        threshold = 0.20 * previous_price  # 20% change for prices between 11 and 20 EUR
    elif 21 <= previous_price <= 50:
        threshold = 0.10 * previous_price  # 10% change for prices between 21 and 50 EUR
    else:
        # Define additional ranges as needed or handle prices above 50 EUR
        threshold = 0.05 * previous_price  # Example: 5% change for prices above 50 EUR

    # Check if the difference is greater than or equal to the threshold
    print(
        f"{previous_price} -> {current_price} : {'Recorded' if difference >= threshold else 'Not Recorded'}"
    )
    return difference >= threshold


def insert_minifig_price(minifig_dict: dict):
    conn = sqlite3.connect("data/lego.db")
    cursor = conn.cursor()

    df = pd.read_sql_query(
        f"SELECT * FROM minifigs_price_history WHERE id = '{minifig_dict['id']}' ORDER BY scraped_at DESC LIMIT 1",
        conn,
    )

    # Do not record the price if the difference between the last scraped price and the new one is not significant
    if df.shape[0] == 0 or should_record_price(
        minifig_dict["avg_price_eur"], df.loc[0]["avg_price_eur"]
    ):
        # Insert new row
        params = [
            minifig_dict["id"],
            minifig_dict["avg_price_raw"],
            minifig_dict["avg_price_pln"],
            minifig_dict["avg_price_eur"],
        ]
        cursor.execute(
            "INSERT INTO minifigs_price_history VALUES (?,datetime('now'),?,?,?)",
            params,
        )

        conn.commit()
        print(f"MinifigPriceHistory saved to db")
    conn.close()


def insert_set(set_dict: dict):
    conn = sqlite3.connect("data/lego.db")
    cursor = conn.cursor()

    df = pd.read_sql_query(f"SELECT * FROM sets WHERE id = '{set_dict['id']}'", conn)

    if df.shape[0] == 0:
        params = [
            set_dict["id"],
            set_dict["name"],
            set_dict["category"],
            set_dict["sub_category"],
            set_dict["image"],
            set_dict["minifigs_included"],
            set_dict["avg_price_raw"],
            set_dict["avg_price_pln"],
            set_dict["avg_price_eur"],
            set_dict["bricklink"],
            set_dict["release_year"],
        ]
        cursor.execute(
            "INSERT INTO sets VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'))", params
        )
    else:
        db_values = df.iloc[0].to_dict()  # update only if the values are not None
        avg_price_raw = (
            f"'{set_dict['avg_price_raw']}'"
            if set_dict["avg_price_raw"]
            else (
                f"'{db_values['avg_price_raw']}'"
                if db_values["avg_price_raw"]
                else "NULL"
            )
        )
        cursor.execute(
            f"""UPDATE sets 
            SET avg_price_raw={avg_price_raw}, 
            avg_price_pln={set_dict['avg_price_pln'] or db_values['avg_price_pln'] or "NULL"},
            avg_price_eur={set_dict['avg_price_eur'] or db_values['avg_price_eur'] or "NULL"},
            release_year={set_dict['release_year'] or db_values['release_year'] or "NULL"},
            last_scraped_at=datetime('now')
            WHERE id='{set_dict['id']}'
            """
        )
    conn.commit()
    print(f"Set saved to db [{conn.total_changes} change(s)]")
    conn.close()


if __name__ == "__main__":
    """Execute to create the database and table"""
    sql_database()
