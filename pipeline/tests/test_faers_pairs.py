from __future__ import annotations

import zipfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import polars as pl
import pytest
from nomi_pipeline.config import Settings
from nomi_pipeline.evidence._faers_pairs import (
    _clean_demographics,
    _load_event_groups,
    _map_event_groups,
    build_faers_pairs,
)
from nomi_pipeline.ingest._faers import ingest_faers

# Test fixtures for FAERS data
DEMO = """\
primaryid$caseid$caseversion$age$age_cod$gndr_cod
1001$100$1$5$YR$M
1002$100$2$15$YR$F
1003$101$1$30$YR$M
1004$102$1$70$YR$F
1005$103$1$50$DEC$UNK
1006$104$1$$YR$
"""

DRUG = """\
primaryid$caseid$drug_seq$role_cod$drugname
1001$100$1$PS$IBUPROFEN
1002$100$1$PS$IBUPROFEN
1002$100$2$C$ASPIRIN
1002$100$3$I$WARFARIN
1003$101$1$SS$ACETAMINOPHEN
1004$102$1$PS$NAPROXEN
1005$103$1$PS$ASPIRIN
1006$104$1$PS$TYLENOL
"""

REAC = """\
primaryid$caseid$pt
1001$100$NAUSEA
1002$100$GASTROINTESTINAL HEMORRHAGE
1002$100$FALL
1003$101$HEPATIC FAILURE
1004$102$STROKE
1005$103$DIZZINESS
1006$104$HEADACHE
"""

TABLE_DATA = {
    "demo": DEMO,
    "drug": DRUG,
    "reac": REAC,
    "outc": "primaryid$caseid$outc_cod\n1002$100$HO\n",
    "rpsr": "primaryid$caseid$rpsr_cod\n1002$100$HP\n",
    "ther": "primaryid$caseid$dsg_drug_seq$start_dt$end_dt\n1002$100$1$20240101$20240115\n",
    "indi": "primaryid$caseid$indi_drug_seq$indi_pt\n1002$100$1$PAIN\n",
}


def _make_zip(path: Path, quarter: str = "24Q1") -> None:
    """Create a test FAERS ZIP file."""
    with zipfile.ZipFile(path, "w") as z:
        for table, data in TABLE_DATA.items():
            z.writestr(f"ASCII/{table.upper()}{quarter}.txt", data.encode("latin-1"))


def _mock_settings(tmp_path: Path) -> Settings:
    """Create mock Settings for testing."""
    m = MagicMock(spec=Settings)
    m.raw_dir = tmp_path / "raw"
    m.bronze_dir = tmp_path / "bronze"
    m.silver_dir = tmp_path / "silver"
    return cast(Settings, m)


@pytest.fixture()
def faers_bronze(tmp_path: Path) -> Path:
    """Create bronze FAERS data for testing."""
    # Create raw ZIP
    zf = tmp_path / "raw" / "faers" / "faers_ascii_2024q1.zip"
    zf.parent.mkdir(parents=True)
    _make_zip(zf)

    # Run ingest to create bronze
    settings = _mock_settings(tmp_path)
    ingest_faers(settings, reports_dir=tmp_path / "reports")

    return tmp_path / "bronze" / "faers"


def test_filter_ps_ss_only(faers_bronze: Path, tmp_path: Path) -> None:
    """Test that only PS and SS drugs are kept, not C or I."""
    settings = _mock_settings(tmp_path)
    build_faers_pairs(settings, reports_dir=tmp_path / "reports")

    pairs = pl.read_parquet(tmp_path / "silver" / "faers_pairs.parquet")

    # Check that only PS/SS roles are present
    roles = set(pairs["role_cod"].to_list())
    assert roles == {"PS", "SS"}, f"Expected only PS/SS roles, got {roles}"

    # Verify concomitant (C) and interacting (I) drugs are excluded
    # primaryid 1002 had ASPIRIN (C) and WARFARIN (I) which should be filtered out
    drugs_for_1002 = pairs.filter(pl.col("primaryid") == "1002")["drugname"].to_list()
    assert "ASPIRIN" not in drugs_for_1002
    assert "WARFARIN" not in drugs_for_1002
    assert "IBUPROFEN" in drugs_for_1002  # PS drug should be included


def test_age_conversion(tmp_path: Path) -> None:
    """Test age unit conversion to years."""
    demo = pl.DataFrame(
        {
            "primaryid": ["1", "2", "3", "4", "5", "6", "7"],
            "age": ["5", "10", "120", "52", "365", "8760", ""],
            "age_cod": ["DEC", "YR", "MON", "WK", "DY", "HR", "YR"],
            "gndr_cod": ["M", "F", "M", "F", "M", "F", "M"],
        }
    )

    cleaned = _clean_demographics(demo)

    # Verify age conversion
    assert "age_band" in cleaned.columns
    age_bands = dict(
        zip(cleaned["primaryid"].to_list(), cleaned["age_band"].to_list(), strict=False)
    )

    assert age_bands["1"] == "18-64"  # 5 decades = 50 years
    assert age_bands["2"] == "0-11"  # 10 years
    assert age_bands["3"] == "0-11"  # 120 months = 10 years
    assert age_bands["4"] == "0-11"  # 52 weeks = 1 year
    assert age_bands["5"] == "0-11"  # 365 days = 1 year
    assert age_bands["6"] == "0-11"  # 8760 hours = 1 year
    assert age_bands["7"] == "unknown"  # null age


