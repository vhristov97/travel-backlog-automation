import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TAB_FOREIGN_CITIES = "Foreign Cities"
TAB_FOREIGN_THINGS = "Foreign Things To Do"

DEDUP_COL = 4  # Column D (1-indexed) — City for Cities tab, Place Name for Things To Do tab

_client = None


def _get_client():
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
        _client = gspread.authorize(creds)
        _client.set_timeout(15) #seconds
    return _client


def _get_sheet():
    return _get_client().open_by_key(config.GOOGLE_SHEETS_ID)


def check_duplicate(tab_name, value):
    """Check if a value already exists in the dedup column of the given tab.

    For Foreign Cities, pass the city name.
    For Foreign Things To Do, pass the place name.
    Returns True if found, False otherwise.
    """
    sheet = _get_sheet()
    worksheet = sheet.worksheet(tab_name)
    values = worksheet.col_values(DEDUP_COL)
    for val in values[1:]:  # skip header
        if val.strip().lower() == value.strip().lower():
            return True
    return False


def add_place(tab_name, row_data):
    """Append a row to the specified tab."""
    sheet = _get_sheet()
    worksheet = sheet.worksheet(tab_name)
    worksheet.append_row(row_data, value_input_option="USER_ENTERED")
