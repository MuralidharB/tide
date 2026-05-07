from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = parent of the backend package directory. Used to anchor relative
# paths so commands work the same from any cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    fred_api_key: str = ""
    tide_db_path: Path = PROJECT_ROOT / "data" / "tide.duckdb"
    tide_api_url: str = "http://127.0.0.1:8000"

    zscore_window_years: int = 3

    @field_validator("tide_db_path", mode="after")
    @classmethod
    def _resolve_db_path(cls, v: Path) -> Path:
        return v if v.is_absolute() else (PROJECT_ROOT / v).resolve()


settings = Settings()
