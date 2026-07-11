from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    static_dir: Path = BASE_DIR / "static"
    downloads_dir: Path = BASE_DIR / "downloads"

    max_file_age_seconds: int = 3600
    cleanup_interval_seconds: int = 900

    cors_origins: list[str] = ["*"]


settings = Settings()

settings.static_dir.mkdir(exist_ok=True)
settings.downloads_dir.mkdir(exist_ok=True)
