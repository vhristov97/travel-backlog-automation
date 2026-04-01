import gspread
from google.oauth2.service_account import Credentials

import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TAB_FOREIGN_CITIES = "Foreign Cities"
TAB_FOREIGN_THINGS = "Foreign Things To Do"

PLACE_NAME_COL = 3  # Column C (1-indexed)

_client = None


def _get_client():
    global _client
    if _client is None:
        creds = Credentials.from_service_account_file(
            "credentials.json", scopes=SCOPES
        )
        _client = gspread.authorize(creds)
    return _client


def _get_sheet():
    return _get_client().open_by_key(config.GOOGLE_SHEETS_ID)


def check_duplicate(place_name):
    """Check if a place already exists in either tab. Returns the tab name if found, None otherwise."""
    sheet = _get_sheet()
    for tab_name in [TAB_FOREIGN_CITIES, TAB_FOREIGN_THINGS]:
        worksheet = sheet.worksheet(tab_name)
        values = worksheet.col_values(PLACE_NAME_COL)
        for val in values[1:]:  # skip header
            if val.strip().lower() == place_name.strip().lower():
                return tab_name
    return None


def add_place(tab_name, row_data):
    """Append a row to the specified tab.

    row_data should be a list matching the column order:
    [Date Requested, Date Processed, Place Name, City, Country,
     Peak Season, Good & Cheaper, Avoid, Status, Notes]
    """
    sheet = _get_sheet()
    worksheet = sheet.worksheet(tab_name)
    worksheet.append_row(row_data, value_input_option="USER_ENTERED")
