"""Module to handle item processing"""

import sys
import logging

from mbu_rpa_core.exceptions import BusinessError

from processes.sub_processes import (
    borger_fyldt_22,
    faglig_vurdering_udfoert,
    aftale_oprettet_i_solteq,
    formular_indsendt,
    tandklinik_registreret_i_solteq
)

from helpers import helper_functions, ats_functions

logger = logging.getLogger(__name__)

PROCESS_MAP = {
    "--borger_fyldt_22": borger_fyldt_22.main,
    "--aftale_oprettet_i_solteq": aftale_oprettet_i_solteq.main,
    "--formular_indsendt": formular_indsendt.main,
    "--tandklinik_registreret_i_solteq": tandklinik_registreret_i_solteq.main,
}


def process_item(item_data: dict, item_reference: str):
    """Function to handle item processing"""
    assert item_data, "Item data is required"
    assert item_reference, "Item reference is required"

    if "--journal_faerdig" in sys.argv:
        print()

        # SEND PROCESS DASHBOARD API UPDATE

        return

    if "--faglig_vurdering_udfoert" in sys.argv:
        try:
            faglig_vurdering_udfoert.main(item_data=item_data, item_reference=item_reference)

        except BusinessError as be:
            logger.info(f"BusinessError: {be}")

            raise

        except Exception as e:
            logger.exception(f"Unexpected error while processing item: {e}")

            raise

        # SEND PROCESS DASHBOARD API UPDATE

        return

    data, references = [], []

    for arg, func in PROCESS_MAP.items():
        if arg in sys.argv:
            try:
                data, references = func(item_data=item_data, item_reference=item_reference)

            except BusinessError as be:
                logger.info(f"BusinessError: {be}")

                raise

            except Exception as e:
                logger.exception(f"Unexpected error while processing item: {e}")

                raise

            break

    workqueue = helper_functions.fetch_next_workqueue(faglig_vurdering=False)

    queue_references = {str(r) for r in ats_functions.get_workqueue_items(workqueue)}

    items = [
        {"reference": ref, "data": d} for ref, d in zip(references, data, strict=True)
    ]

    for item in items:
        reference = str(item.get("reference") or "")

        if reference and reference not in queue_references:
            data = {"item": item}

            workqueue.add_item(data, reference)

    if "--borger_fyldt_22" in sys.argv:
        faglig_vurdering_workqueue = helper_functions.fetch_next_workqueue(faglig_vurdering=True)

        queue_references = {str(r) for r in ats_functions.get_workqueue_items(faglig_vurdering_workqueue)}

        for item in items:
            reference = str(item.get("reference") or "")

            if reference and reference not in queue_references:
                data = {"item": item}

                faglig_vurdering_workqueue.add_item(data, reference)
