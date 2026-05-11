"""Configuration module using pydantic-settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Groq AI
    groq_api_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/iphipi"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/iphipi"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8000

    # App
    app_name: str = "iphipi"
    debug: bool = True
    backend_port: int = 8001
    frontend_url: str = "http://localhost:3000"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Models
    groq_llm_model: str = "llama-3.3-70b-versatile"
    groq_whisper_model: str = "whisper-large-v3-turbo"
    groq_vision_model: str = "llama-3.2-90b-vision-preview"
    embedding_model: str = "all-MiniLM-L6-v2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
