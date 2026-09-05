import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]


def load_config():
    load_dotenv(ROOT / "backend" / ".env")
    return {
        "DATABASE_PATH": os.getenv("DATABASE_PATH", str(ROOT / "backend/instance/factorymind.sqlite3")),
        "MODEL_DIR": os.getenv("MODEL_DIR", str(ROOT / "ml/artifacts")),
        "KNOWLEDGE_DIR": str(ROOT / "knowledge_base"),
        "JEV_API_KEY": os.getenv("JEV_API_KEY", ""),
        "JEV_MODEL": os.getenv("JEV_MODEL", "jev-latest"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "LLM_MODEL": os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        "REVIEW_THRESHOLD": 0.75,
        "PROCESSING_TIMEOUT": 180,
        "MAX_CONTENT_LENGTH": 32 * 1024,
    }
