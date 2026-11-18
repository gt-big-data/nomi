"""Tests for the FAERS signal stage (NOMI-053)."""

from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pytest
from nomi_pipeline.evidence import _faers_signals as fs


def _pairs(path: Path) -> None:
    rows = []
    pid = 0

    def report(drugs, pts, age="18-64", sex="F"):  # type: ignore[no-untyped-def]
        nonlocal pid
        pid += 1
        for name, ai in drugs:
            for pt, group in pts:
                rows.append(
                    {
                        "primaryid": str(pid),
                        "quarter": "2024Q1",
                        "drugname": name,
                        "prod_ai": ai,
                        "role_cod": "PS",
                        "pt": pt,
                        "event_group": group,
                        "age_band": age,
                        "sex": sex,
                    }
                )

    for _ in range(30):
        report([("TYLENOL", "ACETAMINOPHEN")], [("hepatic failure", "hepatic_disorders")])
    for _ in range(70):
        report([("PANADOL", "PARACETAMOL")], [("nausea", None)])
    for _ in range(900):
        report([("OTHER", "OTHERDRUG")], [("nausea", None)])
    for _ in range(10):
        report([("OTHER", "OTHERDRUG")], [("hepatic failure", "hepatic_disorders")])
    # Two hepatic PTs on one report count once.
    report(
        [("ADVIL PM", "IBUPROFEN SODIUM\\DIPHENHYDRAMINE CITRATE")],
        [("hepatic failure", "hepatic_disorders"), ("jaundice", "hepatic_disorders")],
    )
    # A salt under its INN name, and a report with unknown age.
    report([("PIRITON", "CHLORPHENAMINE MALEATE")], [("somnolence", "falls_sedation")])
    report([("ACETAMINOPHEN", None)], [("nausea", None)], age="unknown")
    pl.DataFrame(rows).write_parquet(path / "faers_pairs.parquet")


@pytest.fixture
def signals(tmp_path: Path) -> pl.DataFrame:
    _pairs(tmp_path)
    fs.build_faers_signals(
        SimpleNamespace(silver_dir=tmp_path),  # type: ignore[arg-type]
        reports_dir=tmp_path,
        summary_path=tmp_path / "summary.json",
    )
    return pl.read_parquet(tmp_path / "faers_signals.parquet")


def _row(df: pl.DataFrame, moiety: str, group: str = "hepatic_disorders") -> dict:  # type: ignore[type-arg]
    hit = df.filter(
        pl.col("moiety") == moiety,
        pl.col("event_group") == group,
        pl.col("age_band") == "all",
        pl.col("sex") == "all",
    )
    return hit.row(0, named=True)


def test_counts_reports_and_expected(signals: pl.DataFrame) -> None:
    row = _row(signals, "ACETAMINOPHEN")
    # 101 acetaminophen reports (PARACETAMOL and the drugname-only report included), 41 hepatic
    # reports, 1013 reports. The unknown-age report counts in the pooled stratum only.
    assert row["report_count"] == 30
    assert row["expected_count"] == pytest.approx(101 * 41 / 1013)
    assert row["ic"] == pytest.approx(math.log2(30.5 / (101 * 41 / 1013 + 0.5)))
    assert row["ic025"] > 0
    assert row["dimension"] == "liver"


def test_salts_and_multi_ingredient_names(signals: pl.DataFrame) -> None:
    ibuprofen = _row(signals, "IBUPROFEN")
    assert ibuprofen["report_count"] == 1
    assert _row(signals, "DIPHENHYDRAMINE")["report_count"] == 1
    # The ibuprofen moiety is written for both the ibuprofen and ibuprofen sodium files.
    uniis = signals.filter(pl.col("moiety") == "IBUPROFEN")["unii"].unique().to_list()
    assert len(uniis) == 2


def test_rows_follow_signal_schema(signals: pl.DataFrame) -> None:
    assert set(signals["age_band"].unique()) <= {"0-11", "12-17", "18-64", "65+", "all"}
    assert set(signals["sex"].unique()) <= {"F", "M", "all"}
    assert signals["ic025"].is_finite().all()


def test_ic025_matches_gamma_quantile() -> None:
    # Gamma(30.5, rate 4.5): exact 2.5% quantile is about 4.573.
    assert fs._ic025(30, 4.0) == pytest.approx(math.log2(4.573), abs=0.01)
    assert math.isfinite(fs._ic025(0, 0.0))


def test_expected_count_does_not_overflow() -> None:
    counts = pl.DataFrame(
        {"n_x": [50_000], "n_y": [350_000], "n": [17_000_000]},
        schema={"n_x": pl.UInt32, "n_y": pl.UInt32, "n": pl.UInt32},
    )
    assert counts.select(fs._expected())[0, 0] == pytest.approx(50_000 * 350_000 / 17_000_000)


def test_inn_salt_names_match(signals: pl.DataFrame) -> None:
    assert _row(signals, "CHLORPHENIRAMINE", "falls_sedation")["report_count"] == 1


def test_unknown_age_only_in_pooled_strata(signals: pl.DataFrame) -> None:
    adults = signals.filter(
        pl.col("moiety") == "ACETAMINOPHEN",
        pl.col("event_group") == "hepatic_disorders",
        pl.col("age_band") == "18-64",
        pl.col("sex") == "all",
    ).row(0, named=True)
    # 1012 known-age reports, 100 acetaminophen among them.
    assert adults["expected_count"] == pytest.approx(100 * 41 / 1012)


def test_summary_keeps_signals_only(tmp_path: Path, signals: pl.DataFrame) -> None:
    summary = json.loads((tmp_path / "summary.json").read_text())
    rows = [r for entries in summary.values() for r in entries]
    assert rows and all(r["ic025"] > 0 for r in rows)
