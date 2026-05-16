import os

from dotenv import load_dotenv

load_dotenv()

SUPPORTED_BACKENDS = ("ollama", "claude")

BASE_REQUIRED_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_USER_ID_1",
    "TELEGRAM_USER_ID_2",
    "GOOGLE_SHEETS_ID",
]


def validate():
    if LLM_BACKEND not in SUPPORTED_BACKENDS:
        raise EnvironmentError(
            f"Invalid LLM_BACKEND '{LLM_BACKEND}'. "
            f"Must be one of: {', '.join(SUPPORTED_BACKENDS)}"
        )

    required = list(BASE_REQUIRED_VARS)
    if LLM_BACKEND == "claude":
        required.append("ANTHROPIC_API_KEY")

    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID_1 = int(os.getenv("TELEGRAM_USER_ID_1", "0"))
#TODO: Remove comment for 2nd ID
#TELEGRAM_USER_ID_2 = int(os.getenv("TELEGRAM_USER_ID_2", "0"))
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID", "")

LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").lower()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
