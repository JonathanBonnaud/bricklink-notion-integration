#!/bin/bash

TIMESTAMP=$(date +%F_%T)
echo $TIMESTAMP

source venv/bin/activate
export PYTHONPATH=$PYTHONPATH:/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration

for type in minifigs sets; do
    echo $type
    for cat in sw sh; do  # avt hp hfw col
        echo $cat
        python scraping/scrape_BL_init.py $cat $type >>"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/scrape_BL_init_${TIMESTAMP}_std.log" 2>&1
    done
done

#python scraping/scrape_BL_init.py $cat >"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/${TIMESTAMP}_stdout.log" 2>"/Users/jonathanbonnaud/PycharmProjects/bricklink-notion-integration/cronlogs/${TIMESTAMP}_stderr.log"
deactivate