from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    app_secret_key: str = "local-only-change-me"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    log_level: str = "INFO"
    allowed_origins: str = "http://localhost:3000"
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_database: str = "tattva_dev"
    file_storage_root: Path = Path("./data/uploads")
    max_upload_mb: int = Field(default=25, ge=1, le=500)
    max_document_chars: int = Field(default=20_000_000, ge=1000)
    chunk_max_chars: int = Field(default=3000, ge=200, le=20_000)
    chunk_overlap_chars: int = Field(default=300, ge=0, le=5000)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "tattva_case_chunks"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_cache_root: Path = Path("./data/embedding_cache")
    local_auth_enabled: bool = True
    auth_jwks_url: str | None = None
    auth_issuer: str | None = None
    auth_audience: str | None = None
    auth_user_id_claim: str = "sub"
    auth_tenant_id_claim: str = "tenant_id"
    auth_jwks_timeout_seconds: int = Field(default=5, ge=1, le=20)
    run_analysis_workers: bool = True
    max_tasks_per_run: int = Field(default=20, ge=1, le=100)
    max_replan_rounds: int = Field(default=2, ge=0, le=5)
    max_retries_per_task: int = Field(default=1, ge=0, le=3)
    max_concurrent_tasks: int = Field(default=3, ge=1, le=10)
    max_task_timeout_seconds: int = Field(default=120, ge=1, le=600)
    max_concurrent_runs: int = Field(default=2, ge=1, le=10)
    worker_poll_interval_seconds: float = Field(default=1.0, ge=0.1, le=30)
    worker_lease_seconds: int = Field(default=300, ge=30, le=3600)
    core_llm_base_url: str | None = None
    core_llm_api_key: str | None = None
    core_llm_model: str | None = None
    core_llm_timeout_seconds: int = Field(default=45, ge=1, le=180)
    core_llm_max_output_tokens: int = Field(default=2048, ge=128, le=8192)
    gemini_api_key: str | None = None
    gemini_live_model: str | None = None
    voice_max_session_seconds: int = Field(default=600, ge=30, le=1800)
    voice_max_concurrent_sessions: int = Field(default=2, ge=1, le=20)

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def core_llm_configured(self) -> bool:
        return bool(self.core_llm_base_url and self.core_llm_api_key and self.core_llm_model)

    @property
    def gemini_live_configured(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_live_model)


@lru_cache
def get_settings() -> Settings:
    return Settings()
