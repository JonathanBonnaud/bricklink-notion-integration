# bricklink-notion-integration

Notion integration with BrickLink data.
The integration allows you to keep track of your Lego collection in Notion.

Using Beautifulsoup for scraping, Notion SDK, and asyncio

## 1. Set up Database

`python sqlite.py`

## 2. To run the scraper

- CATEGORY values: [sw, sh, hp, avt, hfw, col]

- TYPE values: [minifigs, sets]

#### 2.1. Insert data (Only basic info)

Either automatically scrape lists from BrickLink:

`python scraping/scrape_BL_init.py CATEGORY TYPE`

Or from manually downloaded files (from BL):

`python scraping/process_BL_minifigs_downloaded_file.py CATEGORY TYPE`

#### 2.2. Update data (All info)

`python scraping/scrape_BL_set_info.py CATEGORY`

and

`python scraping/scrape_BL_minifig_info.py CATEGORY`

## 3. To insert/update the data into Notion

Make sure you have the following environment variables set:

- ACCOUNT

And create the file `notion/private_secrets.py` with missing credentials for Notion

### 3.1. Create a new database in Notion (to do only once)

`python notion/create_db.py ALL`

or `python notion/create_db.py [minifigs|sets]`

### 3.2. Insert or update pages to the database in Notion

`python notion/async_upsert_minifigs_data.py CATEGORY`

## 4. Scheduling

Edit cron jobs with `crontab -e`:

And add for example:

```bash
35 9 * * 1 cd /PATH_TO_PROJECT/bricklink-notion-integration && sh cron_weekly_scrape_init.sh
35 10,15 * * * cd /PATH_TO_PROJECT/bricklink-notion-integration && sh cron_daily_scrape_info.sh
```

---

## Remaining Work To Do

### In scraping/

- scrape_BL_ids : save ids in sqlite - `DONE`
    - could even get id, name, category, subcategory
- then read ids from sqlite to scrape info - `DONE`
- read data from Notion where owned=True to process this data in priority - `DONE`
- create priority list of minifigs to scrape - `DONE`
    - 1- owned > 2- wanted > 3- most recent
- add to table:  last_scraped_at - `DONE`
- differentiate when really no price vs BL quota reached - `DONE`
- general refactor (factorize code, create classes, optimize where possible, etc)

### In notion/

- create async methods to send the data to Notion - `DONE`
- add to notion_mapping table: last_updated_at - `DONE`

### Deployment / Scheduling

- add cron scheduling (weekly scrape ids for new, daily scrape infos) - `DONE`
- create serverless deployment
- deploy to AWS
    - and schedule the scraper
    - and schedule the inserter/updater