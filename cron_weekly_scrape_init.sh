#!/bin/bash

TIMESTAMP=$(date +%F_%T)
echo $TIMESTAMP

source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:/Users/$USER/PycharmProjects/bricklink-notion-integration

type="sets"
echo $type":"
for cat in sw sh idea hp crea; do  # avt hfw col
    echo $cat
    python scraping/scrape_BL_init.py $cat $type >>"/Users/${USER}/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_init_${TIMESTAMP}_std.log" 2>&1
    python scraping/scrape_BL_set_info.py $cat --scrape-only-release-year >>"/Users/${USER}/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_info_${TIMESTAMP}_std.log" 2>&1

    # upsert to Notion
    python notion/async_upsert_sets_data.py $cat >>"/Users/${USER}/PycharmProjects/bricklink-notion-integration/cronlogs/upsert_to_notion_${TIMESTAMP}_std.log" 2>&1
done

type="minifigs"
echo $type":"
for cat in sw sh idea hp; do  # avt hfw col
    echo $cat
    python scraping/scrape_BL_init.py $cat $type >>"/Users/${USER}/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_init_${TIMESTAMP}_std.log" 2>&1
done
echo "Done!"
deactivate
