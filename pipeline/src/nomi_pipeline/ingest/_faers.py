"""Load and deduplicate FAERS quarterly reports into bronze Parquet tables (NOMI-024)."""

from __future__ import annotations

import io
import logging
import shutil
import zipfile
from pathlib import Path

import polars as pl

from nomi_pipeline.config import REPO_ROOT, Settings

log = logging.getLogger(__name__)

TABLES = ("demo", "drug", "reac", "outc", "rpsr", "ther", "indi")


def ingest_faers(settings: Settings, reports_dir: Path | None = None) -> None:
    """Read all FAERS ZIPs, deduplicate by latest caseversion, write bronze Parquet.

    The ASCII files are about 17 GB uncompressed, so each quarter is staged to Parquet on
    its own and the dedup runs lazily over the staged files, one table at a time.
    """
    raw_dir = settings.raw_dir / "faers"
    out_dir = settings.bronze_dir / "faers"
    out_dir.mkdir(parents=True, exist_ok=True)

    zips = sorted(raw_dir.glob("*.zip"))
    if not zips:
        raise FileNotFoundError(
            f"No FAERS ZIP files found in {raw_dir}. Run 'pipeline fetch faers' first."
        )

    staging = out_dir / "_staging"
    shutil.rmtree(staging, ignore_errors=True)
    deleted: set[str] = set()
    try:
        for zf in zips:
            log.info("reading %s", zf.name)
            for table in TABLES:
                df = _read_table(zf, table)
                if df is not None and len(df) > 0:
                    (staging / table).mkdir(parents=True, exist_ok=True)
                    df.write_parquet(staging / table / f"{zf.stem}.parquet")
            deleted |= _read_deleted_caseids(zf)

        if not (staging / "demo").exists():
            raise ValueError("No DEMO data found in any FAERS ZIP.")

        # Keep only the latest version of each case, and drop cases FDA has deleted.
        latest_primaryids = (
            _scan(staging / "demo")
            .with_columns(pl.col("caseversion").cast(pl.Int32, strict=False))
            .filter(~pl.col("caseid").is_in(list(deleted)))
            .sort(["caseid", "caseversion", "primaryid"], descending=True, nulls_last=True)
            .unique(subset=["caseid"], keep="first", maintain_order=True)
            .select("primaryid")
            .collect()
        )
        log.info("%d cases deleted by FDA were dropped", len(deleted))

        stats: list[dict[str, object]] = []
        for table_name in TABLES:
            if not (staging / table_name).exists():
                log.warning("no data found for table %s", table_name)
                continue
            source = _scan(staging / table_name)
            total = source.select(pl.len()).collect().item()
            out = out_dir / f"{table_name}.parquet"
            source.join(latest_primaryids.lazy(), on="primaryid", how="semi").sink_parquet(out)
            after = pl.scan_parquet(out).select(pl.len()).collect().item()
            log.info(
                "%s: %d → %d rows after dedup (%d removed)",
                table_name,
                total,
                after,
                total - after,
            )
            stats.append(
                {
                    "table": table_name,
                    "total": total,
                    "after_dedup": after,
                    "removed": total - after,
                }
            )
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    _write_report(stats, zips, reports_dir or REPO_ROOT / "pipeline" / "reports")


def _scan(folder: Path) -> pl.LazyFrame:
    # Columns change between FAERS years, so line the quarters up by name.
    return pl.concat([pl.scan_parquet(f) for f in sorted(folder.glob("*.parquet"))], how="diagonal")


def _read_deleted_caseids(zip_path: Path) -> set[str]:
    """Case ids FDA removed, from the Deleted/DELETE*.txt file in quarters since 2019."""
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = [
                n for n in z.namelist() if "DELETE" in n.upper() and n.lower().endswith(".txt")
            ]
            return {
                line.strip().strip("$")
                for n in names
                for line in z.read(n).decode("latin-1").splitlines()
                if line.strip().strip("$").isdigit()
            }
    except zipfile.BadZipFile:
        return set()


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
