#!/usr/bin python3
# -*- coding: utf-8 -*-

import os
import requests
from urllib.parse import urlencode
from dateutil.parser import parse

request_limit = 50
revisions_query = {
    "format": "json",
    "action": "query",
    "list": "allrevisions",
    "arvstart": parse(os.getenv('START')).strftime('%Y-%m-%dT%H:%M:%SZ') if os.getenv('START') else None,
    "arvend": parse(os.getenv('STOP')).strftime('%Y-%m-%dT%H:%M:%SZ') if os.getenv('STOP') else None,
    "arvdir": "newer",
    "arvlimit": request_limit,
    "arvnamespace": 6,
    "arvslots": "main",
    "arvprop": "ids|tags|timestamp"
}
tag = os.getenv('TAG') if os.getenv('TAG') else None

sum_files = 0
sum_categories_hidden = 0
sum_categories_other = 0
sum_zero_categories = 0

while True:
    revisions_response = requests.get(f"https://commons.wikimedia.org/w/api.php?{urlencode(revisions_query)}")
    if revisions_response.status_code != 200:
        break
    revisions_json = revisions_response.json()

    for page in revisions_json['query']['allrevisions']:
        revision = page['revisions'][0]

        # filter out edits that are not a page creation
        if revision['parentid'] != 0:
            continue

        # filter out pages with tags we're not interested in
        if tag is not None and tag not in revision['tags']:
            continue

        # get categories
        categories_response = requests.get(f"https://commons.wikimedia.org/w/api.php?format=json&action=parse&oldid={revision['revid']}&prop=categories")
        if categories_response.status_code != 200:
            continue
        categories_json = categories_response.json()

        # calculate amount of hidden/visible categories
        categories = categories_json['parse']['categories']
        categories_hidden = len([cat for cat in categories if 'hidden' in cat.keys()])
        categories_other = len([cat for cat in categories if 'hidden' not in cat.keys()])
        # print(f"{revision['timestamp']} - {page['title']}: {categories_hidden + categories_other} (hidden: {categories_hidden}, other: {categories_other})", flush=True)

        # add to totals
        sum_files += 1
        sum_categories_hidden += categories_hidden
        sum_categories_other += categories_other
        sum_zero_categories += 1 if categories_other == 0 else 0

    if 'continue' in revisions_json:
        # prep next request - continue from here
        revisions_query['arvcontinue'] = revisions_json['continue']['arvcontinue']
    else:
        # or stop
        break


print()
print(f"Uploads: {sum_files}")
print(f"- With non-hidden category: {sum_files - sum_zero_categories} ({(sum_files - sum_zero_categories) / sum_files * 100:.2f}%)")
print(f"- Without non-hidden category: {sum_zero_categories} ({sum_zero_categories / sum_files * 100:.2f}%)")
print(f"Categories total: {sum_categories_hidden + sum_categories_other}")
print(f"- Hidden: {sum_categories_hidden}")
print(f"- Other: {sum_categories_other}")
print(f"Categories average: {(sum_categories_hidden + sum_categories_other) / sum_files}")
print(f"- Hidden: {sum_categories_hidden / sum_files}")
print(f"- Other: {sum_categories_other / sum_files}")
