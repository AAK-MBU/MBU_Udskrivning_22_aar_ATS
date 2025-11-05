"""Module for fetching citizen that have turned 22 as of today's date"""

import os

import logging

from datetime import datetime

import requests

from automation_server_client._models import Workqueue

from processes.sub_processes import handle_process_dashboard

from helpers import helper_functions, ats_functions

logger = logging.getLogger(__name__)

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


def main(item_data: dict, item_reference: str):
    """Main function to execute the script."""

    citizen_cpr = item_data.get("cpr")

    meta_data_for_dashboard = {
        "cpr": citizen_cpr,
        "clinic": item_data.get("clinic"),
        "name": item_data.get("fullName"),
        "patientId": item_data.get("patientId"),
        "new_clinic_ydernummer": "",
        "new_clinic_phone_number": "",
    }

    process_name = "Udskrivning 22 år"
    started_at_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    _create_process_run(process_name=process_name, started_at=started_at_str, meta=meta_data_for_dashboard)

    handle_process_dashboard.main(status="running", item_reference=item_reference, process_name=process_name)

    for workqueue_name in ["aftale_oprettet_i_solteq", "faglig_vurdering_udfoert"]:
        workqueue = ats_functions.fetch_workqueue(workqueue_name=workqueue_name)

        _enqueue_items(workqueue=workqueue, item_data=item_data, reference=item_reference)


def _create_process_run(process_name: str, started_at: str, meta: dict):
    """
    Sends a POST request to create a new process run.
    Requires meta with at least 'cpr' and 'name' keys.
    """

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
        "process_id": process_id,
        "started_at": started_at
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

    except requests.RequestException as e:
        logger.info(f"Error creating process run: {e}")

        raise


def _enqueue_items(workqueue: Workqueue, item_data: dict, reference: dict):
    """
    Enqueues each (reference, data) pair to the next workqueue, avoiding duplicates.

    Used for standard flows where further processing is required in later steps.
    """

    existing_refs = {str(r) for r in ats_functions.get_workqueue_items(workqueue)}

    if reference and reference not in existing_refs:
        workqueue.add_item({"item": {"reference": reference, "data": item_data}}, reference)
