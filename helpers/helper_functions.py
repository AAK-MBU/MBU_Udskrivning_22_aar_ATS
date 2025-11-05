"""Helper functions"""

import os
import logging

import urllib.parse

import requests

import pandas as pd

from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

# !!! REMOVE !!! #
os.environ["ATS_TOKEN"] = os.getenv("ATS_TOKEN_DEV")
os.environ["ATS_URL"] = os.getenv("ATS_URL_DEV")
# !!! REMOVE !!! #

ATS_TOKEN = os.getenv("ATS_TOKEN")
ATS_URL = os.getenv("ATS_URL")

DBCONNECTIONSTRINGPROD = os.getenv("DBCONNECTIONSTRINGPROD")
DBCONNECTIONSTRINGDEV = os.getenv("DBCONNECTIONSTRINGDEV")


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

    return _fetch_single_row(query, (process_name,))


def handle_process_dashboard(status: str, item_reference: str, process_name: str, workitem_id: int = None):
    """
    Method for handling updating the process dashboard
    """

    citizen_cpr = item_reference

    process_step_run_id = _find_process_step_run_by_name_and_cpr(process_step_name=process_name, cpr=citizen_cpr).get("step_run_id")

    if process_name == "Tandklinik registreret i Solteq Tand" and status == "failed":
        _update_process_step_run_status_api(step_run_id=process_step_run_id, status=status, workitem_id=workitem_id)

    else:
        _update_process_step_run_status_api(step_run_id=process_step_run_id, status=status)


def _find_process_step_run_by_name_and_cpr(process_step_name: str, cpr: str) -> dict | None:
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

    return _fetch_single_row(query, ("Udskrivning 22 år", process_step_name, cpr))


def _fetch_single_row(query: str, params: tuple) -> dict | None:
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
        logger.info(f"Error during pd.read_sql: {e}")

        raise


def _update_process_step_run_status_api(step_run_id: int, status: str = "SUCCESSFUL", workitem_id: int = None):
    """
    Sends a PATCH request to update the status of a specific step run.
    """

    url = f"https://mbu-dashboard-api.adm.aarhuskommune.dk/api/v1/step-runs/{step_run_id}"

    headers = {
        "X-API-Key": os.getenv("API_ADMIN_TOKEN"),
        "Content-Type": "application/json"
    }

    if workitem_id:
        payload = {
            "status": status,
            "rerun_config": {
                "workitem_id": workitem_id
            }
        }

    else:
        payload = {
            "status": status,
        }

    try:
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

    except requests.RequestException as e:
        logger.info(f"Error updating step run {step_run_id} via API:", e)

        raise
