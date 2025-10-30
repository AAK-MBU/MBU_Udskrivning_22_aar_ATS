"""Module for fetching patients that have turned 22 as of today's date"""

import os

import json
import urllib.parse

import pandas as pd

from sqlalchemy import create_engine

from mbu_rpa_core.exceptions import BusinessError

DBCONNECTIONSTRINGPROD = os.getenv("DBCONNECTIONSTRINGPROD")


def main(item_data: dict):
    """Main function to execute the script."""

    data = []
    references = []

    citizen_cpr = item_data.get("cpr")

    new_clinic_ydernummer = ""

    print("before calling find citizen")
    citizen_formulars = _find_citizen_formulars(cpr=citizen_cpr)

    for citizen_submission in citizen_formulars:
        form_data = citizen_submission.get("data")

        if form_data.get("borger_cpr_nummer_manuelt") == citizen_cpr:
            if form_data.get("tandlaege_fremkommer_ikke_i_listen") == "0":
                new_clinic_ydernummer = form_data.get("vaelg_tandlaege_api").split("||")[-1].strip()

            else:
                new_clinic_ydernummer = form_data.get("tandlaege_ydernummer_manuelt")

    # if new_clinic_ydernummer != "":
    if new_clinic_ydernummer == "":
        references.append(citizen_cpr)
        data.append(item_data)

    else:
        raise BusinessError("Borger har ikke endnu ikke en besvarelse, der indikerer ønsket tandklinik")

    return data, references


def _find_citizen_formulars(cpr: str = "") -> list[dict]:
    """
    Find any formular submission where the citizen's cpr is in the form_data
    """

    query = """
        SELECT
            [form_id],
            [form_sid],
            [form_type],
            [form_source],
            [form_submitted_date],
            [destination_system],
            [status],
            [response],
            [documented_date],
            [form_data],
            [last_time_modified]
        FROM
            [RPA].[journalizing].[view_Journalizing]
        WHERE
            form_type in ('udskrivning_22_aar_tandpleje_for', 'udskrivning_22_aar_privat_tandkl')
            AND form_data like ?
        ORDER BY
            form_submitted_date DESC
    """

    query_params = (f"%{cpr}%",)

    # Create SQLAlchemy engine
    encoded_conn_str = urllib.parse.quote_plus(DBCONNECTIONSTRINGPROD)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={encoded_conn_str}")

    try:
        df = pd.read_sql(sql=query, con=engine, params=query_params)

    except Exception as e:
        print("Error during pd.read_sql:", e)

        raise

    if df.empty:
        print("Citizen has no formular")

        return []

    extracted_data = []

    for _, row in df.iterrows():
        try:
            parsed = json.loads(row["form_data"])

            if "purged" not in parsed:
                extracted_data.append(parsed)

        except json.JSONDecodeError:
            print("Invalid JSON in form_data, skipping row.")

    return extracted_data
