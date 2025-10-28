"""Helper functions"""

import sys
import os
import logging
import requests

from automation_server_client import AutomationServer
from automation_server_client._models import Workqueue

logger = logging.getLogger(__name__)

ATS_TOKEN = os.getenv("ATS_TOKEN")
ATS_URL = os.getenv("ATS_URL")


def fetch_next_workqueue(faglig_vurdering: bool = False):
    """
    Helper function to fetch the next workqueue in the overall process flow
    """

    next_workqueue_name = ""

    if "--borger_fyldt_22" in sys.argv:
        if faglig_vurdering:
            next_workqueue_name = "faglig_vurdering_udfoert"

        else:
            next_workqueue_name = "aftale_oprettet_i_solteq"

    elif "--aftale_oprettet_i_solteq" in sys.argv:
        next_workqueue_name = "formular_indsendt"

    elif "--formular_indsendt" in sys.argv:
        next_workqueue_name = "tandklinik_registreret_i_solteq"

    else:
        print("ERROR: NO VALID SYS ARGUMENT GIVEN!")
        sys.exit()

    headers = {"Authorization": f"Bearer {ATS_TOKEN}"}

    full_url = f"{ATS_URL}/workqueues/by_name/tan.udskrivning22.{next_workqueue_name}"

    response_json = requests.get(full_url, headers=headers, timeout=60).json()
    workqueue_id = response_json.get("id")

    os.environ["ATS_WORKQUEUE_OVERRIDE"] = str(workqueue_id)  # override it
    ats = AutomationServer.from_environment()
    workqueue = ats.workqueue()

    return workqueue


def fetch_workqueue_workitems(workqueue: Workqueue):
    """
    Helper function to fetch workitems for a given workqueue
    """

    ats_headers = {"Authorization": f"Bearer {ATS_TOKEN}"}

    full_url = f"{ATS_URL}/workqueues/{workqueue.id}/items"

    response_json = requests.get(full_url, headers=ats_headers, timeout=60).json()

    workitems = response_json.get("items")

    return workitems
