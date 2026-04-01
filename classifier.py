import calendar
from datetime import datetime, timezone

from llm import classify_place
from sheets import (
    TAB_FOREIGN_CITIES,
    TAB_FOREIGN_THINGS,
    add_place,
    check_duplicate,
)

MONTH_ABBR = {i: calendar.month_abbr[i] for i in range(1, 13)}


def _format_months(season):
    """Format a season dict like {"start": 6, "end": 8} into "Jun–Aug"."""
    if not season or season.get("start") is None or season.get("end") is None:
        return ""
    return f"{MONTH_ABBR[season['start']]}–{MONTH_ABBR[season['end']]}"


def _build_row(data, message_date):
    """Build a sheet row from LLM data and the Telegram message date."""
    date_requested = message_date.strftime("%Y-%m-%d")
    date_processed = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return [
        date_requested,
        date_processed,
        data.get("place_name") or "",
        data.get("city") or "",
        data.get("country") or "",
        _format_months(data.get("peak_season")),
        _format_months(data.get("good_cheaper")),
        _format_months(data.get("avoid")),
        "",  # Status (set below if needed)
        "",  # Notes (always empty)
    ]


def process_place(text, message_date):
    """Classify a place and write it to the sheet. Returns a reply string for the user."""
    data = classify_place(text)
    classification = data.get("classification")

    if classification == "multiple":
        return "It looks like you sent more than one place. Please send one at a time."

    if classification == "local":
        return "Local places aren't supported yet."

    place_name = data.get("place_name") or text

    # Check for duplicates
    existing_tab = check_duplicate(place_name)
    if existing_tab:
        return f'"{place_name}" is already in {existing_tab}.'

    # Determine target tab
    if classification == "foreign_city":
        tab = TAB_FOREIGN_CITIES
    else:
        tab = TAB_FOREIGN_THINGS

    row = _build_row(data, message_date)

    # Set status for unclear places
    if classification == "unclear":
        row[8] = "⚠️ needs review"

    add_place(tab, row)

    if classification == "unclear":
        return f'Added "{place_name}" to {tab} with ⚠️ needs review.'

    return f'Added "{place_name}" to {tab}.'
