import json
import shutil
from pathlib import Path

import polars as pl
import pytest
from nomi_pipeline.cli import app
from nomi_pipeline.config import Settings
from typer.testing import CliRunner

FIXTURES = Path(__file__).parent / "fixtures" / "build"

runner = CliRunner()


def use_env_file(monkeypatch: pytest.MonkeyPatch, env_file: Path | None) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", env_file)


def write_silver(tmp_path: Path) -> None:
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir(parents=True)
    shutil.copy(FIXTURES / "product.parquet", silver_dir / "product.parquet")
    pl.DataFrame(
        {
            "ndc_raw": ["0363-0710-08", "76176-135-01"],
            "expected_ndc11": ["00363071008", "76176013501"],
            "status": ["resolved", "resolved"],
        }
    ).write_parquet(silver_dir / "identity_results.parquet")


def test_build_writes_sqlite_and_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    write_silver(tmp_path)

    results = runner.invoke(app, ["build", "dataset"])

    assert results.exit_code == 0, results.output

    build_dir = tmp_path / "build"
    assert (build_dir / "nomi.sqlite").exists()
    assert (build_dir / "manifest.json").exists()

    manifest = json.loads((build_dir / "manifest.json").read_text())
    assert manifest["counts"]["products"] == 2


def test_build_without_product_records_says_what_to_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    results = runner.invoke(app, ["build", "dataset"])

    assert results.exit_code == 1
    assert "product.parquet not found; run `pipeline identity resolve` first" in results.output


def test_publish_twice_needs_overwrite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("DATASET_STORE", f"memory://{tmp_path.name}")
    write_silver(tmp_path)

    assert runner.invoke(app, ["build", "dataset", "--publish"]).exit_code == 0
    results = runner.invoke(app, ["build", "dataset", "--publish"])
    assert results.exit_code == 1
    assert "pass --overwrite" in results.output
    assert runner.invoke(app, ["build", "dataset", "--publish", "--overwrite"]).exit_code == 0
