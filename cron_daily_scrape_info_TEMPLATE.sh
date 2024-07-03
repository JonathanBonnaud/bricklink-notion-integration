#!/bin/bash

TIMESTAMP=$(date +%F_%T)
echo $TIMESTAMP

source venv/bin/activate
export PYTHONPATH=$PYTHONPATH

for cat in sw sh hp ; do  # avt hfw col poc mof lor
    echo $cat
    python scraping/scrape_BL_minifig_info.py $cat >>"./cronlogs/scrape_BL_info_${TIMESTAMP}_std.log" 2>&1

    # upsert to Notion
    python notion/async_upsert_minifigs_data.py $cat >>"./cronlogs/upsert_to_notion_${TIMESTAMP}_std.log" 2>&1
    python notion/async_upsert_minifigs_price_history_data.py $cat >>"./cronlogs/upsert_to_notion_${TIMESTAMP}_std.log" 2>&1

    echo "Waiting 15 minutes..."
    sleep 900
done
echo "Done!"
deactivate