def test_age_band_mapping(tmp_path: Path) -> None:
    """Test age to age_band mapping."""
    demo = pl.DataFrame(
        {
            "primaryid": ["1", "2", "3", "4", "5"],
            "age": ["5", "15", "30", "70", ""],
            "age_cod": ["YR", "YR", "YR", "YR", "YR"],
            "gndr_cod": ["M", "F", "M", "F", "M"],
        }
    )

    cleaned = _clean_demographics(demo)
    age_bands = dict(
        zip(cleaned["primaryid"].to_list(), cleaned["age_band"].to_list(), strict=False)
    )

    assert age_bands["1"] == "0-11"  # 5 years
    assert age_bands["2"] == "12-17"  # 15 years
    assert age_bands["3"] == "18-64"  # 30 years
    assert age_bands["4"] == "65+"  # 70 years
    assert age_bands["5"] == "unknown"  # null


def test_sex_standardization(tmp_path: Path) -> None:
    """Test sex standardization to M/F/unknown."""
    demo = pl.DataFrame(
        {
            "primaryid": ["1", "2", "3", "4", "5"],
            "age": ["30", "30", "30", "30", "30"],
            "age_cod": ["YR", "YR", "YR", "YR", "YR"],
            "gndr_cod": ["M", "F", "UNK", "", "X"],
        }
    )

    cleaned = _clean_demographics(demo)
    sexes = dict(zip(cleaned["primaryid"].to_list(), cleaned["sex"].to_list(), strict=False))

    assert sexes["1"] == "M"
    assert sexes["2"] == "F"
    assert sexes["3"] == "unknown"  # UNK → unknown
    assert sexes["4"] == "unknown"  # empty → unknown
    assert sexes["5"] == "unknown"  # X → unknown


def test_event_group_mapping(tmp_path: Path) -> None:
    """Test PT to event group mapping."""
    pairs = pl.DataFrame(
        {
            "primaryid": ["1", "2", "3", "4"],
            "pt": [
                "Gastrointestinal hemorrhage",
                "Fall",
                "Hepatic failure",
                "Unknown reaction",
            ],
            "pt_lower": [
                "gastrointestinal hemorrhage",
                "fall",
                "hepatic failure",
                "unknown reaction",
            ],
        }
    )

    event_groups = {
        "event_groups": {
            "gastrointestinal_hemorrhage": {
                "dimension": "gi_bleeding",
                "pt_patterns": ["gastrointestinal hemorrhage"],
            },
            "falls_sedation": {"dimension": "sedation_falls", "pt_patterns": ["fall"]},
            "hepatic_disorders": {"dimension": "liver", "pt_patterns": ["hepatic failure"]},
        }
    }

    mapped = _map_event_groups(pairs, event_groups)

    groups = dict(zip(mapped["primaryid"].to_list(), mapped["event_group"].to_list(), strict=False))

    assert groups["1"] == "gastrointestinal_hemorrhage"
    assert groups["2"] == "falls_sedation"
    assert groups["3"] == "hepatic_disorders"
    assert groups["4"] is None  # unmapped


def test_final_schema(faers_bronze: Path, tmp_path: Path) -> None:
    """Test that output has correct schema."""
    settings = _mock_settings(tmp_path)
    build_faers_pairs(settings, reports_dir=tmp_path / "reports")

    pairs = pl.read_parquet(tmp_path / "silver" / "faers_pairs.parquet")

    # Check schema
    expected_columns = {"primaryid", "drugname", "role_cod", "pt", "event_group", "age_band", "sex"}
    assert set(pairs.columns) == expected_columns

    # Check that we have data
    assert len(pairs) > 0


def test_report_written(faers_bronze: Path, tmp_path: Path) -> None:
    """Test that reconciliation report is written."""
    settings = _mock_settings(tmp_path)
    reports_dir = tmp_path / "reports"
    build_faers_pairs(settings, reports_dir=reports_dir)

    report = reports_dir / "faers_pairs.md"
    assert report.exists()

    content = report.read_text()
    assert "FAERS Pairs Report" in content
    assert "Input Counts" in content
    assert "Demographics Breakdown" in content
    assert "Event Group Coverage" in content
    assert "Age Bands" in content


def test_deduplication(faers_bronze: Path, tmp_path: Path) -> None:
    """Test that duplicate (primaryid, drugname, pt) combinations are removed."""
    settings = _mock_settings(tmp_path)
    build_faers_pairs(settings, reports_dir=tmp_path / "reports")

    pairs = pl.read_parquet(tmp_path / "silver" / "faers_pairs.parquet")

    # Check for duplicates on key columns
    unique_keys = pairs.select(
        ["primaryid", "drugname", "pt", "age_band", "sex", "role_cod", "event_group"]
    ).unique()

    assert len(unique_keys) == len(pairs), "Found duplicate rows in output"


def test_load_event_groups(tmp_path: Path) -> None:
    """Test loading event groups YAML file."""
    from nomi_pipeline.config import REPO_ROOT

    event_groups_path = REPO_ROOT / "pipeline" / "knowledge" / "faers_event_groups.yaml"
    event_groups = _load_event_groups(event_groups_path)

    assert "event_groups" in event_groups
    assert len(event_groups["event_groups"]) >= 9  # At least 9 event groups

    # Verify structure of first group
    first_group = list(event_groups["event_groups"].values())[0]
    assert "dimension" in first_group
    assert "description" in first_group
    assert "pt_patterns" in first_group
    assert isinstance(first_group["pt_patterns"], list)


def test_sex_comes_from_either_faers_column() -> None:
    # 2014 quarters use gndr_cod, later ones sex; the bronze table holds both.
    demo = pl.DataFrame(
        {
            "primaryid": ["1", "2", "3"],
            "age": ["40", "40", "40"],
            "age_cod": ["YR", "YR", "YR"],
            "gndr_cod": ["F", None, None],
            "sex": [None, "M", None],
        }
    )
    sexes = dict(_clean_demographics(demo).select(["primaryid", "sex"]).iter_rows())
    assert sexes == {"1": "F", "2": "M", "3": "unknown"}
