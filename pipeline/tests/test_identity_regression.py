"""Every barcode an identity fix resolved keeps resolving (NOMI-037).

tests/fixtures/identity_regression.csv has one row per fixed barcode. The rows always have to be
well formed; they are resolved against the real bronze tables when those have been built (CI has
no data, so there the second test is skipped).
"""

import csv
from pathlib import Path

import polars as pl
import pytest
from nomi_pipeline.config import Settings
from nomi_pipeline.identity.barcode import ndc_candidates
from nomi_pipeline.identity.resolver import Resolver

FIXTURE = Path(__file__).parent / "fixtures" / "identity_regression.csv"
ROWS = list(csv.DictReader(FIXTURE.open(newline="", encoding="utf-8")))
BRONZE = Settings().bronze_dir
TABLES = ("ndc", "spl_products", "spl_ingredients")


def test_regression_rows_are_well_formed() -> None:
    assert ROWS
    assert len({row["barcode"] for row in ROWS}) == len(ROWS)
    for row in ROWS:
        parsed = ndc_candidates(row["barcode"])
        assert parsed["status"] == "ok", row
        assert row["expected_ndc11"] in parsed["candidates"], row
        assert row["expected_status"] and row["category"] and row["note"], row


@pytest.mark.skipif(
    not all((BRONZE / f"{name}.parquet").exists() for name in TABLES),
    reason="bronze tables not built (uv run pipeline ingest ndc && uv run pipeline ingest spl)",
)
def test_regression_rows_resolve_on_bronze() -> None:
    resolver = Resolver(
        pl.read_parquet(BRONZE / "ndc.parquet").to_dicts(),
        pl.read_parquet(BRONZE / "spl_products.parquet").to_dicts(),
        pl.read_parquet(BRONZE / "spl_ingredients.parquet")
        .filter(pl.col("role") == "active")
        .to_dicts(),
    )
    for row in ROWS:
        result = resolver.resolve(row["barcode"])
        assert result.status == row["expected_status"], row
        if result.product is not None:
            assert result.product["ndc11"] == row["expected_ndc11"], row
