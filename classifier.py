import calendar
import logging
from datetime import datetime, timezone

from llm import classify_place, get_city_attractions
from sheets import (
    TAB_FOREIGN_CITIES,
    TAB_FOREIGN_THINGS,
    add_place,
    check_duplicate,
)

logger = logging.getLogger(__name__)

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


def _write_city(data, message_date, source_text, status):
    """Build and append a Foreign Cities row. Returns True on success."""
    row = _build_city_row(data, message_date, source_text)
    row[8] = status
    add_place(TAB_FOREIGN_CITIES, row)
    return True


def _write_thing(data, message_date, source_text, status):
    """Build and append a Foreign Things To Do row. Returns True on success."""
    row = _build_things_row(data, message_date, source_text)
    row[7] = status
    add_place(TAB_FOREIGN_THINGS, row)
    return True


def _auto_add_attractions(city, country, message_date):
    """Fan out from a city write: fetch iconic attractions and add them to
    Foreign Things To Do. Skips duplicates. Failures are logged and swallowed
    so the primary reply is never broken. Returns the list of added names.
    """
    if not city:
        return []

    try:
        attractions = get_city_attractions(city, country)
    except Exception:
        logger.exception("Failed to fetch attractions for %s", city)
        return []

    added = []
    source_text = f'auto: from "{city}"'
    for attraction in attractions:
        place_name = attraction.get("place_name")
        if not place_name:
            continue
        try:
            if check_duplicate(TAB_FOREIGN_THINGS, place_name):
                continue
            data = {
                "place_name": place_name,
                "city": city,
                "country": country,
                "price_eur": attraction.get("price_eur"),
                "description": attraction.get("description"),
            }
            _write_thing(data, message_date, source_text, "✅ Valid")
            added.append(place_name)
        except Exception:
            logger.exception("Failed to auto-add attraction %s", place_name)
    return added


def _auto_add_city(city, message_date, source_thing):
    """Fan out from a thing-to-do write: ensure the parent city exists in
    Foreign Cities. No secondary cascade — does NOT trigger attractions.
    Returns the city name on success, None otherwise.
    """
    if not city:
        return None

    try:
        if check_duplicate(TAB_FOREIGN_CITIES, city):
            return None
        city_data = classify_place(city)
    except Exception:
        logger.exception("Failed to auto-classify city %s", city)
        return None

    if isinstance(city_data, list):
        return None
    if city_data.get("classification") != "foreign_city":
        return None
    if (city_data.get("city") or "").strip().lower() != city.strip().lower():
        return None

    source_text = f'auto: from "{source_thing}"'
    try:
        _write_city(city_data, message_date, source_text, "✅ Valid")
    except Exception:
        logger.exception("Failed to auto-add city %s", city)
        return None
    return city


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

    status = "⚠️ needs review" if classification == "unclear" else "✅ Valid"

    if tab == TAB_FOREIGN_CITIES:
        _write_city(data, message_date, text, status)
    else:
        _write_thing(data, message_date, text, status)

    if classification == "unclear":
        return f'Added to {tab} with ⚠️ needs review.'

    reply = f'Added "{dedup_value}" to {tab}.'

    # Cascade: link the two tabs (one hop only).
    if classification == "foreign_city":
        added = _auto_add_attractions(
            data.get("city"), data.get("country"), message_date
        )
        if added:
            reply += (
                f' Also added {len(added)} attraction'
                f'{"s" if len(added) != 1 else ""}: {", ".join(added)}.'
            )
    elif classification == "foreign_place":
        added_city = _auto_add_city(data.get("city"), message_date, dedup_value)
        if added_city:
            reply += f' Also added "{added_city}" to Foreign Cities.'

    return reply
