"""Helper functions"""

import os
import logging

from mbu_process_dashboard_shared_components.process_dashboard_client import ProcessDashboardClient
from mbu_process_dashboard_shared_components import (
    process_run,
    process_step_run
)

logger = logging.getLogger(__name__)

API_ADMIN_TOKEN = os.getenv("API_ADMIN_TOKEN")
CLIENT = ProcessDashboardClient(api_admin_token=API_ADMIN_TOKEN)


def handle_dashboard_run_creation(process_name: str, meta: dict):
    """
    Method for handling the creation of new process dashboard runs
    """

    process_run.create_dashboard_run(client=CLIENT, process_name=process_name, meta=meta)


def handle_process_dashboard(status: str, item_reference: str, process_step_name: str, failure: Exception | None = None):
    """
    Method for handling updating the process dashboard
    """

    status_update_data = {
        "status": status
    }

    citizen_cpr = item_reference

    logger.info("before get_step_run_id_for_process_step_cpr() ...")

    step_run_id = process_step_run.get_step_run_id_for_process_step_cpr(client=CLIENT, process_name="Udskrivning 22 år", step_name=process_step_name, cpr=citizen_cpr)

    if failure:
        step_run_update_data = process_step_run.build_step_run_update(status=status, failure=failure)

        status_update_data["failure"] = failure

    else:
        step_run_update_data = process_step_run.build_step_run_update(status=status)

    logger.info("before update_dashboard_step_run_by_id() ...")

    updated_step_run_data, status_code = process_step_run.update_dashboard_step_run_by_id(client=CLIENT, step_run_id=step_run_id, update_data=step_run_update_data)

    return updated_step_run_data, status_code
