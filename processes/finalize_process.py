"""Module to handle process finalization"""
# from mbu_rpa_core.exceptions import ProcessError, BusinessError

import sys
import os
import logging

import requests

from mbu_rpa_core.exceptions import BusinessError

from processes.sub_processes import (
    borger_fyldt_22,
    faglig_vurdering_udfoert,
    aftale_oprettet_i_solteq,
    formular_indsendt,
    tandklinik_registreret_i_solteq
)

from helpers import helper_functions

logger = logging.getLogger(__name__)

PROCESS_MAP = {
    "--borger_fyldt_22": borger_fyldt_22.finalization,
    "--aftale_oprettet_i_solteq": aftale_oprettet_i_solteq.finalization,
    "--faglig_vurdering_udfoert": faglig_vurdering_udfoert.finalization,
    "--formular_indsendt": formular_indsendt.finalization,
    "--tandklinik_registreret_i_solteq": tandklinik_registreret_i_solteq.finalization,
}


def finalize_process():
    """Function to handle process finalization"""

    workqueue = helper_functions.fetch_next_workqueue(faglig_vurdering=False)

    process_dashboard_url = "mbu-dashboard-api.adm.aarhuskommune.dk"

    workitems = helper_functions.fetch_workqueue_workitems(workqueue=workqueue)

    full_process_dashboard_url = f"{process_dashboard_url}/api/v1/runs"

    dashboard_headers = {"X-API-Key": os.getenv("PROCESS_DASHBOARD_API_KEY")}

    for arg, func in PROCESS_MAP.items():
        if arg in sys.argv:
            try:
                func(workqueue=workqueue, url=process_dashboard_url)

            except BusinessError as be:
                logger.info(f"BusinessError: {be}")

            except Exception as e:
                logger.exception(f"Unexpected error while processing item: {e}")

            break

    sys.exit()
