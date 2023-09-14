# bricklink-notion-integration

Notion integration with BrickLink data

## Set up Database

`python sqlite.py`

## To run the scraper

#### Insert data from downloaded files (Only basic info: without *avg_price* and *appears_in*)

`python scraping/process_BL_minifigs_downloaded_file.py`

#### Categories: ['sw', 'sh', 'hp', 'avt', 'hfw']

[//]: # (1. `python scraping/scrape_minifig_ids.py CATEGORY`)
`python scraping/scrape_minifig_info.py CATEGORY`

## To insert/update the data into Notion

Make sure you have the following environment variables set:

- ACCOUNT

### Create a new database in Notion

`python notion/create_db.py ALL`

or `python notion/create_db.py [minifigs|sets]`

### Insert or update pages to the database in Notion

`python notion/upsert_minifigs_data.py`

or `python notion/upsert_minifigs_data.py CATEGORY`

or `python notion/upsert_minifigs_data.py CATEGORY --insert`

or `python notion/upsert_minifigs_data.py CATEGORY --update`

## Remaining Work To Do

### In scraping/

- scrape_BL_ids : save ids in sqlite
    - could even get id, name, category, subcategory
- then read ids from sqlite to scrape info
- add to table:  last_scraped_at

### In notion/

- create async methods to send the data to Notion - DONE
- read data from Notion where owned=True to process this data in priority
- add to notion_mapping table: last_updated_at

### Deployment

- create serverless deployment
- deploy to AWS
    - and schedule the scraper
    - and schedule the inserter/updater