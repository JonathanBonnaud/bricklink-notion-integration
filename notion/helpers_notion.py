import os

from notion_client import Client, AsyncClient
from notion_client.helpers import collect_paginated_api
from notion.private_secrets import (
    NOTION_JONATHAN_SECRET,
    NOTION_VICTO_SECRET,
    PAGE_ID,
    VICTO_PAGE_ID,
    NOTION_LEGO_COLLECTION_SECRET,
    LEGO_COLLEC_PAGE_ID,
)
from constants import CATEGORY_CONFIG


def account_setup():
    if os.environ.get("ACCOUNT") == "VICTO":
        print("Connected to Victo's Notion\n======================")
        client = Client(auth=NOTION_VICTO_SECRET)
        prefix = "VI"
        page_id = VICTO_PAGE_ID
    elif os.environ.get("ACCOUNT") == "LEGO_COLLEC":
        print("Connected to Lego Collection's Notion\n======================")
        client = Client(auth=NOTION_LEGO_COLLECTION_SECRET)
        prefix = "LEGO"
        page_id = LEGO_COLLEC_PAGE_ID
    else:
        print("Connected to Jo's Notion\n======================")
        client = Client(auth=NOTION_JONATHAN_SECRET)
        prefix = "JO"
        page_id = PAGE_ID

    return client, prefix, page_id


def async_account_setup():
    if os.environ.get("ACCOUNT") == "VICTO":
        print("[async] Connected to Victo's Notion\n======================")
        client = AsyncClient(auth=NOTION_VICTO_SECRET)
        prefix = "VI"
        page_id = VICTO_PAGE_ID
    elif os.environ.get("ACCOUNT") == "LEGO_COLLEC":
        print("Connected to Lego Collection's Notion\n======================")
        client = AsyncClient(auth=NOTION_LEGO_COLLECTION_SECRET)
        prefix = "LEGO"
        page_id = LEGO_COLLEC_PAGE_ID
    else:
        print("[async] Connected to Jo's Notion\n======================")
        client = AsyncClient(auth=NOTION_JONATHAN_SECRET)
        prefix = "JO"
        page_id = PAGE_ID

    return client, prefix, page_id


def read_db_id_from_file(account_prefix: str, db_type: str) -> str:
    with open(f"notion/files/{account_prefix}_{db_type}_database_id.txt", "r") as file:
        return str(file.read())


def read_owned(db_type: str, category: str = None, client: Client = None, prefix=None):
    if client is None and prefix is None:
        client, prefix, _ = account_setup()

    cat = CATEGORY_CONFIG[category]["name"] if category is not None else None
    filters = (
        {
            "and": [
                {"property": "Category", "select": {"equals": cat}},
                {"property": "owned", "checkbox": {"equals": True}},
            ]
        }
        if cat is not None
        else {"property": "owned", "checkbox": {"equals": True}}
    )

    all_results = collect_paginated_api(
        client.databases.query,
        database_id=read_db_id_from_file(prefix, db_type),
        filter=filters,
    )
    print(f"You own {len(all_results)} {db_type} from {cat} category")
    return [
        result["properties"]["Id"]["title"][0]["plain_text"] for result in all_results
    ]


def read_wanted(db_type: str, category: str = None, client: Client = None, prefix=None):
    if client is None and prefix is None:
        client, prefix, _ = account_setup()

    cat = CATEGORY_CONFIG[category]["name"] if category is not None else None
    filters = (
        {
            "and": [
                {"property": "Category", "select": {"equals": cat}},
                {"property": "Wanted", "checkbox": {"equals": True}},
            ]
        }
        if cat is not None
        else {"property": "Wanted", "checkbox": {"equals": True}}
    )

    all_results = collect_paginated_api(
        client.databases.query,
        database_id=read_db_id_from_file(prefix, db_type),
        filter=filters,
    )
    print(f"You want {len(all_results)} {db_type} from {cat} category")
    return [
        result["properties"]["Id"]["title"][0]["plain_text"] for result in all_results
    ]
