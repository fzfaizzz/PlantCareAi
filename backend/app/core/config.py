from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env", env_file_encoding="utf-8",
        extra="ignore", case_sensitive=False,
    )
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    frontend_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    model_path: Path = Path("models/plant_disease_model.keras")
    model_metadata_path: Path = Path("models/model_metadata.json")
    class_labels_path: Path = Path("models/class_labels.json")
    max_upload_mb: int = Field(default=10, ge=1, le=10)
    max_image_pixels: int = Field(default=20_000_000, ge=4096, le=20_000_000)
    max_image_dimension: int = Field(default=12000, ge=64, le=20000)
    max_concurrent_analyses: int = Field(default=2, ge=1, le=8)
    model_concurrency: int = Field(default=1, ge=1, le=2)
    analysis_timeout_seconds: float = Field(default=45, ge=1, le=120)
    rate_limit_per_minute: int = Field(default=20, ge=1, le=120)
    rate_limit_salt: str = "local-development-only"
    redis_url: str = ""
    gemini_enabled: bool = False
    gemini_api_key: str = ""
    gemini_model: str = ""
    gemini_timeout_seconds: float = Field(default=15, ge=1, le=30)
    gemini_max_output_tokens: int = Field(default=1200, ge=256, le=2048)
    gemini_daily_request_limit: int = Field(default=100, ge=1, le=10000)
    gemini_concurrency: int = Field(default=1, ge=1, le=4)
    trust_proxy_headers: bool = False

    @model_validator(mode="after")
    def validate_deployment(self):
        if self.app_env not in {"development", "test", "production"}:
            raise ValueError("APP_ENV must be development, test, or production.")
        if "*" in self.origins:
            raise ValueError("FRONTEND_ORIGINS must be explicit origins.")
        if self.app_env == "production" and self.rate_limit_salt == "local-development-only":
            raise ValueError("Set a private RATE_LIMIT_SALT in production.")
        if self.app_env == "production" and self.gemini_enabled and not self.redis_url:
            raise ValueError("Production Gemini requires REDIS_URL for shared request/cost quotas.")
        for key in ("model_path", "model_metadata_path", "class_labels_path"):
            path = getattr(self, key)
            if not path.is_absolute():
                setattr(self, key, BACKEND_ROOT / path)
        return self

    @property
    def origins(self) -> list[str]:
        return [item.strip().rstrip("/") for item in self.frontend_origins.split(",") if item.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def max_request_bytes(self) -> int:
        return self.max_upload_bytes + 64 * 1024
