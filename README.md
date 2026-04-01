# 📍 Places Tracker

A lightweight automation that turns Telegram messages into a structured Google Sheets travel wishlist. When you or your SO spot an interesting place, just send the name to a Telegram bot — it gets classified and logged automatically.

---

## How It Works

```
You / SO sends place name → Telegram Bot → Python Script → Claude API → Google Sheets
```

1. Either of you sends a place name to the Telegram bot (e.g. `Noma, Copenhagen` or just `Noma Copenhagen`)
2. The Python script picks it up via Telegram polling — catching any messages missed while the PC was off
3. Claude classifies the place and extracts structured details
4. The result is written to the correct tab in Google Sheets

---

## Google Sheets Structure

The sheet has **2 tabs:**

| Tab | What goes here | Example |
|-----|---------------|---------|
| 🏙️ **Foreign Cities** | An entire city recommended as a destination | Lisbon, Copenhagen, Kyoto |
| 📌 **Foreign Things To Do** | A specific place within a city | Noma Restaurant, Sagrada Família, Tiger's Nest hike |

### Columns (both tabs)

| Date Requested | Date Processed | Place Name | City | Country | Peak Season | Good & Cheaper | Avoid | Status | Notes |
|----------------|----------------|-----------|------|---------|-------------|----------------|-------|--------|-------|
| Telegram msg date | Processing date | Extracted | Extracted | Extracted | e.g. Jun–Aug | e.g. Apr–May | e.g. Nov–Feb | ⚠️ if unclear | Manual |

- **Peak Season** — months when the place is in its prime but busiest/most expensive
- **Good & Cheaper** — still a good time to visit, less crowded, potentially cheaper
- **Avoid** — months you should not visit (bad weather, closures, etc.)
- **Notes** — left empty; filled in manually
- **Status** — ⚠️ needs review if Claude can't confidently identify the place

If Claude can't confidently identify the place, it logs it with a **⚠️ needs review** status and leaves the row for manual completion.

**Duplicates:** Before writing, the bot checks if the place already exists in the sheet. If it does, it skips the entry and replies to let you know.

**Bot replies:**
- Success → e.g. "Added Noma to Foreign Things To Do"
- Duplicate → lets you know it already exists
- Local place → "Local places aren't supported yet"
- Unclear → "Added with ⚠️ needs review"
- Error → tells you something went wrong, what failed (e.g. Claude API / Google Sheets), and to retry
- Multiple places detected → asks you to send one place at a time

---

## Classification Logic

Claude follows these rules:

- **Place in Serbia** → not logged; bot replies that local places aren't supported yet
- **Whole foreign country** (e.g. "Japan") → Foreign Cities tab, assumes the capital as the destination
- **Whole foreign city as a destination** → Foreign Cities tab
- **Specific place within a foreign city** → Foreign Things To Do tab
- **Can't identify the place** → Foreign Things To Do tab, flagged as ⚠️ needs review

> "Foreign" = anything outside Serbia (i.e. would need a passport to visit).

---

## Tech Stack

| Component | Tool | Why |
|-----------|------|-----|
| Message interface | Telegram Bot | Open API, easy to forward to |
| Message handling | Python + `python-telegram-bot` | Polling mode for built-in catch-up queue |
| LLM | Claude API (Anthropic) | Starting point — easy to swap for a local model later |
| Output | Google Sheets API | Auto-syncs to mobile for both of you |

> **Planned:** Swap Claude API for a local Ollama model (Mistral 7B or Qwen 2.5 7B) once the workflow is stable. Eventually migrate to a Raspberry Pi or always-on machine.

---

## Authorized Users

Only two Telegram user IDs are whitelisted — yours and your SO's. Messages from anyone else are silently ignored.

---

## Setup

### Prerequisites

- Python 3.10+
- A Telegram bot token (via [@BotFather](https://t.me/BotFather))
- An Anthropic API key
- Google Sheets API credentials

### 1. Clone & install dependencies

```bash
git clone https://github.com/vhristov97/travel-backlog-automation.git
cd travel-backlog-automation
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_USER_ID_1=your_telegram_id
TELEGRAM_USER_ID_2=her_telegram_id
GOOGLE_SHEETS_ID=your_sheet_id
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

### 3. Set up Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → enable Google Sheets API
3. Create a Service Account → download credentials JSON
4. Save as `credentials.json` in the project root
5. Share your Google Sheet with the service account email

### 4. Run

```bash
python main.py
```

The script will poll Telegram continuously and process any messages — including ones sent while it was offline.

> **Goal:** Eventually the entire stack will start with a single command (e.g. `docker compose up` or `./start.sh`), suitable for running on an always-on machine.

---

## Sending Places

Just message the bot with a place name. The more detail the better but it's not required:

```
Noma Copenhagen          ← works
Noma, Copenhagen         ← works
Noma Restaurant Copenhagen Denmark  ← works great
Lisbon                   ← goes to Cities tab
```

If Claude can't figure out the place from the name alone it'll still log it — just flagged for you to fill in manually.

---

## Roadmap

- [ ] **Phase 2:** Swap Claude API for a local Ollama model (Mistral 7B or Qwen 2.5 7B)
- [ ] **Phase 3:** Orchestrate via Docker or bash scripts so the whole thing starts with a single command
- [ ] **Phase 4:** Migrate to an always-on machine (Raspberry Pi or similar) — same single-command start
- [ ] **Phase 5:** Video frame analysis — extract place names from Instagram Shorts that don't mention the place in the caption
- [ ] **Phase 6:** Local categories — split into city-specific and rest-of-country tabs

---

## Project Structure

```
travel-backlog-automation/
├── main.py              # Entry point, Telegram polling loop
├── bot.py               # Telegram message handling & user auth
├── llm.py               # Claude API integration & prompt logic
├── sheets.py            # Google Sheets read/write
├── classifier.py        # Place classification logic
├── requirements.txt
├── credentials.json     # Google service account (not committed)
└── .env                 # Secrets (not committed)
```
