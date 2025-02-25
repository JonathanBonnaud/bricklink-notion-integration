import argparse
import asyncio
import time

import pandas as pd
from notion_client import APIErrorCode, APIResponseError
from notion_client.errors import HTTPResponseError
from tqdm import tqdm
from tqdm.asyncio import tqdm

from helpers_sqlite import (
    async_get_notion_mapping_from_bl_id,
    async_insert_notion_mapping,
    async_update_notion_mapping,
    get_bl_ids_from_sqlite,
    read_sets_database,
)
from notion.helpers_notion import async_account_setup, read_db_id_from_file

NOTION, PREFIX, _ = async_account_setup()

SEM = asyncio.Semaphore(20)


async def notion_update(row_id: str, page_id: str, data: dict):
    # print(f"Updating page for '{row_id}'...")
    await NOTION.pages.update(page_id=page_id, **data)
    # print(f"Updated page for {row_id}")


async def upsert_set_page(row: pd.Series, db_id: str):
    async with SEM:
        data = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {"rich_text": [{"text": {"content": row["name"]}}]},
                "Id": {"title": [{"text": {"content": row["id"]}}]},
                "Category": {"select": {"name": row["category"]}},
                "Sub Category": {
                    "rich_text": [{"text": {"content": row["sub_category"] or ""}}]
                },
                "Image": {
                    "files": [{"name": row["image"], "external": {"url": row["image"]}}]
                },
                "BrickLink": {"url": row["bricklink"]},
                "Avg price raw": {
                    "rich_text": [{"text": {"content": row["avg_price_raw"] or ""}}]
                },
                "Avg price PLN": {
                    "number": (
                        row["avg_price_pln"]
                        if not pd.isnull(row["avg_price_pln"])
                        else None
                    )
                },
                "Avg price EUR": {
                    "number": (
                        row["avg_price_eur"]
                        if not pd.isnull(row["avg_price_eur"])
                        else None
                    )
                },
                "Release Year": {
                    "number": (
                        row["release_year"]
                        if not pd.isnull(row["release_year"])
                        else None
                    )
                },
                # # /!\ Need to be excluded not to update 'Minifigs Included' with empty values /!\
                # "Minifigs Included": {
                #     "relation": [
                #         # {
                #         #     "id": ""
                #         # }
                #     ],
                # },
            },
        }

        page_id, _, _, last_updated_at = await async_get_notion_mapping_from_bl_id(
            row["id"], PREFIX
        )
        if last_updated_at is not None and last_updated_at > row["last_scraped_at"]:
            return 0  # SKIPPED

        try:
            page = await NOTION.pages.retrieve(page_id)
            await notion_update(row["id"], page["id"], data)
            await async_update_notion_mapping(page["id"], row["id"], PREFIX)
            return 1  # UPDATED
        except APIResponseError as e:
            if e.code == APIErrorCode.RateLimited:
                print("Rate limited, sleeping for 5 minutes...")
                await asyncio.sleep(60 * 5)
            elif e.code == APIErrorCode.ValidationError:  # Page not found
                try:
                    page_created = await NOTION.pages.create(database_id=db_id, **data)
                    await asyncio.sleep(0)
                    await async_insert_notion_mapping(
                        page_created["id"], row["id"], PREFIX
                    )
                    print(f"Created page for {row['id']}")
                    return 2  # INSERTED
                except Exception as e:
                    print(f"Error creating page for {row['id']}\n\t{e}")
                    return 3
            else:
                print(f"Uncaught Error: {e}")
                raise e
        except HTTPResponseError:
            return 3


async def main(df: pd.DataFrame, db_id: str):
    tasks = [
        asyncio.ensure_future(
            upsert_set_page(df_row, db_id)
        )  # creating task starts coroutine
        for _, df_row in df.iterrows()
    ]
    res = await tqdm.gather(*tasks)  # asyncio.gather
    print(
        f"{sum([1 for a in res if a == 1])} updated, "
        f"{sum([1 for a in res if a == 2])} inserted, "
        f"{sum([1 for a in res if a == 0])} skipped, "
        f"{sum([1 for a in res if a == 3])} failed"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category", help="category of sets to send", type=str  # nargs="?"
    )
    parser.add_argument(
        "--insert", help="Only execute inserts of new", action="store_true"
    )
    args = parser.parse_args()
    category = args.category
    print(f"Sending sets for category: {category or 'all'}")

    if args.insert:
        bl_ids_df = get_bl_ids_from_sqlite(PREFIX)
        sets_df = read_sets_database(category)
        df = sets_df[~sets_df["id"].isin(bl_ids_df["bl_id"])]
    else:
        df = read_sets_database(category)

    print(f"Number of sets to process: {df.shape[0]}")
    # Insert most recent first
    df = df.sort_values(by=["release_year", "id"], ascending=False)

    db_id = read_db_id_from_file(PREFIX, "sets")

    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(df, db_id))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    end = time.time()
    print(f"Time elapsed: {round(end - start, 2)}s")
