import os

from dotenv import load_dotenv

load_dotenv()

REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_USER_ID_1",
    "TELEGRAM_USER_ID_2",
    "GOOGLE_SHEETS_ID",
    "ANTHROPIC_API_KEY",
]


def validate():
    missing = [var for var in REQUIRED_VARS if not os.getenv(var)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID_1 = int(os.getenv("TELEGRAM_USER_ID_1", "0"))
#TELEGRAM_USER_ID_2 = int(os.getenv("TELEGRAM_USER_ID_2", "0"))
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
