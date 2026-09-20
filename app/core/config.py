"""InsightEngine Configuration Management."""

import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable bindings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    EVALUATION_DIR: Path = DATA_DIR / "evaluation"

    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"
    FRONTEND_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # LLM Settings
    LLM_PROVIDER: Literal["gemini", "groq", "openai"] = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Embeddings Settings
    EMBEDDING_MODEL: str = "BAAI/bge-large-en-v1.5"
    EMBEDDING_DIM: int = 1024
    USE_HF_EMBEDDINGS: bool = False

    # Vector Store Settings
    VECTOR_DB: Literal["inmemory", "qdrant", "chromadb"] = "inmemory"
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    COLLECTION_NAME: str = "financial_reports"

    # Retrieval and Reranker Parameters
    TOP_K_RETRIEVAL: int = 15
    TOP_K_RERANKED: int = 4

    def ensure_directories(self) -> None:
        """Ensure all required local directories exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        self.EVALUATION_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
