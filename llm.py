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
  "avoid": {"start": 1, "end": 12}
}

Rules:
- IMPORTANT: Any place in Serbia (city, venue, attraction) MUST be classified as "local". This includes Belgrade, Novi Sad, Niš, and any other Serbian location.
- "Foreign" means anything outside Serbia.
- If a country name is given (e.g. "Japan"), classify as "foreign_city" and use the capital as the city.
- If classification is "local", "unclear", or "multiple", still include whatever fields you can. Use null for unknown fields.
- For season fields, use null if you cannot determine the season (e.g. for unclear places).
- For "multiple", set place_name/city/country to null.
- The three season ranges must not overlap. A month can only belong to one category: peak_season, good_cheaper, or avoid.
"""


def classify_place(text):
    """Send a place name to Claude and return the parsed classification."""
    response = client.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())
