import shutil
from pathlib import Path

import polars as pl
import pytest
from nomi_pipeline.cli import app
from nomi_pipeline.config import Settings
from typer.testing import CliRunner

FIXTURES = Path(__file__).parent / "fixtures" / "spl"
runner = CliRunner()


def use_env_file(monkeypatch: pytest.MonkeyPatch, env_file: Path | None) -> None:
    monkeypatch.setitem(Settings.model_config, "env_file", env_file)


def test_ingest_spl_writes_parquet_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    raw_dailymed = tmp_path / "raw" / "dailymed-otc"
    raw_dailymed.mkdir(parents=True)
    shutil.copy(FIXTURES / "ibuprofen_otc.xml", raw_dailymed / "ibuprofen_otc.xml")
    shutil.copy(FIXTURES / "not_xml.xml", raw_dailymed / "not_xml.xml")

    result = runner.invoke(app, ["ingest", "spl"])

    assert result.exit_code == 0, result.output

    bronze = tmp_path / "bronze"
    products = pl.read_parquet(bronze / "spl_products.parquet")
    ingredients = pl.read_parquet(bronze / "spl_ingredients.parquet")
    failures = pl.read_parquet(bronze / "spl_parse_failures.parquet")

    assert len(products) == 2
    assert len(ingredients) == 11
    assert len(failures) == 1
    assert failures["file"][0] == "not_xml.xml"


NDC_FIXTURES = Path(__file__).parent / "fixtures" / "ndc"


def test_ingest_ndc_writes_parquet_and_stats(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    use_env_file(monkeypatch, None)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    raw_ndc = tmp_path / "raw" / "ndc"
    raw_ndc.mkdir(parents=True)
    shutil.copy(NDC_FIXTURES / "sample.json", raw_ndc / "sample.json")

    result = runner.invoke(app, ["ingest", "ndc"])

    assert result.exit_code == 0, result.output

    bronze = tmp_path / "bronze"
    products = pl.read_parquet(bronze / "ndc.parquet")
    assert len(products) == 2

    import json

    stats = json.loads((bronze / "ndc.stats.json").read_text())
    assert stats["total_rows"] == 2
    assert stats["skipped_bad_ndc"] == 1
