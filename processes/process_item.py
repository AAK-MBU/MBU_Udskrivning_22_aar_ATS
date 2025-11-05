"""Module to handle item processing"""

import sys
import logging

from mbu_rpa_core.exceptions import BusinessError

from processes.sub_processes import (
    borger_fyldt_22,
    faglig_vurdering_udfoert,
    aftale_oprettet_i_solteq,
)

from helpers import helper_functions

logger = logging.getLogger(__name__)

PROCESS_FLOW_MAP = {
    "--borger_fyldt_22": {
        "main": borger_fyldt_22.main,
        "process_step_name": "Borger fyldt 22 år",
    },
    "--aftale_oprettet_i_solteq": {
        "main": aftale_oprettet_i_solteq.main,
        "process_step_name": "Aftale oprettet i Solteq Tand",
    },
    "--faglig_vurdering_udfoert": {
        "main": faglig_vurdering_udfoert.main,
        "process_step_name": "Faglig vurdering",
    }
}


def process_item(workitem_id: int, item_data: dict, item_reference: str):
    """
    Entry point for processing a single item.
    Dispatches to the appropriate flow based on CLI argument.
    """

    assert item_data, "Item data is required"
    assert item_reference, "Item reference is required"

    try:
        for arg, proc_config in PROCESS_FLOW_MAP.items():
            if arg not in sys.argv:
                continue

            logger.info(f"Running flow: {arg}")

            process_name = proc_config.get("process_step_name")

            if arg == "--borger_fyldt_22":
                proc_config["main"](item_data=item_data, item_reference=item_reference)

            else:
                helper_functions.handle_process_dashboard(status="running", item_reference=item_reference, process_name=process_name)

                proc_config["main"](item_data=item_data)

            helper_functions.handle_process_dashboard(status="success", item_reference=item_reference, process_name=process_name)

            break

    except BusinessError as be:
        logger.info(f"BusinessError: {be}")

        helper_functions.handle_process_dashboard(status="failed", item_reference=item_reference, process_name=process_name, workitem_id=workitem_id)

        raise

    except Exception as e:
        logger.exception(f"Unexpected error while processing item: {e}")

        helper_functions.handle_process_dashboard(status="failed", item_reference=item_reference, process_name=process_name, workitem_id=workitem_id)

        raise
