"""Module for fetching patients that have turned 22 as of today's date"""

import os

from mbu_dev_shared_components.solteqtand.database.db_handler import SolteqTandDatabase

from mbu_rpa_core.exceptions import BusinessError

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


def main(item_data: dict):
    """Main function to execute the script."""

    data = []
    references = []

    citizen_cpr = item_data.get("cpr")
    ydernummer = item_data.get("new_clinic_ydernummer")
    phone_number = item_data.get("new_clinic_phone_number")

    db_handler = SolteqTandDatabase(conn_str=SOLTEQ_TAND_DB_CONN_STRING)

    clinics = []

    # First try using ydernummer (if provided)
    if ydernummer:
        clinics = db_handler.get_list_of_clinics(filters={"contractorId": ydernummer})

    # If nothing found, try using phone number
    if not clinics and phone_number:
        clinics = db_handler.get_list_of_clinics(filters={"phoneNumber": phone_number})

    # Final validation
    if clinics:
        references.append(citizen_cpr)
        data.append(item_data)

    else:
        raise BusinessError("Borgerens ønskede tandklinik mangler information eller eksisterer ikke i Solteq Tand")

    return data, references
