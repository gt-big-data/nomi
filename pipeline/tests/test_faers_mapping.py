from __future__ import annotations

from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import polars as pl
import pytest
from nomi_pipeline.config import Settings
from nomi_pipeline.evidence._faers_mapping import (
    COLUMNS,
    build_faers_drug_mapping,
)
from nomi_pipeline.evidence.name_matcher import (
    SAMPLE_CANONICAL,
    SAMPLE_SYNONYMS,
    FaersNameMatcher,
)


def _mock_settings(tmp_path: Path) -> Settings:
    m = MagicMock(spec=Settings)
    m.bronze_dir = tmp_path / "bronze"
    m.silver_dir = tmp_path / "silver"
    return cast(Settings, m)


@pytest.fixture()
def test_matcher() -> FaersNameMatcher:
    return FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS, fuzzy_threshold=0.85)


@pytest.fixture()
def bronze_drug_data(tmp_path: Path) -> Path:
    """Create a mock bronze FAERS drug table."""
    bronze_faers = tmp_path / "bronze" / "faers"
    bronze_faers.mkdir(parents=True, exist_ok=True)

    df = pl.DataFrame(
        {
            "primaryid": ["1001", "1002", "1003", "1004", "1005", "1006", "1007"],
            "caseid": ["100", "101", "102", "103", "104", "105", "106"],
            "drug_seq": ["1", "1", "1", "1", "2", "1", "1"],
            "role_cod": ["PS", "PS", "PS", "SS", "C", "PS", "PS"],
            "drugname": [
                "IBUPROFEN 200MG",  # Exact
                "TYLENOL EXTRA STRENGTH",  # Synonym
                "ADVIL PM",  # Combination brand synonym (2 ingredients)
                "EXCEDRIN",  # Combination brand synonym (3 ingredients)
                "AMOXICILLIN 500MG",  # Unmapped Rx
                "IBUPROFEN",  # Exact duplicate
                "TYLENOL + CAFFEINE",  # Delimiter combination
            ],
        }
    )
    df.write_parquet(bronze_faers / "drug.parquet")
    return bronze_faers / "drug.parquet"


def test_single_ingredient_mapping(
    bronze_drug_data: Path,
    test_matcher: FaersNameMatcher,
    tmp_path: Path,
) -> None:
    settings = _mock_settings(tmp_path)
    build_faers_drug_mapping(settings, reports_dir=tmp_path / "reports", matcher=test_matcher)

    result = pl.read_parquet(tmp_path / "silver" / "faers_drug_ingredient.parquet")

    # Ibuprofen (1001)
    row_1001 = result.filter(pl.col("primaryid") == "1001")
    assert len(row_1001) == 1
    assert row_1001["unii"].item() == "WK2XYI10QM"
    assert row_1001["match_method"].item() == "exact"

    # Tylenol (1002) -> Acetaminophen
    row_1002 = result.filter(pl.col("primaryid") == "1002")
    assert len(row_1002) == 1
    assert row_1002["unii"].item() == "362O9ITL9D"
    assert row_1002["match_method"].item() == "rxnorm_synonym"


def test_combination_product_explosion(
    bronze_drug_data: Path,
    test_matcher: FaersNameMatcher,
    tmp_path: Path,
) -> None:
    """Combination drugs must explode into one row per active ingredient."""
    settings = _mock_settings(tmp_path)
    build_faers_drug_mapping(settings, reports_dir=tmp_path / "reports", matcher=test_matcher)

    result = pl.read_parquet(tmp_path / "silver" / "faers_drug_ingredient.parquet")

    # Advil PM (1003) -> Ibuprofen + Diphenhydramine (multi-ingredient brand synonym)
    row_1003 = result.filter(pl.col("primaryid") == "1003")
    assert len(row_1003) == 2, f"Expected 2 rows for Advil PM, got {len(row_1003)}"
    uniis_1003 = set(row_1003["unii"].to_list())
    assert uniis_1003 == {"WK2XYI10QM", "814498Ch67"}

    # Excedrin (1004) -> Acetaminophen + Aspirin + Caffeine
    row_1004 = result.filter(pl.col("primaryid") == "1004")
    assert len(row_1004) == 3, f"Expected 3 rows for Excedrin, got {len(row_1004)}"
    uniis_1004 = set(row_1004["unii"].to_list())
    assert uniis_1004 == {"362O9ITL9D", "R16CO5Y76E", "3G6A5W338E"}

    # Tylenol + Caffeine (1007) -> Delimiter combination
    row_1007 = result.filter(pl.col("primaryid") == "1007")
    assert len(row_1007) == 2
    assert set(row_1007["match_method"].to_list()) == {"combination"}
    assert set(row_1007["unii"].to_list()) == {"362O9ITL9D", "3G6A5W338E"}


def test_unmapped_handling(
    bronze_drug_data: Path,
    test_matcher: FaersNameMatcher,
    tmp_path: Path,
) -> None:
    settings = _mock_settings(tmp_path)
    build_faers_drug_mapping(settings, reports_dir=tmp_path / "reports", matcher=test_matcher)

    result = pl.read_parquet(tmp_path / "silver" / "faers_drug_ingredient.parquet")

    # Amoxicillin (1005) -> unmapped
    row_1005 = result.filter(pl.col("primaryid") == "1005")
    assert len(row_1005) == 1
    assert row_1005["unii"].item() is None
    assert row_1005["match_method"].item() == "unmapped"
    assert row_1005["confidence"].item() == 0.0


def test_faers_mapping_schema(
    bronze_drug_data: Path,
    test_matcher: FaersNameMatcher,
    tmp_path: Path,
) -> None:
    settings = _mock_settings(tmp_path)
    build_faers_drug_mapping(settings, reports_dir=tmp_path / "reports", matcher=test_matcher)

    result = pl.read_parquet(tmp_path / "silver" / "faers_drug_ingredient.parquet")
    assert result.columns == COLUMNS


def test_report_written_with_required_sections(
    bronze_drug_data: Path,
    test_matcher: FaersNameMatcher,
    tmp_path: Path,
) -> None:
    settings = _mock_settings(tmp_path)
    reports_dir = tmp_path / "reports"
    build_faers_drug_mapping(settings, reports_dir=reports_dir, matcher=test_matcher)

    report_path = reports_dir / "faers_mapping.md"
    assert report_path.exists()

    content = report_path.read_text(encoding="utf-8")
    assert "FAERS Ingredient Mapping Report" in content
    assert "Summary Statistics" in content
    assert "Match Method Breakdown" in content
    assert "Top Unmapped Drug Names" in content
    assert "Spot Check Sample" in content
    assert "AMOXICILLIN 500MG" in content


def test_missing_drug_table_raises(tmp_path: Path) -> None:
    settings = _mock_settings(tmp_path)
    with pytest.raises(FileNotFoundError, match="FAERS drug table not found"):
        build_faers_drug_mapping(settings)
