"""Load and deduplicate FAERS quarterly reports into bronze Parquet tables (NOMI-024)."""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path

import polars as pl

from nomi_pipeline.config import REPO_ROOT, Settings

log = logging.getLogger(__name__)

TABLES = ("demo", "drug", "reac", "outc", "rpsr", "ther", "indi")


def ingest_faers(settings: Settings, reports_dir: Path | None = None) -> None:
    """Read all FAERS ZIPs, deduplicate by latest caseversion, write bronze Parquet."""
    raw_dir = settings.raw_dir / "faers"
    out_dir = settings.bronze_dir / "faers"
    out_dir.mkdir(parents=True, exist_ok=True)

    zips = sorted(raw_dir.glob("*.zip"))
    if not zips:
        raise FileNotFoundError(
            f"No FAERS ZIP files found in {raw_dir}. Run 'pipeline fetch faers' first."
        )

    frames: dict[str, list[pl.DataFrame]] = {t: [] for t in TABLES}
    for zf in zips:
        log.info("reading %s", zf.name)
        for table in TABLES:
            df = _read_table(zf, table)
            if df is not None and len(df) > 0:
                frames[table].append(df)

    if not frames["demo"]:
        raise ValueError("No DEMO data found in any FAERS ZIP.")

    tables: dict[str, pl.DataFrame] = {
        t: pl.concat(frames[t], how="diagonal") for t in TABLES if frames[t]
    }

    # Keep only the latest version of each case using primaryid from DEMO
    latest_primaryids = (
        tables["demo"]
        .with_columns(pl.col("caseversion").cast(pl.Int32, strict=False))
        .sort("caseversion", descending=True)
        .unique(subset=["caseid"], keep="first")
        .select("primaryid")
    )

    stats: list[dict[str, object]] = []
    for table_name in TABLES:
        if table_name not in tables:
            log.warning("no data found for table %s", table_name)
            continue
        df = tables[table_name]
        total = len(df)
        deduped = df.join(latest_primaryids, on="primaryid", how="inner").sort("primaryid")
        after = len(deduped)
        log.info(
            "%s: %d → %d rows after dedup (%d removed)", table_name, total, after, total - after
        )
        stats.append(
            {"table": table_name, "total": total, "after_dedup": after, "removed": total - after}
        )
        deduped.write_parquet(out_dir / f"{table_name}.parquet")

    _write_report(stats, zips, reports_dir or REPO_ROOT / "pipeline" / "reports")


def _read_table(zip_path: Path, table: str) -> pl.DataFrame | None:
    """Extract one table's ASCII file from a FAERS quarterly ZIP."""
    try:
        with zipfile.ZipFile(zip_path) as z:
            match = next(
                (
                    n
                    for n in z.namelist()
                    if table.upper() in n.upper() and n.lower().endswith(".txt")
                ),
                None,
            )
            if match is None:
                log.debug("no %s file in %s", table, zip_path.name)
                return None
            text = z.read(match).decode("latin-1")
            cleaned = "\n".join(line.rstrip("$") for line in text.splitlines())
            df = pl.read_csv(
                io.StringIO(cleaned),
                separator="$",
                infer_schema_length=0,
                truncate_ragged_lines=True,
                ignore_errors=True,
            )
            return df.rename({c: c.strip().lower() for c in df.columns})
    except zipfile.BadZipFile:
        log.warning("skipping bad ZIP: %s", zip_path.name)
        return None


def _write_report(stats: list[dict[str, object]], zips: list[Path], reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# FAERS dedup report",
        "",
        f"Quarters loaded: {len(zips)}",
        "",
        "| Table | Total rows | After dedup | Removed |",
        "|---|---|---|---|",
    ]
    for s in stats:
        lines.append(f"| {s['table']} | {s['total']:,} | {s['after_dedup']:,} | {s['removed']:,} |")
    (reports_dir / "faers-dedup.md").write_text("\n".join(lines) + "\n")
    log.info("wrote dedup report to %s/faers-dedup.md", reports_dir)
