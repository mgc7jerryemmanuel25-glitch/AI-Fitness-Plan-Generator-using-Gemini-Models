from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@lru_cache
def get_settings() -> dict:
    return {
        "app_title": os.getenv("APP_TITLE", "FitBuddy - AI Fitness Plan Generator"),
        "google_api_key": os.getenv("GOOGLE_API_KEY", "").strip(),
        "workout_model": os.getenv("GEMINI_WORKOUT_MODEL", "gemini-2.5-flash"),
        "tip_model": os.getenv("GEMINI_TIP_MODEL", "gemini-2.5-flash"),
        "database_url": os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'fitbuddy.db'}"),
        "admin_token": os.getenv("ADMIN_TOKEN", "change-this-admin-token"),
        "demo_mode": os.getenv("DEMO_MODE", "").lower() in {"1", "true", "yes"},
    }
