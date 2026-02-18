"""Central configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

# ── Telegram ──────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]
WHITELIST_USER_IDS: set[int] = {
    int(uid.strip())
    for uid in os.getenv("WHITELIST_USER_IDS", "").split(",")
    if uid.strip()
}

# ── OpenAI ────────────────────────────────────────────────
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

# ── PostgreSQL ────────────────────────────────────────────
DATABASE_URL: str = os.environ["DATABASE_URL"]

# ── Paths ─────────────────────────────────────────────────
PDF_FOLDER: Path = Path(os.environ["PDF_FOLDER"])
OUTPUT_BASE_FOLDER: Path = Path(os.environ["OUTPUT_BASE_FOLDER"])
MANUAL_FOLDER: Path = Path(os.environ["MANUAL_FOLDER"])

# ── Limits ────────────────────────────────────────────────
DAILY_COST_LIMIT_USD: float = float(os.getenv("DAILY_COST_LIMIT_USD", "1.0"))
MAX_PARALLEL_PDFS: int = int(os.getenv("MAX_PARALLEL_PDFS", "5"))

# ── AI ────────────────────────────────────────────────────
MODEL_PRIMARY = "gpt-4o-mini"
MODEL_FALLBACK = "gpt-4o"
CONFIDENCE_AUTO = 0.8
CONFIDENCE_REVIEW = 0.5

# ── Categories ────────────────────────────────────────────
KATEGORIE_LIST = [
    "Reparatur",
    "Ersatzteile",
    "TÜV/HU/AU",
    "Reifen",
    "Tanken",
    "Miete",
    "Wartung",
    "Versicherung",
    "Sonstiges",
]
