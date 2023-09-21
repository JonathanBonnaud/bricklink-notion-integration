import argparse

import numpy as np
import pandas as pd
from notion_client import APIResponseError, APIErrorCode
from tqdm.asyncio import tqdm
import asyncio
import time

from helpers_sqlite import (
    read_minifig_database,
    get_bl_ids_from_sqlite,
    read_minifigs_with_appears_in,
    read_minifigs_with_avg_price,
    async_get_page_id_from_sqlite,
    async_insert_notion_mapping,
    async_get_notion_mapping_from_bl_id,
    async_update_notion_mapping,
)
from notion.helpers_notion import async_account_setup, read_owned

NOTION, PREFIX, _ = async_account_setup()

SEM = asyncio.Semaphore(20)


def read_db_id_from_file() -> str:
    with open(f"notion/files/{PREFIX}_minifigs_database_id.txt", "r") as file:
        return str(file.read())


async def get_relations(appears_in: str) -> list:
    relations = []
    try:
        for set_id in appears_in.split(","):
            if page_id := await async_get_page_id_from_sqlite(set_id, PREFIX):
                relations.append({"id": page_id})
    except AttributeError:  # appears_in is None
        pass
    return relations


async def notion_update(row_id: str, page_id: str, data: dict):
    # print(f"Updating page for '{row_id}'...")
    await NOTION.pages.update(page_id=page_id, **data)
    # print(f"Updated page for {row_id}")


async def upsert_minifig_page(row: pd.Series, db_id: str):
    async with SEM:  # semaphore limits num of simultaneous calls
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
                    "number": row["avg_price_pln"]
                    if not np.isnan(row["avg_price_pln"])
                    else None
                },
                "Avg price EUR": {
                    "number": row["avg_price_eur"]
                    if not np.isnan(row["avg_price_eur"])
                    else None
                },
                "Release Year": {
                    "number": row["release_year"]
                    if not np.isnan(row["release_year"])
                    else None
                },
                "Appears In": {"relation": await get_relations(row["appears_in"])},
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
                page_created = await NOTION.pages.create(database_id=db_id, **data)
                await async_insert_notion_mapping(page_created["id"], row["id"], PREFIX)
                print(f"Created page for {row['id']}")
                return 2  # INSERTED
            else:
                raise e


async def main(df: pd.DataFrame, db_id: str):
    tasks = [
        asyncio.ensure_future(
            upsert_minifig_page(df_row, db_id)
        )  # creating task starts coroutine
        for _, df_row in df.iterrows()
    ]
    res = await tqdm.gather(*tasks)  # asyncio.gather
    print(
        f"{sum([1 for a in res if a == 1])} updated, {sum([1 for a in res if a == 2])} inserted, {sum([1 for a in res if a == 0])} skipped"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category", help="category of minifigs to send", type=str  # nargs="?",
    )
    parser.add_argument(
        "--insert", help="Only execute inserts of new", action="store_true"
    )
    parser.add_argument(
        "--update-collec", help="Only execute update of owned", action="store_true"
    )
    parser.add_argument(
        "--update", help="Only execute update of existing", action="store_true"
    )
    parser.add_argument(
        "--avg-price", help="Focus on getting missing avg_price", action="store_true"
    )
    parser.add_argument(
        "--appears-in", help="Focus on getting missing appears_in", action="store_true"
    )
    args = parser.parse_args()
    category = args.category
    print(f"Sending minifigs for category: {category or 'all'}")

    if args.insert:
        bl_ids_df = get_bl_ids_from_sqlite(PREFIX)
        minifig_df = read_minifig_database(category)
        df = minifig_df[~minifig_df["id"].isin(bl_ids_df["bl_id"])]
    elif args.update_collec:
        bl_ids = read_owned("minifigs", category)
        minifig_df = read_minifig_database(category)
        df = minifig_df[minifig_df["id"].isin(bl_ids)]
    elif args.update:
        bl_ids_df = get_bl_ids_from_sqlite(PREFIX)
        if args.avg_price:
            minifig_df = read_minifigs_with_avg_price(category)
        elif args.appears_in:
            minifig_df = read_minifigs_with_appears_in(category)
        else:
            minifig_df = read_minifig_database(category)
        df = minifig_df[minifig_df["id"].isin(bl_ids_df["bl_id"])]
    else:
        df = read_minifig_database(category)

    print(f"Number of minifigs to process: {df.shape[0]}")
    # Insert most recent first
    df = df.sort_values(by=["release_year", "id"], ascending=False)

    db_id = read_db_id_from_file()

    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(df, db_id))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    end = time.time()
    print(f"Time elapsed: {round(end - start, 2)}s")
