import json

import requests

from notion.private_secrets import NOTION_LEGO_COLLECTION_SECRET, PAGE_ID, NOTION_JONATHAN_SECRET
from table_properties import MINIFIG_MINIMAL_SCHEMA

HEADERS = {
    # "Authorization": f"Bearer {NOTION_LEGO_COLLECTION_SECRET}",
    "Authorization": f"Bearer {NOTION_JONATHAN_SECRET}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def write_to_file(db_id: str):
    with open(f"notion/database_id.txt", "w") as file:
        file.write(db_id)


def create_minifig_database():
    data = {
        "parent": {"type": "page_id", "page_id": PAGE_ID},
        "title": [{"type": "text", "text": {"content": "Minifigs DB", "link": None}}],
        "properties": MINIFIG_MINIMAL_SCHEMA,
    }

    res = requests.post(
        "https://api.notion.com/v1/databases/", data=json.dumps(data), headers=HEADERS
    )
    # print(json.dumps(res.json(), sort_keys=True, indent=4))

    db_id = res.json()["id"]
    print(f"Created database with id: {db_id}")
    write_to_file(db_id)


if __name__ == "__main__":
    create_minifig_database()
