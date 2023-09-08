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

### Create a new database in Notion
`python notion/create_db.py ALL`

or `python notion/create_db.py [minifigs|sets]`


### Insert or update pages to the database in Notion
`python notion/upsert_minifigs_data.py`

or `python notion/upsert_minifigs_data.py CATEGORY`

or `python notion/upsert_minifigs_data.py CATEGORY --insert`

or `python notion/upsert_minifigs_data.py CATEGORY --update`

