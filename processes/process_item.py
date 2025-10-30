"""Module to handle item processing"""

import sys
import logging

from mbu_rpa_core.exceptions import BusinessError

from processes.sub_processes import (
    borger_fyldt_22,
    faglig_vurdering_udfoert,
    aftale_oprettet_i_solteq,
    formular_indsendt,
    tandklinik_registreret_i_solteq,
    handle_process_dashboard
)
from helpers import helper_functions, ats_functions

logger = logging.getLogger(__name__)

PROCESS_FLOW_MAP = {
    "--borger_fyldt_22": {
        "main": borger_fyldt_22.main,
        "process_step_name": "Borger fyldt 22 år",
        "enqueue_items": True,
    },
    "--faglig_vurdering_udfoert": {
        "main": faglig_vurdering_udfoert.main,
        "process_step_name": "Faglig vurdering udført",
        "enqueue_items": False,
    },
    "--aftale_oprettet_i_solteq": {
        "main": aftale_oprettet_i_solteq.main,
        "process_step_name": "Aftale oprettet i Confirma",
        "enqueue_items": True,
    },
    "--formular_indsendt": {
        "main": formular_indsendt.main,
        "process_step_name": "Formular indsendt",
        "enqueue_items": True,
    },
    "--tandklinik_registreret_i_solteq": {
        "main": tandklinik_registreret_i_solteq.main,
        "process_step_name": "Tandklinik registreret i Confirma",
        "enqueue_items": True,
    },
}


def process_item(item_data: dict, item_reference: str):
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
            enqueue_items = proc_config.get("enqueue_items")

            if arg != "--borger_fyldt_22":
                handle_process_dashboard.main(status="running", item_reference=item_reference, process_name=process_name)

            data, references = proc_config["main"](item_data=item_data)

            handle_process_dashboard.main(status="success", item_reference=item_reference, process_name=process_name)

            if enqueue_items:
                _enqueue_items(data, references)

            break

    except BusinessError as be:
        logger.info(f"BusinessError: {be}")

        if proc_config.get("use_dashboard", False):
            handle_process_dashboard.main(status="failed", item_reference=item_reference, process_name=process_name)

        raise

    except Exception as e:
        logger.exception(f"Unexpected error while processing item: {e}")

        if proc_config.get("use_dashboard", False):
            handle_process_dashboard.main(status="failed", item_reference=item_reference, process_name=process_name)

        raise


def _enqueue_items(data, references):
    """
    Enqueues each (reference, data) pair to the next workqueue, avoiding duplicates.

    Used for standard flows where further processing is required in later steps.
    """

    workqueue = helper_functions.fetch_next_workqueue()

    existing_refs = {str(r) for r in ats_functions.get_workqueue_items(workqueue)}

    for ref, d in zip(references, data, strict=True):
        ref = str(ref or "")

        print("debug print")
        import pprint
        pprint.pprint(d)  # or just print(d)
        if ref and ref not in existing_refs:
            workqueue.add_item({"item": {"reference": ref, "data": d}}, ref)
