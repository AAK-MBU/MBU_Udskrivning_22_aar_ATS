"""Module for fetching patients that have turned 22 as of today's date"""

import os

from mbu_dev_shared_components.solteqtand.database.db_handler import SolteqTandDatabase

from mbu_rpa_core.exceptions import BusinessError

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


# pylint: disable=unused-argument
def main(item_data: dict, item_reference: dict):
    """Main function to execute the script."""

    citizen_cpr = item_reference

    db_handler = SolteqTandDatabase(conn_str=SOLTEQ_TAND_DB_CONN_STRING)

    citizen_bookings = faglig_vurdering_udfoert(db_handler=db_handler, cpr=citizen_cpr)

    if not citizen_bookings:
        raise BusinessError("Faglig vurdering endnu ikke udført")

    return True


def faglig_vurdering_udfoert(db_handler: SolteqTandDatabase, cpr: str):
    """
    Check if a citizen has a booking with the specified aftaletype and -status
    """

    query = """
        SELECT
            b.BookingID,
            b.CreatedDateTime,
            bt.Description,
            b.Status
        FROM
            [tmtdata_prod].[dbo].[BOOKING] b
        JOIN
            PATIENT p ON p.patientId = b.patientId
        JOIN
            BOOKINGTYPE bt ON bt.BookingTypeID = b.BookingTypeID
        WHERE
            cpr = ?
            AND Description = 'Z - 22 år - Borger fyldt 22 år'
            AND (Status = '632' OR Status = '634')
        ORDER BY
            CreatedDateTime DESC
    """

    # pylint: disable=protected-access
    return db_handler._execute_query(query, params=(cpr,))


def finalization():



    return