# bricklink-notion-integration
Notion integration with BrickLink data

## Set up Database
`python sqlite.py`

## To run the scraper

#### Categories: ['sw', 'sh', 'hp', 'avt', 'hfw']
1. `python scraping/scrape_minifig_ids.py CATEGORY`
2. `python scraping/scrape_minifig_info.py CATEGORY`

## To insert the data into Notion

### Create a new database in Notion
`python notion/create_db.py`

### Add pages to the database in Notion
`python notion/add_page_to_db.py CATEGORY`

or
`python notion/add_all_pages_to_db.py` for all categories