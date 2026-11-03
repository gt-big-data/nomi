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
    """Build drug-reaction pairs from bronze FAERS tables."""
    bronze_dir = settings.bronze_dir / "faers"
    silver_dir = settings.silver_dir
    silver_dir.mkdir(parents=True, exist_ok=True)

    # Load bronze tables
    demo = pl.read_parquet(bronze_dir / "demo.parquet")
    drug = pl.read_parquet(bronze_dir / "drug.parquet")
    reac = pl.read_parquet(bronze_dir / "reac.parquet")

    # Load event groups mapping
    event_groups_path = REPO_ROOT / "pipeline" / "knowledge" / "faers_event_groups.yaml"
    event_groups = _load_event_groups(event_groups_path)

    # Step 1: Filter drugs to primary/secondary suspect only
    suspect_drugs = drug.filter(pl.col("role_cod").is_in(["PS", "SS"])).select(
        ["primaryid", "drugname", "role_cod"]
    )

    log.info("Filtered to %d suspect drug records (PS/SS only)", len(suspect_drugs))

    # Step 2: Add demographics (age_band, sex) from DEMO
    # Convert age to standardized age_band
    demo_cleaned = _clean_demographics(demo)

    # Step 3: Join drug + demographics
    drug_demo = suspect_drugs.join(demo_cleaned, on="primaryid", how="inner")

    # Step 4: Join reactions
    reac_cleaned = reac.select(["primaryid", "pt"]).with_columns(
        pl.col("pt").str.to_lowercase().alias("pt_lower")
    )

    pairs = drug_demo.join(reac_cleaned, on="primaryid", how="inner")

    # Step 5: Map reactions to event groups
    pairs = _map_event_groups(pairs, event_groups)

    # Step 6: Select final columns and deduplicate
    final = (
        pairs.select(
            [
                "primaryid",
                "drugname",
                "role_cod",
                "pt",
                "event_group",
                "age_band",
                "sex",
            ]
        )
        .unique(
            subset=["primaryid", "drugname", "pt", "age_band", "sex", "role_cod", "event_group"]
        )
        .sort("primaryid", "drugname", "pt")
    )

    output_path = silver_dir / "faers_pairs.parquet"
    final.write_parquet(output_path)
    log.info("Wrote %d pairs to %s", len(final), output_path)

    # Step 7: Write reconciliation report
    _write_report(
        demo, drug, reac, suspect_drugs, final, reports_dir or REPO_ROOT / "pipeline" / "reports"
    )


def _clean_demographics(demo: pl.DataFrame) -> pl.DataFrame:
    """Convert age/age_cod to age_band and standardize sex."""
    # Convert age to years
    demo = demo.with_columns(
        [
            pl.col("age").cast(pl.Float64, strict=False).alias("age_numeric"),
            pl.col("age_cod").str.to_lowercase().alias("age_unit"),
            pl.col("gndr_cod").str.to_uppercase().alias("sex_raw"),
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


def _map_event_groups(pairs: pl.DataFrame, event_groups: dict[str, Any]) -> pl.DataFrame:
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


def _write_report(
    demo: pl.DataFrame,
    drug: pl.DataFrame,
    reac: pl.DataFrame,
    suspect_drugs: pl.DataFrame,
    pairs: pl.DataFrame,
    reports_dir: Path,
) -> None:
    """Write reconciliation report."""
    reports_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        "# FAERS Pairs Report",
        "",
        "## Input Counts (from bronze FAERS dedup)",
        f"- DEMO records: {len(demo):,}",
        f"- DRUG records (all roles): {len(drug):,}",
        f"- REAC records: {len(reac):,}",
        "",
        "## Filtering Steps",
        f"- DRUG records after PS/SS filter: {len(suspect_drugs):,}",
        f"- Final pairs (drug × reaction × demographics): {len(pairs):,}",
        "",
        "## Demographics Breakdown",
        "### Age Bands",
    ]

    age_counts = (
        pairs.group_by("age_band").agg(pl.count().alias("count")).sort("count", descending=True)
    )
    for row in age_counts.iter_rows(named=True):
        lines.append(f"- {row['age_band']}: {row['count']:,}")

    lines.append("")
    lines.append("### Sex")
    sex_counts = pairs.group_by("sex").agg(pl.count().alias("count")).sort("count", descending=True)
    for row in sex_counts.iter_rows(named=True):
        lines.append(f"- {row['sex']}: {row['count']:,}")

    lines.append("")
    lines.append("## Event Group Coverage")
    event_counts = (
        pairs.group_by("event_group").agg(pl.count().alias("count")).sort("count", descending=True)
    )
    mapped = pairs.filter(pl.col("event_group").is_not_null()).height
    unmapped = pairs.filter(pl.col("event_group").is_null()).height
    lines.append(
        f"- Reactions mapped to event groups: {mapped:,} ({100 * mapped / len(pairs):.1f}%)"
    )
    lines.append(f"- Reactions not mapped: {unmapped:,}")
    lines.append("")
    for row in event_counts.iter_rows(named=True):
        group = row["event_group"] or "(unmapped)"
        lines.append(f"- {group}: {row['count']:,}")

    (reports_dir / "faers_pairs.md").write_text("\n".join(lines) + "\n")
    log.info("Wrote pairs report to %s/faers_pairs.md", reports_dir)
