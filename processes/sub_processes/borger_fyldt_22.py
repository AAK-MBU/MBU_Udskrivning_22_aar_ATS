"""Module for fetching citizen that have turned 22 as of today's date"""

import os
import requests

from datetime import datetime

from mbu_dev_shared_components.solteqtand.database.db_handler import SolteqTandDatabase

from helpers import helper_functions

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


# pylint: disable=unused-argument
def main(item_data: dict, item_reference: dict):
    """Main function to execute the script."""

    citizens_turned_22 = []
    data = []
    references = []

    prefix = item_data.get("todays_date")

    db_handler = SolteqTandDatabase(conn_str=SOLTEQ_TAND_DB_CONN_STRING)

    citizen_in_age_range = get_citizen_turning_22_today(db_handler, prefix)

    for citizen_solteq in citizen_in_age_range:
        patient_id = citizen_solteq["patientId"]
        citizen_cpr = citizen_solteq["cpr"]
        citizen_full_name = f"{citizen_solteq['firstName']} {citizen_solteq['lastName']}"

        filters = {"p.cpr": citizen_cpr}

        list_of_associated_primary_clinics = db_handler.get_list_of_primary_dental_clinics(filters=filters)

        if not list_of_associated_primary_clinics:
            citizen_clinic = "Ingen klinik fundet"

        else:
            citizen_clinic = list_of_associated_primary_clinics[0].get("preferredDentalClinicName")

        # Add to result list
        citizens_turned_22.append({
            "patientId": patient_id,
            "cpr": citizen_cpr,
            "fullName": citizen_full_name,
            "clinic": citizen_clinic,
        })

    for citizen in citizens_turned_22:
        references.append(citizen_cpr)
        data.append(citizen)

    return data, references


def get_citizen_turning_22_today(db_handler: SolteqTandDatabase, prefix):
    """
    Get citizen who are exactly 22 years old based on CPR.
    """

    query = """
        SELECT
            patientId,
            firstName,
            lastName,
            cpr
        FROM
            [tmtdata_prod].[dbo].[PATIENT]
        WHERE
            cpr LIKE ?
        ORDER BY
            firstName, lastName;
    """

    like_param = f"{prefix}%"

    # pylint: disable=protected-access
    return db_handler._execute_query(query, params=(like_param,))


def finalization(workqueue, url):
    """
    Process to finalize
    """

    # full_process_dashboard_url = f"{url}/api/v1/runs"

    # dashboard_headers = {"X-API-Key": os.getenv("API_ADMIN_TOKEN")}

    workitems = helper_functions.fetch_workqueue_workitems(workqueue=workqueue)

    for item in workitems:
        now = datetime.now().date()
        item_created_at = datetime.fromisoformat(item.get("created_at")).date()

        if now != item_created_at:
            continue

        workitem_id = item.get("id")
        workitems_data = (item.get("data", {}).get("item", {}).get("data", {}))

        cpr = workitems_data.get("cpr")
        entity_id = f"{cpr[:6]}-{cpr[6:]}"

        entity_name = workitems_data.get("fullName")

        full_data_object = {
            "entity_id": entity_id,
            "entity_name": entity_name,
            "meta": {
                "cpr": cpr,
                "name": entity_name,
                "clinic": workitems_data.get("clinic"),
                "workitem_id": workitem_id
            },
            "process_id": 1,
        }

        # requests.post(url=full_process_dashboard_url, data=full_data_object, headers=dashboard_headers, timeout=60)
