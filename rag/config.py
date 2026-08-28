from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    load_dotenv()
except ImportError:
    pass
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CHROMA_DIR = DATA_DIR / "chroma"

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "chat_model": "openai/gpt-oss-120b",
        "has_embeddings": False,
        "pause_s": 2.0,
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "key_env": None,
        "chat_model": "llama3.1:8b",
        "has_embeddings": False,
        "pause_s": 0.0,
    },
    "openai": {
        "base_url": None,
        "key_env": "OPENAI_API_KEY",
        "chat_model": "gpt-4o-mini",
        "has_embeddings": True,
        "pause_s": 0.0,
    },
}

SOURCES = ["grokipedia", "wikipedia"]

DEFAULT_TOPICS = [
    "Elon Musk",
    "Climate change",
    "COVID-19 pandemic origins",
    "Artificial intelligence",
    "Cryptocurrency",
    "Wikipedia",
]

WIKI_TITLE_OVERRIDE = {
    "COVID-19 pandemic origins": "Investigations into the origin of COVID-19",
}

USER_AGENT = "rag-grokipedia-vs-wikipedia/0.1 (educational comparison project)"
WIKI_API = "https://en.wikipedia.org/w/api.php"


@dataclass
class Settings:
    provider: str = "groq"
    temperature: float = 0.1
    top_k: int = 5
    max_chars_per_doc: int = 120_000
    topics: tuple = tuple(DEFAULT_TOPICS)

    def __post_init__(self) -> None:
        if self.provider not in PROVIDERS:
            raise ValueError(f"PROVIDER must be one of {list(PROVIDERS)}")
        cfg = PROVIDERS[self.provider]
        self.base_url: Optional[str] = cfg["base_url"]
        self.key_env: Optional[str] = cfg["key_env"]
        self.chat_model: str = cfg["chat_model"]
        self.rate_pause_s: float = cfg["pause_s"]
        self.embedding_backend: str = "openai" if cfg["has_embeddings"] else "local"
        if self.embedding_backend == "local":
            self.embed_model = "all-MiniLM-L6-v2"
            self.embed_tag = "minilm"
            self.chunk_tokens = 220
            self.chunk_overlap = 40
        else:
            self.embed_model = "text-embedding-3-small"
            self.embed_tag = "oa3small"
            self.chunk_tokens = 400
            self.chunk_overlap = 60

    def require_keys(self) -> None:
        if self.key_env and not os.environ.get(self.key_env, "").strip():
            raise RuntimeError(
                f"{self.key_env} is missing. Locally: copy .env.example to .env. "
                "On Streamlit Cloud: App settings → Secrets → "
                'GROQ_API_KEY = "gsk_..."'
            )
        if self.embedding_backend == "openai" and not os.environ.get("OPENAI_API_KEY", "").strip():
            raise RuntimeError("OPENAI_API_KEY is missing.")

    def ensure_dirs(self) -> None:
        for d in (DATA_DIR, RAW_DIR, CHROMA_DIR):
            d.mkdir(parents=True, exist_ok=True)
