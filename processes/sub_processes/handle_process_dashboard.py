"""
Module for handling process dashboard updates
"""

from helpers import helper_functions


DASHBOARD_MAP = {
    "--borger_fyldt_22": "Borger fyldt 22 år",
    "--faglig_vurdering_gennemført": "Faglig vurdering udført",  # NOT YET CREATED IN DB ! CHANGE !!!!!
    "--aftale_oprettet_i_solteq": "Aftale oprettet i Confirma",
    "--formular_indsendt": "Formular indsendt",
    "--tandklinik_registreret_i_solteq": "Tandklinik registreret i Confirma",
}


def main(status: str, item_reference: str, process_name: str):
    """
    Method for handling updating the process dashboard
    """

    citizen_cpr = item_reference

    process_step_run_id = helper_functions.find_process_step_run_by_name_and_cpr(process_step_name=process_name, cpr=citizen_cpr).get("step_run_id")

    helper_functions.update_process_step_run_status_api(step_run_id=process_step_run_id, status=status)
