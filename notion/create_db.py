import argparse
import os

from notion.helpers_notion import account_setup, read_db_id_from_file
from table_properties import MINIFIG_PRICE_HISTORY_SCHEMA, MINIFIG_SCHEMA, SET_SCHEMA

"""
https://developers.notion.com/reference/create-a-database
"""

DB_CONFIG = {
    "minifigs": {
        "schema": MINIFIG_SCHEMA,
        "name": "Minifigs DB",
        "icon": "https://www.notion.so/icons/database_yellow.svg",
    },
    "sets": {
        "schema": SET_SCHEMA,
        "name": "Sets DB",
        "icon": "https://www.notion.so/icons/database_lightgray.svg",
    },
    "minifigs_price_history": {
        "schema": MINIFIG_PRICE_HISTORY_SCHEMA,
        "name": "Minifigs Price History DB",
        "icon": "https://www.notion.so/icons/database_lightgray.svg",
    },
}

NOTION, PREFIX, PAGE_ID = account_setup()


def write_to_file(db_type: str, db_id: str):
    os.makedirs("notion/files", exist_ok=True)  # Create folder if it doesn't exist
    with open(f"notion/files/{PREFIX}_{db_type}_database_id.txt", "w") as file:
        file.write(db_id)


def create_database(db_type: str):
    data = {
        "parent": {"type": "page_id", "page_id": PAGE_ID},
        "title": [
            {
                "type": "text",
                "text": {"content": DB_CONFIG[db_type]["name"], "link": None},
            }
        ],
        "icon": {"type": "external", "external": {"url": DB_CONFIG[db_type]["icon"]}},
        "properties": DB_CONFIG[db_type]["schema"],
    }
    res = NOTION.databases.create(**data)

    db_id = res["id"]
    print(f"Created database with id: {db_id}")
    write_to_file(db_type, db_id)


def update_dbs_to_add_relations():
    minifig_db_id = read_db_id_from_file(PREFIX, "minifigs")
    sets_db_id = read_db_id_from_file(PREFIX, "sets")
    properties = {
        "Appears In": {
            "name": "Appears In",
            "type": "relation",
            "relation": {
                "database_id": sets_db_id,
                "type": "dual_property",
                "dual_property": {},
            },
        }
    }
    res = NOTION.databases.update(minifig_db_id, properties=properties)
    synced_property_id = res["properties"]["Appears In"]["relation"]["dual_property"][
        "synced_property_id"
    ]
    properties = {synced_property_id: {"name": "Minifigs Included"}}
    _ = NOTION.databases.update(sets_db_id, properties=properties)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "type",
        choices=["minifigs", "sets", "ALL", "minifigs_price_history"],
        help="type to scrape",
        type=str,
    )
    args = parser.parse_args()

    if args.type == "ALL":
        # TODO: create dbs in order: 1.sets 2.minifigs 3.price_history
        for db_type in DB_CONFIG.keys():
            create_database(db_type)
        update_dbs_to_add_relations()
    else:
        create_database(args.type)
