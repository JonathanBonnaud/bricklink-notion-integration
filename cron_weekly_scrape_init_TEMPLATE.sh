#!/bin/bash

TIMESTAMP=$(date +%F_%T)
echo $TIMESTAMP

source venv/bin/activate
export PYTHONPATH=$PYTHONPATH

type="sets"
echo $type":"
for cat in sw sh hp idea crea; do  # avt hfw col poc mof lor
    echo $cat
    python scraping/scrape_BL_init.py $cat $type >>"./cronlogs/scrape_BL_init_${TIMESTAMP}_std.log" 2>&1
    python scraping/scrape_BL_set_info.py $cat --scrape-only-release-year >>"./cronlogs/scrape_BL_info_${TIMESTAMP}_std.log" 2>&1

    # upsert to Notion
    python notion/async_upsert_sets_data.py $cat >>"./cronlogs/upsert_to_notion_${TIMESTAMP}_std.log" 2>&1

done

type="minifigs"
echo $type":"
for cat in sw sh hp idea; do  # avt hfw col crea poc mof lor
    echo $cat
    python scraping/scrape_BL_init.py $cat $type >>"./cronlogs/scrape_BL_init_${TIMESTAMP}_std.log" 2>&1
done
echo "Done!"
deactivate
