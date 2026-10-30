import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

KB_DIR = Path(os.getenv("KB_DIR", BASE_DIR / "data" / "knowledge_base"))
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "data" / "tickets.db"))
KB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")
RETRIEVER = os.getenv("RETRIEVER", "tfidf").lower()
TOP_K = int(os.getenv("TOP_K", "4"))
_min = os.getenv("MIN_SCORE", "").strip()
MIN_SCORE = float(_min) if _min else (0.35 if RETRIEVER == "embeddings" else 0.08)
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
COMPANY = os.getenv("COMPANY_NAME", "Acme Cloud")
