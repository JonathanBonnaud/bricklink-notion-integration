MINIFIG_SCHEMA = {
    # DB properties
    "Id": {"name": "Id", "type": "title", "title": {}},
    "Name": {"id": "title", "name": "Name", "type": "rich_text", "rich_text": {}},
    "Category": {
        "name": "Category",
        "type": "select",
        "select": {
            "options": [
                {"name": "Star Wars", "color": "default"},
                {"name": "Super Heroes", "color": "purple"},
                {"name": "Minecraft", "color": "green"},
                {"name": "Avatar", "color": "blue"},
            ]
        },
    },
    "Sub Category": {"name": "Sub Category", "type": "rich_text", "rich_text": {}},
    "Image": {"name": "Image", "type": "files", "files": {}},
    "Avg price raw": {"name": "Avg price raw", "type": "rich_text", "rich_text": {}},
    "Avg price PLN": {
        "name": "Avg price PLN",
        "type": "number",
        "number": {"format": "zloty"},
    },
    "Avg price EUR": {
        "name": "Avg price EUR",
        "type": "number",
        "number": {"format": "euro"},
    },
    "BrickLink": {"name": "BrickLink", "type": "url", "url": {}},
    "Release Year": {
        "name": "Release Year",
        "type": "number",
        "number": {"format": "number"},
    },
    # Properties used in Notion
    "owned": {"name": "owned", "type": "checkbox", "checkbox": {}},
    "Wanted": {"name": "Wanted", "type": "checkbox", "checkbox": {}},
    "Condition": {
        "name": "Condition",
        "type": "multi_select",
        "multi_select": {
            "options": [
                {"name": "Incomplete", "color": "brown"},
                {"name": "Marked", "color": "red"},
            ]
        },
    },
    "Total Quantity": {
        "name": "Total Quantity",
        "type": "number",
        "number": {"format": "number"},
    },
    "Incomplete/Marked": {
        "name": "Incomplete/Marked",
        "type": "number",
        "number": {"format": "number"},
    },
    "Quantity To Sell": {
        "name": "Quantity To Sell",
        "type": "formula",
        "formula": {"expression": 'prop("Total Quantity") - 1'},
    },
    "Status": {
        "name": "Category",
        "type": "select",
        "select": {
            "options": [
                {"name": "Purchased", "color": "orange"},
                {"name": "In Research", "color": "yellow"},
            ]
        },
    },
    "is_released_this_year": {
        "name": "is_released_this_year",
        "type": "formula",
        "formula": {"expression": 'prop("Release Year") == year(now())'},
    },
    # "OLX Search": {
    #     "name": "OLX Search",
    #     "type": "formula",
    #     "formula": {"expression": '"https://www.olx.pl/oferty/q-lego-" + prop("Id")'},
    # },
}

SET_SCHEMA = {
    # DB properties
    "Id": {"name": "Id", "type": "title", "title": {}},
    "Name": {"id": "title", "name": "Name", "type": "rich_text", "rich_text": {}},
    "Category": {
        "name": "Category",
        "type": "select",
        "select": {
            "options": [
                {"name": "Star Wars", "color": "default"},
                {"name": "Super Heroes", "color": "purple"},
                {"name": "Minecraft", "color": "green"},
                {"name": "Avatar", "color": "blue"},
            ]
        },
    },
    "Sub Category": {"name": "Sub Category", "type": "rich_text", "rich_text": {}},
    "Image": {"name": "Image", "type": "files", "files": {}},
    "Avg price raw": {"name": "Avg price raw", "type": "rich_text", "rich_text": {}},
    "Avg price PLN": {
        "name": "Avg price PLN",
        "type": "number",
        "number": {"format": "zloty"},
    },
    "Avg price EUR": {
        "name": "Avg price EUR",
        "type": "number",
        "number": {"format": "euro"},
    },
    "BrickLink": {"name": "BrickLink", "type": "url", "url": {}},
    "Release Year": {
        "name": "Release Year",
        "type": "number",
        "number": {"format": "number"},
    },
    # Properties used in Notion
    "owned": {"name": "owned", "type": "checkbox", "checkbox": {}},
    "Wanted": {"name": "Wanted", "type": "checkbox", "checkbox": {}},
    "Condition": {
        "name": "Condition",
        "type": "multi_select",
        "multi_select": {
            "options": [
                {"name": "Incomplete", "color": "brown"},
                {"name": "Marked", "color": "red"},
            ]
        },
    },
    "Incomplete/Marked": {
        "name": "Incomplete/Marked",
        "type": "number",
        "number": {"format": "number"},
    },
    "is_released_this_year": {
        "name": "is_released_this_year",
        "type": "formula",
        "formula": {"expression": 'prop("Release Year") == year(now())'},
    },
    "Lego store": {
        "name": "Lego store",
        "type": "formula",
        "formula": {
            "expression": '"https://www.lego.com/pl-pl/product/" + substring(prop("Id"), 0 , -2)'
        },
    },
    "Brickset": {
        "name": "Brickset",
        "type": "formula",
        "formula": {"expression": '"https://brickset.com/sets/" + prop("Id")'},
    },
    # "Promoklocki": {
    #     "name": "Promoklocki",
    #     "type": "formula",
    #     "formula": {"expression": '"https://promoklocki.pl/"+ substring(prop("Id"), 0, -2)'},
    # },
    # "OLX Search": {
    #     "name": "OLX Search",
    #     "type": "formula",
    #     "formula": {"expression": '"https://www.olx.pl/oferty/q-lego-" + substring(prop("Id"), 0, -2)'},
    # },
}

MINIFIG_PRICE_HISTORY_SCHEMA = {
    "Id": {"name": "Id", "type": "title", "title": {}},
    "Avg price raw": {"name": "Avg price raw", "type": "rich_text", "rich_text": {}},
    "Avg price PLN": {
        "name": "Avg price PLN",
        "type": "number",
        "number": {"format": "zloty"},
    },
    "Avg price EUR": {
        "name": "Avg price EUR",
        "type": "number",
        "number": {"format": "euro"},
    },
    "Scraped At": {
        "name": "Scraped At",
        "type": "date",
        "date": {},
    },
    "Minifig": {
        "name": "Minifig",
        "type": "relation",
        "relation": {
            "database_id": "8e5d75c0-230f-4b31-a58d-0aabb6f86aad",  # FIXME: add this in create_db script
            "dual_property": {},
        },
    },
}
