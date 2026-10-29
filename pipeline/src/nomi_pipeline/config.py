from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")
    data_dir: Path = Path("data")
    log_level: str = "INFO"

    r2_account_id: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    r2_bucket: str | None = None
    r2_endpoint: str | None = None

    @field_validator("data_dir")
    @classmethod
    def _anchor_data_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else REPO_ROOT / value

    @field_validator("log_level")
    @classmethod
    def _uppercase_log_level(cls, value: str) -> str:
        return value.upper()

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def bronze_dir(self) -> Path:
        return self.data_dir / "bronze"

    @property
    def silver_dir(self) -> Path:
        return self.data_dir / "silver"

    @property
    def gold_dir(self) -> Path:
        return self.data_dir / "gold"

    @property
    def build_dir(self) -> Path:
        return self.data_dir / "build"

    def r2_client(self) -> S3Client:
        import boto3

        missing = [
            name
            for name, val in [
                ("R2_ENDPOINT", self.r2_endpoint),
                ("R2_ACCESS_KEY_ID", self.r2_access_key_id),
                ("R2_SECRET_ACCESS_KEY", self.r2_secret_access_key),
                ("R2_BUCKET", self.r2_bucket),
            ]
            if not val
        ]
        if missing:
            raise RuntimeError(
                f"R2 credentials not configured: {', '.join(missing)}. "
                "Copy .env.example to .env and fill in the R2_* values."
            )
        return boto3.client(
            "s3",
            endpoint_url=self.r2_endpoint,
            aws_access_key_id=self.r2_access_key_id,
            aws_secret_access_key=self.r2_secret_access_key,
            region_name="auto",
        )
