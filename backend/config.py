"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic-settings configuration with .env support."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # LLM
    anthropic_api_key: str = ""

    # Data APIs
    fred_api_key: str = ""
    alpha_vantage_api_key: str = ""
    bls_api_key: str = ""  # free at https://www.bls.gov/developers/
    bea_api_key: str = ""  # free at https://apps.bea.gov/api/signup/

    # Reasoning stage: use a cheaper/faster model for the scaffold step
    reasoning_model: str = "claude-haiku-4-5-20251001"

    # Database
    database_url: str = "sqlite:///./data/homemade_intelligence.db"
    chroma_persist_dir: Path = Path("./data/chroma")

    # Server
    frontend_url: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Agent
    anthropic_model: str = "claude-sonnet-4-6"
    max_source_chunks: int = 15
    max_past_reports: int = 3
    chunk_char_limit: int = 800
    reuse_similarity_threshold: float = 0.92
    reuse_window_hours: int = 48


settings = Settings()
