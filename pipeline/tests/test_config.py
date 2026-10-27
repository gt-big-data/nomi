from pathlib import Path

import pytest
from nomi_pipeline.config import REPO_ROOT, Settings


def use_env_file(monkeypatch: pytest.MonkeyPatch, env_file: Path | None) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", env_file)


def test_no_env_file(monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    settings = Settings()

    assert settings.data_dir == REPO_ROOT / "data"
    assert settings.raw_dir == REPO_ROOT / "data/raw"
    assert settings.bronze_dir == REPO_ROOT / "data/bronze"
    assert settings.r2_account_id is None


def test_yes_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("R2_BUCKET=test-bucket-name\n")
    use_env_file(monkeypatch, env_file)
    settings = Settings()
    assert settings.r2_bucket == "test-bucket-name"


def test_unrelated_env_keys_are_ignored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SOME_OTHER_TOOL_KEY=1\n")
    use_env_file(monkeypatch, env_file)
    assert Settings().r2_bucket is None


def test_data_dir_does_not_depend_on_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.chdir(tmp_path)
    assert Settings().data_dir == REPO_ROOT / "data"


def test_absolute_data_dir_is_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    assert Settings().data_dir == tmp_path


def test_log_level_is_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("LOG_LEVEL", "debug")
    assert Settings().log_level == "DEBUG"
