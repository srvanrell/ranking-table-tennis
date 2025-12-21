import json
import logging
import os
from datetime import datetime, timezone
from typing import List

import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe


logger = logging.getLogger(__name__)


def upload_sheet_from_df(
    spreadsheet_id: str,
    sheet_name: str,
    df: pd.DataFrame,
    headers: List[str] | None = None,
    include_index: bool = False,
    include_df_headers: bool = True,
) -> None:
    """
    Saves headers and df data into given sheet_name in spreadsheet_id.
    If sheet_name does not exist, it will be created.

    :param include_index: will upload DataFrame index as the first column. It is False by default.
    :param include_df_headers: will upload DataFrame column names as the first row.
        It is True by default.
    :param headers: This list will replace df column names and must have the same length.
    If headers are given, include_df_headers is turn to True.
    """
    logger.info("< Saving '%s' @ '%s'", sheet_name, spreadsheet_id)
    try:
        worksheet = _get_ws_from_spreadsheet(sheet_name, spreadsheet_id)

        df_headers = df.copy()
        if include_index:
            df_headers.reset_index(inplace=True)
        if headers:
            df_headers.columns = headers
            include_df_headers = True

        set_with_dataframe(
            worksheet,
            df_headers,
            resize=True,  # include_index=include_index,
            include_column_header=include_df_headers,
        )

    except PermissionError:
        logger.warn("!! Permission Error. FAILED to upload '%s' @ '%s'", sheet_name, spreadsheet_id)


def days_since_last_update(spreadsheet_id) -> int:
    try:
        gc = _get_gc()
        spreadsheet = gc.open_by_key(spreadsheet_id)
        last_update_time = spreadsheet.get_lastUpdateTime()
    except PermissionError:
        logger.warn("!! Permission Error. FAIL TO GET last updated time @ '%s'", spreadsheet_id)

    # Parse the ISO 8601 datetime string into a datetime at UTC
    last_update_utc = datetime.fromisoformat(last_update_time[:-1]).replace(tzinfo=timezone.utc)
    difference = datetime.now(timezone.utc) - last_update_utc

    return difference.days


def _get_gc() -> gspread.Client:
    gc = None

    try:
        github_secret_name = "GCP_SA_KEY"
        credentials_str = os.getenv(github_secret_name)
        if credentials_str:
            logger.debug("Loading GCP SA credentials from %s", github_secret_name)
            credentials_dict = json.loads(credentials_str)
            gc = gspread.service_account_from_dict(credentials_dict)
        else:
            logger.debug("Loading GCP SA credentials from standard path")
            gc = gspread.service_account()
    except FileNotFoundError:
        logger.warn(
            "!! The service account .json key file has not been configured. Upload might fail."
        )

    try:
        if gc is None:
            logger.debug("Loading GCP End User credentials from standard path")
            gc = gspread.oauth()
    except FileNotFoundError:
        logger.warn("!! The end user .json key file has not been configured. Upload might fail.")
    # except OSError:
    #     logger.warn("!!Connection failure. Upload will fail.")

    if gc is None:
        raise PermissionError("Cannot authenticate to read and write using gspread")

    return gc


def _get_ws_from_spreadsheet(sheet_name: str, spreadsheet_id: str):
    gc = _get_gc()
    wb = gc.open_by_key(spreadsheet_id)
    if sheet_name not in [ws.title for ws in wb.worksheets()]:
        wb.add_worksheet(sheet_name, rows=1, cols=1)
    ws = wb.worksheet(sheet_name)

    return ws
