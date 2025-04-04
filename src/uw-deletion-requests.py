#!/usr/bin python3
# -*- coding: utf-8 -*-

import os
import re
import requests
import urllib3
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timedelta
from dateutil.parser import parse


user_agent = "Script to count amount of deletion requests related to UW uploads"
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests_session = requests.Session()
retries = requests.adapters.Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
requests_session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retries))


tag = os.getenv("TAG") if os.getenv("TAG") else None
days = int(os.getenv("DAYS")) if os.getenv("DAYS") else None
text = os.getenv("TEXT") if os.getenv("TEXT") else None
start = (datetime.fromtimestamp(int(os.getenv("START"))) if os.getenv("START").isnumeric() else parse(os.getenv("START"))) if os.getenv("START") else None
stop = (datetime.fromtimestamp(int(os.getenv("STOP"))) if os.getenv("STOP").isnumeric() else parse(os.getenv("STOP"))) if os.getenv("STOP") else None
if start is None:
    exit("No start date provided")
if stop is None:
    exit("No stop date provided")

deletion_request_count = 0
deletion_request_pending_count = 0
deletion_request_deleted_count = 0
deletion_request_kept_count = 0
deletion_request_page_count = 0
deletion_request_pending_page_count = 0
deletion_request_deleted_page_count = 0
deletion_request_kept_page_count = 0
deletion_request_matching_page_count = 0
deletion_request_matching_pending_page_count = 0
deletion_request_matching_deleted_page_count = 0
deletion_request_matching_kept_page_count = 0


def check_deletions(page):
    deleted_revisions_response = requests_session.get(
        f"https://commons.wikimedia.org/w/api.php?format=json&action=query&prop=deletedrevisions&titles={quote_plus(page)}&drvprop=tags|timestamp",
        headers={"User-Agent": user_agent},
        verify=False,
        timeout=120,
    )
    if deleted_revisions_response.status_code != 200:
        return {
            # @todo handle failures better
            "missing": False,
            "matching": False,
        }

    deleted_revisions_json = deleted_revisions_response.json()
    page_id = list(deleted_revisions_json["query"]["pages"].keys())[0]

    if "deletedrevisions" in deleted_revisions_json["query"]["pages"][page_id]:
        revisions = deleted_revisions_json["query"]["pages"][page_id]["deletedrevisions"]
    else:
        revisions_response = requests_session.get(
            f"https://commons.wikimedia.org/w/api.php?format=json&action=query&prop=revisions&titles={quote_plus(page)}&rvprop=tags|timestamp",
            headers={"User-Agent": user_agent},
            verify=False,
            timeout=120,
        )
        if revisions_response.status_code != 200:
            return {
                # @todo handle failures better
                "missing": False,
                "matching": False,
            }

        revisions_json = revisions_response.json()
        page_id = list(revisions_json["query"]["pages"].keys())[0]
        if "revisions" not in revisions_json["query"]["pages"][page_id]:
            return {
                "missing": True,
                "matching": False, # well we don't really know, but hey...
            }
        revisions = revisions_json["query"]["pages"][page_id]["revisions"]

    if tag is not None:
        revisions = list(filter(lambda revision: tag in revision["tags"], revisions))
    if days is not None:
        revisions = list(filter(lambda revision: parse(revision["timestamp"]).timestamp() >= (date - timedelta(days=days)).timestamp(), revisions))

    return {
        "missing": page_id == "-1",
        "matching": len(revisions) > 0,
    }


