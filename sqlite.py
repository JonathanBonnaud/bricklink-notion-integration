import sqlite3


def sql_database():
    conn = sqlite3.connect('data/lego.db')  # Opens Connection to SQLite database file.
    conn.execute("""CREATE TABLE minifigs
                (id              TEXT NOT NULL,
                name             TEXT NOT NULL,
                category         TEXT NOT NULL,
                sub_category     TEXT,
                image            TEXT NOT NULL,
                appears_in       BLOB NOT NULL,
                avg_price_raw    TEXT NULL,
                avg_price_pln    REAL NULL,
                bricklink        TEXT NOT NULL,
                release_year     INTEGER NULL,
                UNIQUE(id) ON CONFLICT IGNORE
                );""")  # Creates the table
    conn.commit()  # Commits the entries to the database
    conn.close()


def insert_minifig(minifig_dict: dict):
    conn = sqlite3.connect('data/lego.db')
    cursor = conn.cursor()
    params = [
        minifig_dict['id'],
        minifig_dict['name'],
        minifig_dict['category'],
        minifig_dict['sub_category'],
        minifig_dict['image'],
        minifig_dict['appears_in'],
        minifig_dict['avg_price_raw'],
        minifig_dict['avg_price_pln'],
        minifig_dict['bricklink'],
        minifig_dict['release_year']
    ]
    cursor.execute("INSERT INTO minifigs VALUES (?,?,?,?,?,?,?,?,?,?)", params)
    conn.commit()
    print('Minifig saved to db')
    conn.close()


if __name__ == '__main__':
    """Execute to create the database and table"""
    sql_database()
