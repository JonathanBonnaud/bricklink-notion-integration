import argparse
import asyncio
import time
from uuid import NAMESPACE_DNS, uuid5

import pandas as pd
from notion_client.errors import HTTPResponseError
from tqdm.asyncio import tqdm

from helpers_sqlite import (
    async_get_page_id_from_sqlite,
    read_minifigs_price_history_database,
)
from notion.helpers_notion import (
    async_account_setup,
    read_db_id_from_file,
    read_minifig_price_history_db,
)

NOTION, PREFIX, _ = async_account_setup()

SEM = asyncio.Semaphore(15)


async def get_relations(bl_id: str) -> list:
    relations = []
    try:
        if page_id := await async_get_page_id_from_sqlite(bl_id, PREFIX):
            relations.append({"id": page_id})
    except AttributeError:
        pass
    return relations


async def upsert_minifig_price_history_page(row: pd.Series, db_id: str):
    async with SEM:  # semaphore limits num of simultaneous calls
        data = {
            "parent": {"database_id": db_id},
            "properties": {
                "Id": {"title": [{"text": {"content": row["id"]}}]},
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
                "Scraped At": {"date": {"start": row["scraped_at"]}},
                "Minifig": {"relation": await get_relations(row["id"])},
            },
        }

        try:
            _ = await NOTION.pages.create(database_id=db_id, **data)
            print(f"Created page for {row['id']}")
            return 2  # INSERTED
        except HTTPResponseError as e:
            print(e)
            return 3


async def main(df: pd.DataFrame, db_id: str):
    tasks = [
        asyncio.ensure_future(
            upsert_minifig_price_history_page(df_row, db_id)
        )  # creating task starts coroutine
        for _, df_row in df.iterrows()
    ]
    res = await tqdm.gather(*tasks)  # asyncio.gather
    print(
        f"{sum([1 for a in res if a == 2])} inserted, "
        f"{sum([1 for a in res if a == 3])} failed"
    )


def filter_existing(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    df2["marker"] = 1

    # join the two, keeping all of df1's indices
    joined = pd.merge(df1, df2[["uuid", "marker"]], on=["uuid"], how="left")
    filtered_df = joined[pd.isnull(joined["marker"])][df1.columns]

    return filtered_df


def custom_uuid(data):
    val = uuid5(NAMESPACE_DNS, data)
    return val


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "category", help="category of minifigs to send", type=str  # nargs="?",
    )
    args = parser.parse_args()
    category = args.category

    print("Reading DB...")
    df = read_minifigs_price_history_database(category)
    df["scraped_at"] = pd.to_datetime(
        df["scraped_at"].str[:-3], format="%Y-%m-%d %H:%M"
    ).astype(str)
    db_df = df.assign(uuid=(df.id + "_" + df.scraped_at).apply(custom_uuid))

    existing_rows = read_minifig_price_history_db("minifigs_price_history")
    notion_df = pd.DataFrame(existing_rows, columns=["id", "scraped_at"])
    notion_df["scraped_at"] = pd.to_datetime(
        notion_df["scraped_at"].str.split(".").str[0].str[:-3], format="%Y-%m-%dT%H:%M"
    ).astype(str)
    notion_df = notion_df.assign(
        uuid=(notion_df.id + "_" + notion_df.scraped_at).apply(custom_uuid)
    )

    filter_df = filter_existing(db_df, notion_df)

    print(f"Number of minifigs price history to process: {filter_df.shape[0]}")

    db_id = read_db_id_from_file(PREFIX, "minifigs_price_history")

    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(filter_df, db_id))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
    end = time.time()
    print(f"Time elapsed for insert: {round(end - start, 2)}s")
