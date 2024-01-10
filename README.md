# bricklink-notion-integration

Notion integration with BrickLink data.
The integration allows you to keep track of your Lego collection in Notion.

Using Beautifulsoup for scraping, Notion SDK, and asyncio

Here are some screenshots of what it looks like in Notion:

### The Database

<img width="1000" alt="Screenshot 2024-01-10 at 11 16 49" src="https://github.com/JonathanBonnaud/bricklink-notion-integration/assets/23031977/578ad01e-81de-4c82-ab0e-80d847c2441a">
<img width="1000" alt="Screenshot 2024-01-10 at 11 09 09" src="https://github.com/JonathanBonnaud/bricklink-notion-integration/assets/23031977/47b5a1e8-e214-4c63-ba5d-62f4656af271">

### Example of Inventory

<img width="1000" alt="Screenshot 2024-01-10 at 11 14 18" src="https://github.com/JonathanBonnaud/bricklink-notion-integration/assets/23031977/3e86d1b0-48b7-4e09-8ead-531d7476ea75">

---

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

First rename the file `notion/private_secrets_TEMPLATE.py` to `notion/private_secrets.py` with missing credentials for Notion

### 3.1. Create a new database in Notion (to be done ONLY ONCE)

`python notion/create_db.py ALL`

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
- Add logic (exponential backoff "delay = (base_delay * 2 ** retries + random.uniform(0, 1))") - `DONE`
    - logic: do not scrape if today < last_scraped_at + 2 ** failed_count days
    - add column in db: failed_count [default=0]
- general refactor (factorize code, create classes, optimize where possible, etc.)
- In the future, add logic to scrape based on last_scraped_at

### In notion/

- create async methods to send the data to Notion - `DONE`
- add to notion_mapping table: last_updated_at - `DONE`
