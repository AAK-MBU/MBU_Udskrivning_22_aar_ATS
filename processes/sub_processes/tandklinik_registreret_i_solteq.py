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

    db_handler = SolteqTandDatabase(conn_str=SOLTEQ_TAND_DB_CONN_STRING)

    filters = {"contractorId": ydernummer}

    clinics = db_handler.get_list_of_clinics(filters=filters)

    if clinics:
        references.append(citizen_cpr)
        data.append(item_data)

    else:
        raise BusinessError("Borgerens ønskede tandklinik er ikke registreret i Solteq Tand")

    return data, references
