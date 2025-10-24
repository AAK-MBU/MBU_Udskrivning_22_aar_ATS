"""Module for fetching patients that have turned 22 as of today's date"""

import os

from mbu_dev_shared_components.solteqtand.database.db_handler import SolteqTandDatabase

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


def main(item_data: dict):
    """Main function to execute the script."""

    citizens_turned_22 = []
    data = []
    references = []

    prefix = item_data.get("todays_date")

    db_handler = SolteqTandDatabase(conn_str=SOLTEQ_TAND_DB_CONN_STRING)

    patiens_in_age_range = get_patients_turning_22_today(db_handler, prefix)

    for patient in patiens_in_age_range:
        patient_id = patient["patientId"]
        patient_cpr = patient["cpr"]
        patient_full_name = f"{patient['firstName']} {patient['lastName']}"

        filters = {"p.cpr": patient_cpr}

        list_of_associated_primary_clinics = db_handler.get_list_of_primary_dental_clinics(filters=filters)

        if not list_of_associated_primary_clinics:
            citizen_clinic = "Ingen klinik fundet"

        else:
            citizen_clinic = list_of_associated_primary_clinics[0].get("preferredDentalClinicName")

        # Add to result list
        citizens_turned_22.append({
            "patientId": patient_id,
            "cpr": patient_cpr,
            "fullName": patient_full_name,
            "clinic": citizen_clinic,
        })

    for citizen in citizens_turned_22:
        references.append(citizen["cpr"])
        data.append(citizen)

    return data, references


def get_patients_turning_22_today(db_handler: SolteqTandDatabase, prefix):
    """
    Get patients who are exactly (years, months) old based on CPR.
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
