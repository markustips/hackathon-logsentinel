"""Configuration management for LogSentinel AI."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # LLM Configuration (supports both Anthropic and Google Gemini)
    llm_provider: str = "gemini"  # "anthropic" or "gemini"
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = "gemini-2.0-flash-exp"  # Latest Gemini 2.0 Flash model

    # Database - Support both SQLite (development) and PostgreSQL (production)
    database_url: str = "sqlite:///./logsentinel.db"

    # FAISS Index
    faiss_index_path: str = "./data/faiss_index"

    # Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Chunking
    chunk_window_minutes: int = 5

    # API
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
