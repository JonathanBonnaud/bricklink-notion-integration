#!/bin/bash

TIMESTAMP=$(date +%F_%T)
echo $TIMESTAMP

source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration

type="sets"
echo $type
for cat in sw sh; do  # avt hp hfw col
    echo $cat
    python scraping/scrape_BL_init.py $cat $type >>"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_init_${TIMESTAMP}_std.log" 2>&1
    python scraping/scrape_BL_set_info.py $cat --scrape-only-release-year >>"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_info_${TIMESTAMP}_std.log" 2>&1

    # upsert to Notion
    python notion/async_upsert_sets_data.py $cat >>"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/upsert_to_notion_${TIMESTAMP}_std.log" 2>&1
done

type="minifigs"
echo $type
for cat in sw sh; do  # avt hp hfw col
    echo $cat
    python scraping/scrape_BL_init.py $cat $type >>"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_init_${TIMESTAMP}_std.log" 2>&1
done

deactivate

#python scraping/scrape_BL_init.py $cat >"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/${TIMESTAMP}_stdout.log" 2>"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/${TIMESTAMP}_stderr.log"