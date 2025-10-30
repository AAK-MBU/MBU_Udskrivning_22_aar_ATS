"""Helper functions"""

import sys
import os
import logging

import urllib.parse

import requests

import pandas as pd

from sqlalchemy import create_engine

from automation_server_client import AutomationServer

logger = logging.getLogger(__name__)

# !!! REMOVE !!! #
os.environ["ATS_TOKEN"] = os.getenv("ATS_TOKEN_DEV")
os.environ["ATS_URL"] = os.getenv("ATS_URL_DEV")
# !!! REMOVE !!! #

ATS_TOKEN = os.getenv("ATS_TOKEN")
ATS_URL = os.getenv("ATS_URL")

DBCONNECTIONSTRINGPROD = os.getenv("DBCONNECTIONSTRINGPROD")
DBCONNECTIONSTRINGDEV = os.getenv("DBCONNECTIONSTRINGDEV")


def fetch_next_workqueue(faglig_vurdering: bool = False):
    """
    Helper function to fetch the next workqueue in the overall process flow
    """

    next_workqueue_name = ""

    if faglig_vurdering:
        next_workqueue_name = "faglig_vurdering_udfoert"

    elif "--borger_fyldt_22" in sys.argv:
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


def find_process_id_by_name(process_name: str) -> dict | None:
    """
    Helper to fetch a process id by filtering for its name.
    """

    query = """
        SELECT
            created_at,
            updated_at,
            name,
            meta,
            id,
            retention_months,
            deleted_at
        FROM
            [ProcessVisualization].[dbo].[process]
        WHERE
            name = ?
    """

    return fetch_single_row(query, (process_name,))


def find_process_step_run_by_name_and_cpr(process_step_name: str, cpr: str) -> dict | None:
    """
    Helper to fetch process_step_run data for a given step name and citizen CPR,
    using the process name 'Udskrivning 22 år' instead of hardcoded process_id.
    """

    query = """
        SELECT
            step_run.created_at,
            step_run.updated_at,
            step_run.status,
            step_run.started_at,
            step_run.finished_at,
            step_run.failure,
            step_run.run_id,
            step_run.step_id,
            step_run.step_index,
            step_run.id AS step_run_id,
            step_run.can_rerun,
            step_run.rerun_config,
            step_run.rerun_count,
            step_run.max_reruns,
            step_run.deleted_at
        FROM
            [ProcessVisualization].[dbo].[process_step_run] AS step_run
        JOIN
            [ProcessVisualization].[dbo].[process_step] AS step
            ON step.id = step_run.step_id
        JOIN
            [ProcessVisualization].[dbo].[process_run] AS run
            ON run.id = step_run.run_id
        JOIN
            [ProcessVisualization].[dbo].[process] AS p
            ON p.id = step.process_id AND p.id = run.process_id
        WHERE
            p.name = ?
            AND step.name = ?
            AND run.entity_id = ?
            AND step_run.deleted_at is NULL
    """

    return fetch_single_row(query, ("Udskrivning 22 år", process_step_name, cpr))


def fetch_single_row(query: str, params: tuple) -> dict | None:
    """
    Helper to execute a SQL query and return the first row as dict, or None if empty.
    """

    # encoded_conn_str = urllib.parse.quote_plus(DBCONNECTIONSTRINGPROD)
    encoded_conn_str = urllib.parse.quote_plus(DBCONNECTIONSTRINGDEV)

    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={encoded_conn_str}")

    try:
        df = pd.read_sql(sql=query, con=engine, params=params)

        if df.empty:
            return None

        return df.iloc[0].to_dict()

    except Exception as e:
        print("Error during pd.read_sql:", e)

        raise


def update_process_step_run_status_api(step_run_id: int, status: str = "SUCCESSFUL"):
    """
    Sends a PATCH request to update the status of a specific step run.
    """

    url = f"https://mbu-dashboard-api.adm.aarhuskommune.dk/api/v1/step-runs/{step_run_id}"

    headers = {
        "X-API-Key": os.getenv("API_ADMIN_TOKEN"),
        "Content-Type": "application/json"
    }

    payload = {
        "status": status,
    }

    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

    except requests.RequestException as e:
        print(f"Error updating step run {step_run_id} via API:", e)

        raise