for day in range((stop - start).days):
    date = start + timedelta(days=day)

    active_response = requests_session.get(
        f"https://commons.wikimedia.org/w/api.php?format=json&action=parse&prop=wikitext&page=Commons:Deletion_requests/{date.strftime("%Y")}/{date.strftime("%m")}/{date.strftime("%d")}",
        headers={"User-Agent": user_agent},
        verify=False,
        timeout=120,
    )
    if active_response.status_code == 200:
        active_response_json = active_response.json()
        if not "error" in active_response_json:
            active_response_wikitext = active_response_json["parse"]["wikitext"]["*"]
            deletion_requests = list(set(re.findall("\\{\\{(Commons:Deletion requests/.+?)\\}\\}", active_response_wikitext)))
            deletion_request_count += len(deletion_requests)
            deletion_request_pending_count += len(deletion_requests)

            for deletion_request in deletion_requests:
                deletion_request_response = requests_session.get(f"https://commons.wikimedia.org/w/api.php?format=json&action=parse&prop=wikitext&page={quote_plus(deletion_request)}")
                if deletion_request_response.status_code != 200:
                    continue

                deletion_request_response_json = deletion_request_response.json()
                if not "error" in deletion_request_response_json:
                    deletion_request_response_wikitext = deletion_request_response_json["parse"]["wikitext"]["*"]
                    deletion_request_pages = list(set(re.findall("\\[\\[:?((?:File|Image):[^|]+?)\\]\\]", deletion_request_response_wikitext)))
                    deletion_request_page_count += len(deletion_request_pages)
                    deletion_request_pending_page_count += len(deletion_request_pages)

                    matches_text = True if text is None or text.casefold() in deletion_request_response_wikitext.casefold() else False

                    for deletion_request_page in deletion_request_pages:
                        result = check_deletions(deletion_request_page)
                        deletion_request_matching_page_count += 1 if result["matching"] and matches_text else 0
                        deletion_request_matching_pending_page_count += 1 if result["matching"] and matches_text else 0

    archive_response = requests_session.get(
        f"https://commons.wikimedia.org/w/api.php?format=json&action=parse&prop=wikitext&page=Commons:Deletion_requests/Archive/{date.strftime("%Y")}/{date.strftime("%m")}/{date.strftime("%d")}",
        headers={"User-Agent": user_agent},
        verify=False,
        timeout=120,
    )
    if archive_response.status_code == 200:
        archive_response_json = archive_response.json()
        if not "error" in archive_response_json:
            archive_response_wikitext = archive_response_json["parse"]["wikitext"]["*"]
            deletion_requests = list(set(re.findall("\\{\\{(Commons:Deletion requests/.+?)\\}\\}", archive_response_wikitext)))
            deletion_request_count += len(deletion_requests)

            for deletion_request in deletion_requests:
                deletion_request_response = requests_session.get(
                    f"https://commons.wikimedia.org/w/api.php?format=json&action=parse&prop=wikitext&page={quote_plus(deletion_request)}",
                    headers={"User-Agent": user_agent},
                    verify=False,
                    timeout=120,
                )
                if deletion_request_response.status_code != 200:
                    continue

                deletion_request_response_json = deletion_request_response.json()
                if not "error" in deletion_request_response_json:
                    deletion_request_response_wikitext = deletion_request_response_json["parse"]["wikitext"]["*"]
                    deletion_request_pages = list(set(re.findall("\\[\\[:?((?:File|Image):[^|]+?)\\]\\]", deletion_request_response_wikitext)))
                    deletion_request_deleted_count += 1 if "'''Deleted:'''" in deletion_request_response_wikitext else 0
                    deletion_request_kept_count += 1 if "'''Kept:'''" in deletion_request_response_wikitext else 0

                    matches_text = True if text is None or text.casefold() in deletion_request_response_wikitext.casefold() else False

                    for deletion_request_page in deletion_request_pages:
                        result = check_deletions(deletion_request_page)
                        deletion_request_page_count += 1
                        deletion_request_deleted_page_count += 1 if result["missing"] else 0
                        deletion_request_kept_page_count += 1 if not result["missing"] else 0
                        deletion_request_matching_page_count += 1 if result["matching"] and matches_text else 0
                        deletion_request_matching_deleted_page_count += 1 if result["matching"] and matches_text and result["missing"] else 0
                        deletion_request_matching_kept_page_count += 1 if result["matching"] and matches_text and not result["missing"] else 0

    #print(f"{date.strftime("%Y-%m-%d")}")
    #print(f"Deletion requests: {deletion_request_count} (pending: {deletion_request_pending_count}; deleted: {deletion_request_deleted_count}; kept: {deletion_request_kept_count})")
    #print(f"Deletion request pages: {deletion_request_page_count} (pending: {deletion_request_pending_page_count}; deleted: {deletion_request_deleted_page_count}; kept: {deletion_request_kept_page_count})")
    #print(f"Matching deletion request pages: {deletion_request_matching_page_count} (pending: {deletion_request_matching_pending_page_count}; deleted: {deletion_request_matching_deleted_page_count}; kept: {deletion_request_matching_kept_page_count})")
    #print()

    #print(f"Date; Deletion requests; Pending deletion requests; Deleted deletion requests; Kept deletion requests; Deletion request pages; Pending deletion request pages; Deleted deletion request pages; Kept deletion request pages; Matching deletion request pages; Pending matching deletion request pages; Deleted matching deletion request pages; Kept matching deletion request pages")
    print(f"{date.strftime("%Y-%m-%d")}; {deletion_request_count}; {deletion_request_pending_count}; {deletion_request_deleted_count}; {deletion_request_kept_count}; {deletion_request_page_count}; {deletion_request_pending_page_count}; {deletion_request_deleted_page_count}; {deletion_request_kept_page_count}; {deletion_request_matching_page_count}; {deletion_request_matching_pending_page_count}; {deletion_request_matching_deleted_page_count}; {deletion_request_matching_kept_page_count}")
