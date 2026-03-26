"""
config.py — centralised configuration loaded from .env
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # ── Database ──────────────────────────────────────────────
    BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))
    DB_PATH: str = os.path.join(BASE_DIR, "aosa.db")

    # ── Auth ──────────────────────────────────────────────────
    ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "admin123")

    # ── Google / Gemini ───────────────────────────────────────
    GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = "gemini-2.0-flash"

    # ── Flask ─────────────────────────────────────────────────
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "0") == "1"
    STATIC_FOLDER: str = os.path.join(BASE_DIR, "..", "frontend1")
