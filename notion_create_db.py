import json

import requests

from constants import NOTION_LEGO_COLLECTION_SECRET, PAGE_ID
from table_properties import MINIFIG_MINIMAL_SCHEMA

HEADERS = {
    "Authorization": f"Bearer {NOTION_LEGO_COLLECTION_SECRET}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


def create_minifig_database():
    data = {
        "parent": {"type": "page_id", "page_id": PAGE_ID},
        "title": [{"type": "text", "text": {"content": "Minifigs", "link": None}}],
        "properties": MINIFIG_MINIMAL_SCHEMA,
    }

    res = requests.post(
        "https://api.notion.com/v1/databases/", data=json.dumps(data), headers=HEADERS
    )
    print(json.dumps(res.json(), sort_keys=True, indent=4))


if __name__ == "__main__":
    create_minifig_database()
