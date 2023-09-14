import os
from notion_client import Client, AsyncClient
from notion.private_secrets import (
    NOTION_JONATHAN_SECRET,
    NOTION_VICTO_SECRET,
    PAGE_ID,
    VICTO_PAGE_ID,
)


def account_setup():
    if os.environ.get("ACCOUNT") == "VICTO":
        print("Connected to Victo's Notion\n======================")
        client = Client(auth=NOTION_VICTO_SECRET)
        prefix = "VI"
        page_id = VICTO_PAGE_ID
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
    else:
        print("[async] Connected to Jo's Notion\n======================")
        client = AsyncClient(auth=NOTION_JONATHAN_SECRET)
        prefix = "JO"
        page_id = PAGE_ID

    return client, prefix, page_id
