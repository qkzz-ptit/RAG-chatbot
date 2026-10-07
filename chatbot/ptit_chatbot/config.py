import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = PROJECT_ROOT / "data" / "documents"
CHAT_MODEL = os.getenv("PTIT_CHAT_MODEL", "gemini-3.5-flash-lite")
CHAT_MODEL_FALLBACKS = tuple(
    model.strip()
    for model in os.getenv(
        "PTIT_CHAT_MODEL_FALLBACKS", "gemini-3.7-flash,gemini-3.8-flash"
    ).split(",")
    if model.strip() and model.strip() != CHAT_MODEL
)
