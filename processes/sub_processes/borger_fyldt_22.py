"""Module for fetching citizen that have turned 22 as of today's date"""

import os

import logging

import requests


from helpers import helper_functions, ats_functions

logger = logging.getLogger(__name__)

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


def main(item_data: dict):
    """Main function to execute the script."""

    data = []
    references = []

    citizen_cpr = item_data.get("cpr")

    meta_data_for_dashboard = {
        "cpr": citizen_cpr,
        "name": item_data.get("fullName"),
        "clinic": item_data.get("clinic"),
    }

    _create_process_run(meta=meta_data_for_dashboard)

    _add_to_faglig_vurdering_queue(item_data=item_data, item_reference=citizen_cpr)

    references.append(citizen_cpr)
    data.append(item_data)

    return data, references


def _create_process_run(meta: dict) -> dict:
    """
    Sends a POST request to create a new process run.
    Requires meta with at least 'cpr' and 'name' keys.
    """

    print("inside create_process_run() func")

    process_name = "Udskrivning 22 år"
    process_id = helper_functions.find_process_id_by_name(process_name=process_name).get("id")

    url = "https://mbu-dashboard-api.adm.aarhuskommune.dk/api/v1/runs/"

    headers = {
        "X-API-Key": os.getenv("API_ADMIN_TOKEN"),
        "Content-Type": "application/json"
    }

    payload = {
        "entity_id": meta.get("cpr"),
        "entity_name": meta.get("name"),
        "meta": meta,
        "process_id": process_id
    }

    print("before try post")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        print("printing the response from the post attempt:")
        print(response)
        print(response.json())

    except requests.RequestException as e:
        print("Error creating process run:", e)

        raise
    print("after try post")


def _add_to_faglig_vurdering_queue(item_data: dict, item_reference: str):
    faglig_vurdering_queue = helper_functions.fetch_next_workqueue(faglig_vurdering=True)

    existing_refs = {str(r) for r in ats_functions.get_workqueue_items(faglig_vurdering_queue)}

    ref = item_reference

    if ref and ref not in existing_refs:
        faglig_vurdering_queue.add_item({"item": {"reference": ref, "data": item_data}}, ref)
