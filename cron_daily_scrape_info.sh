#!/bin/bash

TIMESTAMP=$(date +%F_%T)
echo $TIMESTAMP

source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:/Users/$USERNAME/PycharmProjects/bricklink-notion-integration

for cat in sw sh; do
    echo $cat
    python scraping/scrape_BL_minifig_info.py $cat >>"/Users/${USER}/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_info_${TIMESTAMP}_std.log" 2>&1

    # upsert to Notion
    python notion/async_upsert_minifigs_data.py $cat >>"/Users/${USER}/PycharmProjects/bricklink-notion-integration/cronlogs/upsert_to_notion_${TIMESTAMP}_std.log" 2>&1

    echo "Waiting 20 minutes..."
    sleep 1200
done
echo "Done"
deactivate