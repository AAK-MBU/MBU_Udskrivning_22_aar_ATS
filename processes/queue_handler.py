"""Module to hande queue population"""

import sys
import os
import asyncio
import json
import logging

from datetime import date
from dateutil.relativedelta import relativedelta

from automation_server_client import Workqueue

from mbu_dev_shared_components.solteqtand.database.db_handler import SolteqTandDatabase

from helpers import config

logger = logging.getLogger(__name__)

SOLTEQ_TAND_DB_CONN_STRING = os.getenv("DBCONNECTIONSTRINGSOLTEQTAND")


def retrieve_items_for_queue() -> list[dict]:
    """Function to populate queue with items for processing."""

    if "--borger_fyldt_22" not in sys.argv:
        return []

    data = []
    references = []

    prefix = (date.today() - relativedelta(years=22)).strftime("%d%m%y")

    db_handler = SolteqTandDatabase(conn_str=SOLTEQ_TAND_DB_CONN_STRING)

    citizen_in_age_range = _get_citizen_turning_22_today(db_handler, prefix)

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

        references.append(citizen_cpr)
        data.append({
            "patientId": patient_id,
            "cpr": citizen_cpr,
            "fullName": citizen_full_name,
            "clinic": citizen_clinic,
        })

    items = [
        {"reference": ref, "data": d} for ref, d in zip(references, data, strict=True)
    ]

    return items


def _get_citizen_turning_22_today(db_handler: SolteqTandDatabase, prefix: str):
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
            -- [tmtdata_prod].[dbo].[ACTIVE_PATIENTS]
            [tmtdata_prod].[dbo].[PATIENT]
        WHERE
            cpr LIKE ?
        ORDER BY
            firstName, lastName;
    """

    # like_param = f"{prefix}%"
    like_param = "1110109996"  # REMOVE

    # pylint: disable=protected-access
    return db_handler._execute_query(query, params=(like_param,))


def create_sort_key(item: dict) -> str:
    """
    Create a sort key based on the entire JSON structure.
    Converts the item to a sorted JSON string for consistent ordering.
    """
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


async def concurrent_add(workqueue: Workqueue, items: list[dict]) -> None:
    """
    Populate the workqueue with items to be processed.
    Uses concurrency and retries with exponential backoff.

    Args:
        workqueue (Workqueue): The workqueue to populate.
        items (list[dict]): List of items to add to the queue.

    Returns:
        None

    Raises:
        Exception: If adding an item fails after all retries.
    """
    sem = asyncio.Semaphore(config.MAX_CONCURRENCY)

    async def add_one(it: dict):
        reference = str(it.get("reference") or "")
        data = {"item": it}

        async with sem:
            for attempt in range(1, config.MAX_RETRIES + 1):
                try:
                    await asyncio.to_thread(workqueue.add_item, data, reference)
                    logger.info("Added item to queue with reference: %s", reference)
                    return True

                except Exception as e:
                    if attempt >= config.MAX_RETRIES:
                        logger.error(
                            "Failed to add item %s after %d attempts: %s",
                            reference,
                            attempt,
                            e,
                        )
                        return False

                    backoff = config.RETRY_BASE_DELAY * (2 ** (attempt - 1))

                    logger.warning(
                        "Error adding %s (attempt %d/%d). Retrying in %.2fs... %s",
                        reference,
                        attempt,
                        config.MAX_RETRIES,
                        backoff,
                        e,
                    )
                    await asyncio.sleep(backoff)

    if not items:
        logger.info("No new items to add.")
        return

    sorted_items = sorted(items, key=create_sort_key)
    logger.info(
        "Processing %d items sorted by complete JSON structure", len(sorted_items)
    )

    results = await asyncio.gather(*(add_one(i) for i in sorted_items))
    successes = sum(1 for r in results if r)
    failures = len(results) - successes

    logger.info(
        "Summary: %d succeeded, %d failed out of %d", successes, failures, len(results)
    )
