"""Build FAERS drug-reaction pairs table with demographics (NOMI-044)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import polars as pl
import yaml

from nomi_pipeline.config import REPO_ROOT, Settings

log = logging.getLogger(__name__)


def build_faers_pairs(settings: Settings, reports_dir: Path | None = None) -> None:
    """Build drug-reaction pairs from bronze FAERS tables.

    The tables run to tens of millions of rows, so everything is lazy and the result is
    streamed to Parquet rather than collected in memory.
    """
    bronze_dir = settings.bronze_dir / "faers"
    silver_dir = settings.silver_dir
    silver_dir.mkdir(parents=True, exist_ok=True)

    demo = pl.scan_parquet(bronze_dir / "demo.parquet")
    drug = pl.scan_parquet(bronze_dir / "drug.parquet")
    reac = pl.scan_parquet(bronze_dir / "reac.parquet")

    event_groups_path = REPO_ROOT / "pipeline" / "knowledge" / "faers_event_groups.yaml"
    event_groups = _load_event_groups(event_groups_path)

    # Primary and secondary suspect drugs only
    suspect_drugs = drug.filter(pl.col("role_cod").is_in(["PS", "SS"])).select(
        ["primaryid", "drugname", "role_cod"]
    )

    pairs = suspect_drugs.join(_clean_demographics(demo), on="primaryid", how="inner").join(
        reac.select(["primaryid", "pt"]).with_columns(
            pl.col("pt").str.to_lowercase().alias("pt_lower")
        ),
        on="primaryid",
        how="inner",
    )
    pairs = _map_event_groups(pairs, event_groups)

    columns = ["primaryid", "drugname", "role_cod", "pt", "event_group", "age_band", "sex"]
    output_path = silver_dir / "faers_pairs.parquet"
    pairs.select(columns).unique(subset=columns).sink_parquet(output_path)

    counts = {
        "demo": demo.select(pl.len()).collect().item(),
        "drug": drug.select(pl.len()).collect().item(),
        "reac": reac.select(pl.len()).collect().item(),
        "suspect": suspect_drugs.select(pl.len()).collect().item(),
    }
    final = pl.scan_parquet(output_path)
    log.info("Wrote %d pairs to %s", final.select(pl.len()).collect().item(), output_path)
    _write_report(counts, final, reports_dir or REPO_ROOT / "pipeline" / "reports")


def _clean_demographics[Frame: (pl.DataFrame, pl.LazyFrame)](demo: Frame) -> Frame:
    """Convert age/age_cod to age_band and standardize sex."""
    # FAERS renamed gndr_cod to sex in 2014; quarters from both eras sit in one table.
    present = demo.collect_schema().names()
    sex_columns = [pl.col(c) for c in ("sex", "gndr_cod") if c in present]
    sex_raw = pl.coalesce(sex_columns) if sex_columns else pl.lit(None, dtype=pl.String)
    demo = demo.with_columns(
        [
            pl.col("age").cast(pl.Float64, strict=False).alias("age_numeric"),
            pl.col("age_cod").str.to_lowercase().alias("age_unit"),
            sex_raw.str.to_uppercase().alias("sex_raw"),
        ]
    )

    # Convert age to years based on unit
    demo = demo.with_columns(
        pl.when(pl.col("age_unit") == "dec")
        .then(pl.col("age_numeric") * 10)
        .when(pl.col("age_unit") == "yr")
        .then(pl.col("age_numeric"))
        .when(pl.col("age_unit") == "mon")
        .then(pl.col("age_numeric") / 12)
        .when(pl.col("age_unit") == "wk")
        .then(pl.col("age_numeric") / 52)
        .when(pl.col("age_unit") == "dy")
        .then(pl.col("age_numeric") / 365)
        .when(pl.col("age_unit") == "hr")
        .then(pl.col("age_numeric") / 8760)
        .otherwise(None)
        .alias("age_years")
    )

    # Map to age_band matching signal.schema.json: "0-11", "12-17", "18-64", "65+"
    demo = demo.with_columns(
        pl.when(pl.col("age_years").is_null())
        .then(pl.lit("unknown"))
        .when(pl.col("age_years") < 12)
        .then(pl.lit("0-11"))
        .when(pl.col("age_years") < 18)
        .then(pl.lit("12-17"))
        .when(pl.col("age_years") < 65)
        .then(pl.lit("18-64"))
        .otherwise(pl.lit("65+"))
        .alias("age_band")
    )

    # Standardize sex to M/F/unknown
    demo = demo.with_columns(
        pl.when(pl.col("sex_raw").is_in(["M", "F"]))
        .then(pl.col("sex_raw"))
        .otherwise(pl.lit("unknown"))
        .alias("sex")
    )

    return demo.select(["primaryid", "age_band", "sex"])


def _load_event_groups(path: Path) -> dict[str, Any]:
    """Load event groups YAML."""
    with path.open() as f:
        data: dict[str, Any] = yaml.safe_load(f)
        return data


def _map_event_groups[Frame: (pl.DataFrame, pl.LazyFrame)](
    pairs: Frame, event_groups: dict[str, Any]
) -> Frame:
    """Map PT to event_group using pattern matching."""
    # Build mapping from PT patterns to event group names
    pt_to_group = {}
    for group_name, group_data in event_groups["event_groups"].items():
        for pattern in group_data["pt_patterns"]:
            pt_to_group[pattern.lower()] = group_name

    # Add event_group column
    # For MVP: exact match on lowercase PT
    # TODO: Later support contains/regex matching
    pairs = pairs.with_columns(
        pl.col("pt_lower")
        .replace_strict(pt_to_group, default=None, return_dtype=pl.String)
        .alias("event_group")
    )

    return pairs


def _write_report(counts: dict[str, int], pairs: pl.LazyFrame, reports_dir: Path) -> None:
    """Write reconciliation report."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    total = pairs.select(pl.len()).collect().item()

    lines = [
        "# FAERS Pairs Report",
        "",
        "## Input Counts (from bronze FAERS dedup)",
        f"- DEMO records: {counts['demo']:,}",
        f"- DRUG records (all roles): {counts['drug']:,}",
        f"- REAC records: {counts['reac']:,}",
        "",
        "## Filtering Steps",
        f"- DRUG records after PS/SS filter: {counts['suspect']:,}",
        f"- Final pairs (drug × reaction × demographics): {total:,}",
        "",
        "## Demographics Breakdown",
        "### Age Bands",
    ]
    for row in _counts(pairs, "age_band").iter_rows(named=True):
        lines.append(f"- {row['age_band']}: {row['count']:,}")

    lines.append("")
    lines.append("### Sex")
    for row in _counts(pairs, "sex").iter_rows(named=True):
        lines.append(f"- {row['sex']}: {row['count']:,}")

    lines.append("")
    lines.append("## Event Group Coverage")
    event_counts = _counts(pairs, "event_group")
    mapped = event_counts.filter(pl.col("event_group").is_not_null())["count"].sum()
    share = 100 * mapped / total if total else 0.0
    lines.append(f"- Reactions mapped to event groups: {mapped:,} ({share:.1f}%)")
    lines.append(f"- Reactions not mapped: {total - mapped:,}")
    lines.append("")
    for row in event_counts.iter_rows(named=True):
        group = row["event_group"] or "(unmapped)"
        lines.append(f"- {group}: {row['count']:,}")

    (reports_dir / "faers_pairs.md").write_text("\n".join(lines) + "\n")
    log.info("Wrote pairs report to %s/faers_pairs.md", reports_dir)


def _counts(pairs: pl.LazyFrame, column: str) -> pl.DataFrame:
    return (
        pairs.group_by(column)
        .agg(pl.len().alias("count"))
        .sort(["count", column], descending=[True, False])
        .collect()
    )
