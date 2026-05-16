# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Places Tracker** — a Telegram bot that classifies travel wishlist items (sent as plain text messages) using an LLM and logs them to Google Sheets. Two users are whitelisted (owner + SO). Runs via Telegram polling so it catches messages sent while offline. One place per message only.

## Architecture

```
Telegram polling → bot.py (auth + routing) → classifier.py → llm.py (Ollama or Claude) → sheets.py
```

- `main.py` — entry point, starts the polling loop
- `bot.py` — Telegram message handling, user whitelist enforcement
- `llm.py` — LLM calls and prompt logic; switches between Ollama (default) and Claude API based on `LLM_BACKEND`
- `classifier.py` — decides which Google Sheets tab a place belongs to (whole city vs. specific venue)
- `sheets.py` — Google Sheets read/write via service account

## Classification Rules

- Place in Serbia → not logged; bot replies local places aren't supported yet
- Whole foreign country (e.g. "Japan") → **Foreign Cities** tab, assumes the capital as the destination
- Whole foreign city as destination → **Foreign Cities** tab
- Specific place within a foreign city → **Foreign Things To Do** tab
- Unidentifiable place → **Foreign Things To Do** tab, `Status` = ⚠️ needs review

> "Foreign" = anything outside Serbia.

## Sheet Columns

**Foreign Cities:**
`Date Requested | Date Processed | Input | City | Country | Peak Season | Good & Cheaper | Price | Days Needed | Status | LLM Notes | Visited | Notes`

**Foreign Things To Do:**
`Date Requested | Date Processed | Input | Place Name | City | Country | Price | Status | LLM Notes | Visited | Notes`

- **Input** = raw Telegram message text
- **Price** = €/€€/€€€ for cities (relative global cost), ~€X for things to do (EUR estimate), "Free" if free, blank if unknown
- **Days Needed** = typical visit length for cities, e.g. `3–5 days` (cities only)
- **Status** = `✅ Valid` on success, `⚠️ needs review` if unclear
- **LLM Notes** = short description + recommendations from the LLM
- **Visited** and **Notes** = left empty (manual)
- Duplicates are checked before writing (city name for Cities, place name for Things To Do) — bot skips and notifies the user

## Bot Replies

- Success → confirms what was added and where
- Duplicate → tells you it already exists
- Local place → "Local places aren't supported yet"
- Unclear → "Added with ⚠️ needs review"
- Error → what failed (LLM / Google Sheets) and to retry
- Multiple places detected → asks to send one at a time

## Running

```bash
python main.py
```

Eventually the full stack will launch with a single command (`docker compose up` or `./start.sh`). Design with this in mind.

## Environment Variables (`.env`)

Common to both backends:

```
TELEGRAM_BOT_TOKEN
TELEGRAM_USER_ID_1
TELEGRAM_USER_ID_2
GOOGLE_SHEETS_ID
LLM_BACKEND=ollama   # or "claude"; defaults to "ollama" if unset
```

Ollama backend (production / desktop):

```
OLLAMA_HOST=http://localhost:11434   # default
OLLAMA_MODEL=qwen2.5:7b              # default
```

Claude backend (laptop / development without GPU):

```
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

`credentials.json` — Google service account key file, placed in project root.

## LLM

The bot supports two LLM backends behind a single interface in `llm.py`, switchable via `LLM_BACKEND`:

- **`ollama` (default)** — local Qwen 2.5 7B via Ollama on the desktop GPU. Uses Ollama's structured-output feature (`format=<JSON schema>`) for strict response shape. Requires Ollama ≥ 0.5.0 and `ollama pull qwen2.5:7b`.
- **`claude`** — Anthropic Claude Haiku via the `anthropic` SDK. Used on the laptop where there's no GPU. Output validated by Pydantic on the Python side.

Both backends share the same Pydantic response models (`ClassifyResponse`, `AttractionsResponse`), so output is shape-validated regardless of backend. `classifier.py` consumes plain dicts and is backend-agnostic.

## Roadmap Context

1. ~~Claude API~~ → **local Ollama model (current)** → single-command Docker/bash orchestration → audit log → automated problem reports → always-on machine (Raspberry Pi) → Instagram Shorts video frame analysis → local categories
