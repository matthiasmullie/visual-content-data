#!/usr/bin python3
# -*- coding: utf-8 -*-

import json
import requests
import urllib3
from urllib.parse import urlencode

user_agent = "Script to count depth of categories added to UW uploads"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests_session = requests.Session()
retries = requests.adapters.Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
requests_session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))

request_limit = 50
categories_query = {
    "format": "json",
    "action": "query",
    "list": "allcategories",
    "aclimit": request_limit,
}

parents_map = {}

while True:
    categories_response = requests_session.get(
        f"https://commons.wikimedia.org/w/api.php?{urlencode(categories_query)}",
        headers={"User-Agent": user_agent},
        verify=False,
        timeout=120,
    )
    if categories_response.status_code != 200:
        raise Exception("Request failed")
    categories_json = categories_response.json()
    if "error" in categories_json:
        raise Exception("Invalid response")

    for page in categories_json["query"]["allcategories"]:
        category_title = f"Category:{page["*"]}"

        parent_categories_query = {
            "format": "json",
            "action": "query",
            "titles": category_title,
            "prop": "categories",
            "cllimit": 500,
        }
        parent_categories_response = requests_session.get(
            f"https://commons.wikimedia.org/w/api.php?{urlencode(parent_categories_query)}",
            headers={"User-Agent": user_agent},
            verify=False,
            timeout=120,
        )
        if parent_categories_response.status_code != 200:
            raise Exception("Request failed")
        parent_categories_json = parent_categories_response.json()
        if "error" in parent_categories_json:
            raise Exception("Invalid response")

        parents_map[category_title] = []
        parent_categories_pages = list(parent_categories_json["query"]["pages"].values())[0]
        if "categories" not in parent_categories_pages:
            continue

        for parent_category in parent_categories_pages["categories"]:
            parents_map[category_title].append(parent_category["title"])

    print(".", end="", flush=True)

    if "continue" in categories_json:
        # prep next request - continue from here
        categories_query.update(categories_json["continue"])
    else:
        # or stop
        break


f = open("categories_parents_map.json", "a")
f.write(json.dumps(parents_map))
f.close()
