MINIFIG_MINIMAL_SCHEMA = {
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
    # "Appears In": {"id": "fBth", "name": "Appears In", "type": "relation",
    #                      "relation": {"database_id": "4816f486-d580-43d8-b32b-94a644c1434e",
    #                                   "type": "dual_property",
    #                                   "dual_property": {"synced_property_name": "Minifigs",
    #                                                     "synced_property_id": "%3FeyZ"}}},
    "Appears In": {"name": "Appears In", "type": "rich_text", "rich_text": {}},
    "Avg price raw": {"name": "Avg price raw", "type": "rich_text", "rich_text": {}},
    "Avg price PLN": {
        "name": "Avg price PLN",
        "type": "number",
        "number": {"format": "zloty"},
    },
    "BrickLink": {"name": "BrickLink", "type": "url", "url": {}},
    "Release Year": {
        "name": "Release Year",
        "type": "number",
        "number": {"format": "number"},
    },
}
