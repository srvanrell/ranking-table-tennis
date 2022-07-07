from typing import List

import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe

from ranking_table_tennis.configs import cfg


def upload_sheet_from_df(
    spreadsheet_id: str,
    sheet_name: str,
    df: pd.DataFrame,
    headers: List[str] = None,
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
    print("<<<Saving", sheet_name, "in", spreadsheet_id, sep="\t")
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

    except ConnectionError:
        print("<<<FAILED to upload", sheet_name, "in", spreadsheet_id, sep="\t")


def load_and_upload_sheet(filename: str, sheet_name: str, spreadsheet_id: str) -> None:
    df = pd.read_excel(filename, sheet_name, index_col=None, header=None, na_filter=False)
    upload_sheet_from_df(spreadsheet_id, sheet_name, df, include_df_headers=False)  # index is pid


def create_n_tour_sheet(spreadsheet_id: str, tid: str) -> None:
    """
    Create sheet corresponding to n_tour tournament by duplication of the first-tournament sheet.
    A new sheeet is created in given spreadsheet_id as follows:
    1- first-tournament sheet is duplicated
    2- Two replacements are performed in the new sheet, considering n_tour.
       For example, if n_tour=4, value of A1 cell and sheet title will change
       'Tournament 01'->'Tournament 04'
    :param spreadsheet_id: spreadsheet where duplication will be performed
    :param tid: tournament to create
    :return: None
    """
    first_key = f"{cfg.labels.Tournament} 01"
    replacement_key = f"{cfg.labels.Tournament} {tid[-2:]}"

    try:
        gc = _get_gc()
        wb = gc.open_by_key(spreadsheet_id)
        sheetname_listed = [ws.title for ws in wb.worksheets() if first_key in ws.title]
        if sheetname_listed:
            sheetname = sheetname_listed[0]
            new_sheetname = sheetname.replace(first_key, replacement_key)
            if new_sheetname in [ws.title for ws in wb.worksheets()]:
                out_ws = wb.worksheet(new_sheetname)
                wb.del_worksheet(out_ws)
            ws = wb.worksheet(sheetname)
            dup_ws = wb.duplicate_sheet(ws.id, new_sheet_name=new_sheetname)
            dup_cell_value = dup_ws.acell("A1", value_render_option="FORMULA").value
            dup_ws.update_acell("A1", dup_cell_value.replace(first_key, replacement_key))
            print("<<<Creating", new_sheetname, "from", sheetname, "in", spreadsheet_id, sep="\t")
        else:
            print("FAILED TO DUPLICATE", first_key, "do not exist in", spreadsheet_id, sep="\t")

    except ConnectionError:
        print("<<<Connection Error. FAILED TO DUPLICATE", first_key, "in", spreadsheet_id, sep="\t")


def publish_to_web(tid: str, show_on_web=False) -> None:
    if show_on_web:
        for spreadsheet_id in cfg.io.published_on_web_spreadsheets_id:
            create_n_tour_sheet(spreadsheet_id, tid)


def _in_colab() -> bool:
    # Verify if it is running on colab
    try:
        import google.colab  # noqa

        _in_colab = True
    except ModuleNotFoundError:
        _in_colab = False

    return _in_colab


def _get_gc() -> gspread.Client:
    try:
        if _in_colab():
            from google.colab import auth

            auth.authenticate_user()
            from oauth2client.client import GoogleCredentials  # type: ignore

            gc = gspread.authorize(GoogleCredentials.get_application_default())
        else:
            gc = gspread.oauth()
    except FileNotFoundError:
        print("The .json key file has not been configured. Upload will fail.")
        raise ConnectionError
    # except OSError:
    #     print("Connection failure. Upload will fail.")

    return gc


def _get_ws_from_spreadsheet(sheet_name: str, spreadsheet_id: str):
    gc = _get_gc()
    wb = gc.open_by_key(spreadsheet_id)
    if sheet_name not in [ws.title for ws in wb.worksheets()]:
        wb.add_worksheet(sheet_name, rows=1, cols=1)
    ws = wb.worksheet(sheet_name)

    return ws
