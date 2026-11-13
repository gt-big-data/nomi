import json
import shutil
from pathlib import Path

import pytest
from nomi_pipeline.cli import app
from nomi_pipeline.config import Settings
from typer.testing import CliRunner

FIXTURES = Path(__file__).parent / "fixtures" / "build"

runner = CliRunner()


def use_env_file(monkeypatch: pytest.MonkeyPatch, env_file: Path | None) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", env_file)


def test_build_writes_sqlite_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    silver_dir = tmp_path / "silver"
    silver_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "product.parquet", silver_dir / "product.parquet")

    results = runner.invoke(app, ["build"])

    assert results.exit_code == 0, results.output

    build_dir = tmp_path / "build"
    assert (build_dir / "nomi.sqlite").exists()
    assert (build_dir / "manifest.json").exists()

    manifest = json.loads((build_dir / "manifest.json").read_text())
    assert manifest["counts"]["products"] == 2
