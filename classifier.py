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


def _build_city_row(data, message_date, text):
    """Build a Foreign Cities row.

    Columns: Date Requested | Date Processed | Input | City | Country |
             Peak Season | Good & Cheaper | Price | Status | LLM Notes | Visited | Notes
    """
    date_requested = message_date.strftime("%Y-%m-%d")
    date_processed = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return [
        date_requested,
        date_processed,
        text,
        data.get("city") or "",
        data.get("country") or "",
        _format_months(data.get("peak_season")),
        _format_months(data.get("good_cheaper")),
        data.get("price_level") or "",
        "",  # Status (set by caller)
        data.get("description") or "",
        "",  # Visited (manual)
        "",  # Notes (manual)
    ]


def _build_things_row(data, message_date, text):
    """Build a Foreign Things To Do row.

    Columns: Date Requested | Date Processed | Input | Place Name | City | Country |
             Price | Status | LLM Notes | Visited | Notes
    """
    date_requested = message_date.strftime("%Y-%m-%d")
    date_processed = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    return [
        date_requested,
        date_processed,
        text,
        data.get("place_name") or "",
        data.get("city") or "",
        data.get("country") or "",
        data.get("price_eur") or "",
        "",  # Status (set by caller)
        data.get("description") or "",
        "",  # Visited (manual)
        "",  # Notes (manual)
    ]


def process_place(text, message_date):
    """Classify a place and write it to the sheet. Returns a reply string for the user."""
    data = classify_place(text)

    if isinstance(data, list):
        return "It looks like you sent more than one place. Please send one at a time."

    classification = data.get("classification")

    if classification == "multiple":
        return "It looks like you sent more than one place. Please send one at a time."

    if classification == "local" or (data.get("country") or "").lower() == "serbia":
        return "Local places aren't supported yet."

    # Determine target tab and dedup value
    if classification == "foreign_city":
        tab = TAB_FOREIGN_CITIES
        dedup_value = data.get("city")
    else:
        tab = TAB_FOREIGN_THINGS
        dedup_value = data.get("place_name")

    # Check for duplicates
    if dedup_value and check_duplicate(tab, dedup_value):
        return f'"{dedup_value}" is already in {tab}.'

    # Build tab-specific row
    if tab == TAB_FOREIGN_CITIES:
        row = _build_city_row(data, message_date, text)
        status_idx = 8
    else:
        row = _build_things_row(data, message_date, text)
        status_idx = 7

    # Set status
    if classification == "unclear":
        row[status_idx] = "⚠️ needs review"
    else:
        row[status_idx] = "✅ Valid"

    add_place(tab, row)

    if classification == "unclear":
        return f'Added to {tab} with ⚠️ needs review.'

    return f'Added "{dedup_value}" to {tab}.'
