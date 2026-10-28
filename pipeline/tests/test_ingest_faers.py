from __future__ import annotations

import zipfile
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import polars as pl
import pytest
from nomi_pipeline.config import Settings
from nomi_pipeline.ingest._faers import TABLES, _read_table, ingest_faers

DEMO = """\
primaryid$caseid$caseversion$age$age_cod$sex
1001$100$1$45$YR$M
1002$100$2$45$YR$M
1003$101$1$30$YR$F
"""

DRUG = """\
primaryid$caseid$drug_seq$role_cod$drugname
1001$100$1$PS$IBUPROFEN
1002$100$1$PS$IBUPROFEN
1003$101$1$PS$ACETAMINOPHEN
"""

REAC = """\
primaryid$caseid$pt
1001$100$NAUSEA
1002$100$NAUSEA
1003$101$HEADACHE
"""

OUTC = """\
primaryid$caseid$outc_cod
1002$100$HO
1003$101$OT
"""

RPSR = """\
primaryid$caseid$rpsr_cod
1002$100$HP
1003$101$CS
"""

THER = """\
primaryid$caseid$dsg_drug_seq$start_dt$end_dt
1002$100$1$20240101$20240115
1003$101$1$20240101$20240110
"""

INDI = """\
primaryid$caseid$indi_drug_seq$indi_pt
1002$100$1$PAIN
1003$101$1$FEVER
"""

TABLE_DATA = {
    "demo": DEMO,
    "drug": DRUG,
    "reac": REAC,
    "outc": OUTC,
    "rpsr": RPSR,
    "ther": THER,
    "indi": INDI,
}


def _make_zip(path: Path, quarter: str = "24Q1") -> None:
    with zipfile.ZipFile(path, "w") as z:
        for table, data in TABLE_DATA.items():
            z.writestr(f"ASCII/{table.upper()}{quarter}.txt", data.encode("latin-1"))


def _mock_settings(tmp_path: Path) -> Settings:
    m = MagicMock(spec=Settings)
    m.raw_dir = tmp_path / "raw"
    m.bronze_dir = tmp_path / "bronze"
    return cast(Settings, m)


@pytest.fixture()
def faers_zip(tmp_path: Path) -> Path:
    zf = tmp_path / "raw" / "faers" / "faers_ascii_2024q1.zip"
    zf.parent.mkdir(parents=True)
    _make_zip(zf)
    return zf


def test_dedup_keeps_latest_caseversion(tmp_path: Path, faers_zip: Path) -> None:
    settings = _mock_settings(tmp_path)
    ingest_faers(settings, reports_dir=tmp_path / "reports")

    demo = pl.read_parquet(tmp_path / "bronze" / "faers" / "demo.parquet")
    # case 100 had versions 1 and 2 — only version 2 (primaryid 1002) should survive
    assert set(demo["primaryid"].to_list()) == {"1002", "1003"}


def test_all_seven_tables_written(tmp_path: Path, faers_zip: Path) -> None:
    settings = _mock_settings(tmp_path)
    ingest_faers(settings, reports_dir=tmp_path / "reports")

    for table in TABLES:
        assert (tmp_path / "bronze" / "faers" / f"{table}.parquet").exists(), (
            f"missing {table}.parquet"
        )


def test_two_runs_produce_identical_output(tmp_path: Path, faers_zip: Path) -> None:
    settings = _mock_settings(tmp_path)
    ingest_faers(settings, reports_dir=tmp_path / "reports")
    run1 = pl.read_parquet(tmp_path / "bronze" / "faers" / "demo.parquet")

    ingest_faers(settings, reports_dir=tmp_path / "reports")
    run2 = pl.read_parquet(tmp_path / "bronze" / "faers" / "demo.parquet")

    assert run1.equals(run2)


def test_no_zips_raises_file_not_found(tmp_path: Path) -> None:
    (tmp_path / "raw" / "faers").mkdir(parents=True)
    settings = _mock_settings(tmp_path)
    with pytest.raises(FileNotFoundError, match="pipeline fetch faers"):
        ingest_faers(settings, reports_dir=tmp_path / "reports")


def test_read_table_returns_none_for_missing_table(tmp_path: Path, faers_zip: Path) -> None:
    result = _read_table(faers_zip, "nonexistent")
    assert result is None


def test_read_table_parses_demo(tmp_path: Path, faers_zip: Path) -> None:
    df = _read_table(faers_zip, "demo")
    assert df is not None
    assert "primaryid" in df.columns
    assert "caseid" in df.columns
    assert len(df) == 3


def test_dedup_report_written(tmp_path: Path, faers_zip: Path) -> None:
    settings = _mock_settings(tmp_path)
    reports_dir = tmp_path / "reports"
    ingest_faers(settings, reports_dir=reports_dir)
    report = reports_dir / "faers-dedup.md"
    assert report.exists()
    assert "demo" in report.read_text()
