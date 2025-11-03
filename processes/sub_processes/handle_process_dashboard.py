"""
Module for handling process dashboard updates
"""

from helpers import helper_functions


def main(status: str, item_reference: str, process_name: str, workitem_id: int = None):
    """
    Method for handling updating the process dashboard
    """

    citizen_cpr = item_reference

    process_step_run_id = helper_functions.find_process_step_run_by_name_and_cpr(process_step_name=process_name, cpr=citizen_cpr).get("step_run_id")

    if process_name == "Tandklinik registreret i Confirma" and status == "failed":
        helper_functions.update_process_step_run_status_api(step_run_id=process_step_run_id, status=status, workitem_id=workitem_id)

    helper_functions.update_process_step_run_status_api(step_run_id=process_step_run_id, status=status)
