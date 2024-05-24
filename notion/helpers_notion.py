import os

from notion_client import Client, AsyncClient
from notion_client.helpers import collect_paginated_api
from notion.private_secrets import (
    NOTION_USER_SECRET,
    NOTION_SECOND_USER_SECRET,
    PAGE_ID,
    SECOND_USER_PAGE_ID,
    NOTION_SHARED_WORKSPACE_SECRET,
    SHARED_WORKSPACE_PAGE_ID,
    DEFAULT_USER_PREFIX,
    SECOND_USER_PREFIX,
    SECOND_USER_ACCOUNT,
    SHARED_WORKSPACE_PREFIX,
    SHARED_WORKSPACE_ACCOUNT,
)
from constants import CATEGORY_CONFIG


def account_setup():
    if os.environ.get("ACCOUNT") == SECOND_USER_ACCOUNT:
        name = SECOND_USER_ACCOUNT
        client = Client(auth=NOTION_SECOND_USER_SECRET)
        prefix = SECOND_USER_PREFIX
        page_id = SECOND_USER_PAGE_ID
    elif os.environ.get("ACCOUNT") == SHARED_WORKSPACE_ACCOUNT:
        name = SHARED_WORKSPACE_ACCOUNT
        client = Client(auth=NOTION_SHARED_WORKSPACE_SECRET)
        prefix = SHARED_WORKSPACE_PREFIX
        page_id = SHARED_WORKSPACE_PAGE_ID
    else:
        client = Client(auth=NOTION_USER_SECRET)
        prefix = name = DEFAULT_USER_PREFIX
        page_id = PAGE_ID
    print(f"Connected to {name}'s Notion\n======================")

    return client, prefix, page_id


def async_account_setup():
    if os.environ.get("ACCOUNT") == SECOND_USER_ACCOUNT:
        name = SECOND_USER_ACCOUNT
        client = AsyncClient(auth=NOTION_SECOND_USER_SECRET)
        prefix = SECOND_USER_PREFIX
        page_id = SECOND_USER_PAGE_ID
    elif os.environ.get("ACCOUNT") == SHARED_WORKSPACE_ACCOUNT:
        name = SHARED_WORKSPACE_ACCOUNT
        client = AsyncClient(auth=NOTION_SHARED_WORKSPACE_SECRET)
        prefix = SHARED_WORKSPACE_PREFIX
        page_id = SHARED_WORKSPACE_PAGE_ID
    else:
        client = AsyncClient(auth=NOTION_USER_SECRET)
        prefix = name = DEFAULT_USER_PREFIX
        page_id = PAGE_ID
    print(f"[async] Connected to {name}'s Notion\n======================")

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


def read_minifig_price_history_db(db_type: str, client: Client = None, prefix=None):
    if client is None and prefix is None:
        client, prefix, _ = account_setup()

    all_results = collect_paginated_api(
        client.databases.query,
        database_id=read_db_id_from_file(prefix, db_type),
    )
    print(f"Minifig Price History notion DB: {len(all_results)}")
    return [
        (
            result["properties"]["Id"]["title"][0]["plain_text"],
            result["properties"]["Scraped At"]["date"]["start"],
        )
        for result in all_results
    ]
