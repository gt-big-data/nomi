from pathlib import Path

import pytest
from nomi_pipeline.config import Settings


def test_no_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    settings = Settings()

    assert settings.data_dir == Path("data")
    assert settings.raw_dir == Path("data/raw")
    assert settings.bronze_dir == Path("data/bronze")
    assert settings.r2_account_id is None


def test_yes_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("R2_BUCKET=test-bucket-name\n")
    settings = Settings()
    assert settings.r2_bucket == "test-bucket-name"
