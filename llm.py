import json

import anthropic

import config

client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a travel place classifier. Given a place name or description, you must:

1. Determine the classification:
   - "local" — the place is in Serbia
   - "foreign_city" — a whole foreign city as a travel destination, OR a whole foreign country (use the capital city)
   - "foreign_place" — a specific place/venue/attraction within a foreign city
   - "unclear" — you cannot confidently identify the place
   - "multiple" — the message contains more than one place

2. Extract structured details about the place.

3. For season data, return month numbers (1=January, 12=December).

You MUST respond with valid JSON only, no other text. Use this exact schema:

{
  "classification": "foreign_city | foreign_place | local | unclear | multiple",
  "place_name": "the name of the place",
  "city": "the city name (use capital if a country was given)",
  "country": "the country name",
  "peak_season": {"start": 1, "end": 12},
  "good_cheaper": {"start": 1, "end": 12},
  "price_level": "€ | €€ | €€€",
  "price_eur": "~€12 | Free | null",
  "days_needed": {"min": 3, "max": 5},
  "description": "short description and recommendations"
}

Rules:
- IMPORTANT: Any place in Serbia (city, venue, attraction) MUST be classified as "local". This includes Belgrade, Novi Sad, Niš, and any other Serbian location.
- "Foreign" means anything outside Serbia.
- If a country name is given (e.g. "Japan"), classify as "foreign_city" and use the capital as the city.
- If classification is "local", "unclear", or "multiple", still include whatever fields you can. Use null for unknown fields.
- For season fields, use null if you cannot determine the season (e.g. for unclear places).
- For "multiple", set place_name/city/country to null.
- The two season ranges must not overlap. A month can only belong to one category: peak_season or good_cheaper.
- price_level: only for "foreign_city" classification. Use "€" for cheap cities, "€€" for mid-range, "€€€" for expensive, relative to global city costs. Use null for other classifications.
- price_eur: only for "foreign_place" classification. Approximate price in EUR (e.g. "~€17" for a museum ticket, "~€25" for an average restaurant meal). Use "Free" if the place is free to visit. Use null if you have no reliable information — never fabricate a price.
- days_needed: only for "foreign_city" classification. Estimate the typical number of days a traveller needs to see the city well. min and max may be equal (e.g. {"min": 1, "max": 1} for a one-day stop). Use null for non-city classifications or if you cannot estimate.
- description: a brief description of the place with travel recommendations. 1-2 sentences.
"""


ATTRACTIONS_SYSTEM_PROMPT = """You are a travel attractions recommender. Given a city (and country), return its top attractions, each tagged with a notability tier so downstream code can filter strictly.

You MUST respond with valid JSON only, no other text. Use this exact schema:

{
  "attractions": [
    {
      "place_name": "the attraction's common English name",
      "notability": "world_famous | nationally_famous | local",
      "price_eur": "~€17 | Free | null",
      "description": "short description and recommendations"
    }
  ]
}

Notability tiers — be strict, most attractions are NOT world_famous:
- "world_famous": a random well-travelled foreigner on another continent would recognise the name. Eiffel Tower, Colosseum, Taj Mahal, Machu Picchu, Statue of Liberty, Louvre, Acropolis, Great Wall. Typical cities have 0-3 of these; Paris/Rome/Tokyo have 4-5.
- "nationally_famous": most residents of that country know it, but foreigners outside the region usually do not. Smaller castles, regional cathedrals, national museums, famous markets, well-known parks.
- "local": interesting to visitors already in the city, but not a draw on its own. Neighbourhoods, alternative scenes, specific restaurants, small galleries.

Rules:
- Return up to 8 candidates total across all tiers. Do not pad — if a city has only 1 world_famous and 2 nationally_famous sites, return 3 items.
- STRICTLY EXCLUDE: whole districts, neighbourhoods, old towns, entire streets, general areas, or the city itself. Only specific venues, landmarks, or sites.
- Never fabricate attractions.
- price_eur: approximate price in EUR to visit/enter (e.g. "~€17"). Use "Free" if free to visit. Use null if you have no reliable information — never fabricate a price.
- description: 1-2 sentences, brief description with travel recommendations.
"""

# Filtering happens in code, not in the prompt, because LLMs anchor on the cap.
# If a city has any world_famous landmarks, we take up to MAX_WORLD_FAMOUS of them.
# Otherwise we fall back to the top MAX_FALLBACK_NATIONAL nationally_famous
# entries, so smaller cities (Ljubljana, Tallinn) still get their best-known sites.
MAX_WORLD_FAMOUS = 5
MAX_FALLBACK_NATIONAL = 3


def _parse_json_response(raw):
    """Strip code fences and parse the response as JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def classify_place(text):
    """Send a place name to Claude and return the parsed classification."""
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )

    return _parse_json_response(response.content[0].text)


def get_city_attractions(city, country):
    """Ask Claude for up to 5 iconic attractions in a given city.

    Returns a list of dicts with keys: place_name, price_eur, description.
    Returns [] if the response is malformed.
    """
    user_msg = f"{city}, {country}" if country else city
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=800,
        system=ATTRACTIONS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )

    data = _parse_json_response(response.content[0].text)
    attractions = data.get("attractions")
    if not isinstance(attractions, list):
        return []

    # Filter by tier. Prefer world_famous; if a city has none, fall back to
    # nationally_famous so small cities still get their best-known sites.
    world_famous = [
        a for a in attractions
        if isinstance(a, dict) and a.get("notability") == "world_famous"
    ]
    if world_famous:
        return world_famous[:MAX_WORLD_FAMOUS]

    national = [
        a for a in attractions
        if isinstance(a, dict) and a.get("notability") == "nationally_famous"
    ]
    return national[:MAX_FALLBACK_NATIONAL]
