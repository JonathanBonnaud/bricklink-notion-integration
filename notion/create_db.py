import argparse

from notion.private_secrets import NOTION_LEGO_COLLECTION_SECRET, PAGE_ID, NOTION_JONATHAN_SECRET
from table_properties import MINIFIG_SCHEMA, SET_SCHEMA
from notion_client import Client

DB_CONFIG = {
    "minifigs": {
        "schema": MINIFIG_SCHEMA,
        "name": "Minifigs DB",
        "icon": 'https://www.notion.so/icons/database_yellow.svg',
    },
    "sets": {
        "schema": SET_SCHEMA,
        "name": "Sets DB",
        "icon": 'https://www.notion.so/icons/database_lightgray.svg',
    }
}

client = Client(auth=NOTION_JONATHAN_SECRET)


def write_to_file(db_type: str, db_id: str):
    with open(f"notion/{db_type}_database_id.txt", "w") as file:
        file.write(db_id)


def read_db_id_from_file(db_type: str) -> str:
    with open(f"notion/{db_type}_database_id.txt", "r") as file:
        return str(file.read())


def create_database(db_type: str):
    data = {
        "parent": {"type": "page_id", "page_id": PAGE_ID},
        "title": [{"type": "text", "text": {"content": DB_CONFIG[db_type]["name"], "link": None}}],
        'icon': {'type': 'external', 'external': {'url': DB_CONFIG[db_type]["icon"]}},
        "properties": DB_CONFIG[db_type]["schema"],
    }
    res = client.databases.create(**data)

    db_id = res["id"]
    print(f"Created database with id: {db_id}")
    write_to_file(db_type, db_id)


def update_dbs_to_add_relations():
    minifig_db_id = read_db_id_from_file("minifigs")
    sets_db_id = read_db_id_from_file("sets")
    properties = {
        "Appears In": {"name": "Appears In", "type": "relation",
             "relation": {"database_id": sets_db_id,
                          "type": "dual_property",
                          "dual_property": {}}}
    }
    res = client.databases.update(minifig_db_id, properties=properties)
    synced_property_id = res["properties"]["Appears In"]["relation"]["dual_property"]["synced_property_id"]
    properties = {
        synced_property_id: {"name": "Minifigs Included"}
    }
    _ = client.databases.update(sets_db_id, properties=properties)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("type", choices=['minifigs', 'sets', 'ALL'], help="type to scrape", type=str)
    args = parser.parse_args()

    if args.type == "ALL":
        for db_type in DB_CONFIG.keys():
            create_database(db_type)
        update_dbs_to_add_relations()
    else:
        create_database(args.type)


