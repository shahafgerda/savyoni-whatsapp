"""Loads environment variables and spec.json, exposes settings.

Fails fast with a clear error if a required value is missing, so the
student gets an actionable message instead of a deep stack trace.
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"חסר משתנה סביבה: {name}. בדוק את קובץ .env (ראה .env.example)."
        )
    return value


# --- Green API (WhatsApp connection) ---
GREEN_API_URL = _required("GREEN_API_URL").rstrip("/")
GREEN_API_INSTANCE = _required("GREEN_API_INSTANCE")
GREEN_API_TOKEN = _required("GREEN_API_TOKEN")

# --- LLM ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY = _required("GOOGLE_API_KEY")

# --- Storage ---
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = str(DATA_DIR / "conversations.db")

# How many past messages (user+assistant) to feed the model as context.
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "20"))

# --- Spec (source of truth for the bot's character) ---
with open(BASE_DIR / "spec.json", encoding="utf-8") as f:
    SPEC = json.load(f)
