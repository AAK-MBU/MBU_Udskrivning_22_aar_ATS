"""Module for fetching citizen that have turned 22 as of today's date"""

import os

import logging

from helpers import helper_functions, ats_functions

logger = logging.getLogger(__name__)

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


def main(item_data: dict, item_reference: str):
    """Main function to execute the script."""

    citizen_cpr = item_data.get("cpr")

    process_name = "Udskrivning 22 år"

    meta_data_for_dashboard = {
        "cpr": citizen_cpr,
        "clinic": item_data.get("clinic"),
        "name": item_data.get("fullName"),
        "patientId": item_data.get("patientId"),
        "new_clinic_ydernummer": "",
        "new_clinic_phone_number": "",
    }

    logger.info(f"Creating process run for cpr: {citizen_cpr} ...")
    helper_functions.handle_dashboard_run_creation(process_name=process_name, meta=meta_data_for_dashboard)

    process_step_name = "Borger fyldt 22 år"

    logger.info(f"Handling dashboard update for step: {process_step_name} ...")
    helper_functions.handle_process_dashboard(status="running", item_reference=item_reference, process_step_name=process_step_name)

    for workqueue_name in ["aftale_oprettet_i_solteq", "faglig_vurdering_udfoert"]:
        workqueue = ats_functions.fetch_workqueue(workqueue_name=workqueue_name)

        ats_functions.enqueue_items(workqueue=workqueue, item_data=item_data, reference=item_reference)
