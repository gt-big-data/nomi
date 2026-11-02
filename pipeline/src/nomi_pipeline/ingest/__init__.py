"""Load raw sources into typed bronze tables: NDC directory, DailyMed SPL, FAERS, RxNorm (NOMI-009, 010, 023, 024)."""

import json
import logging

import polars as pl
import typer

from nomi_pipeline.config import Settings
from nomi_pipeline.ingest.ndc import NdcResult, compute_stats, parse_ndc_file
from nomi_pipeline.ingest.spl import collect_labels

app = typer.Typer(help="Load raw sources into typed bronze tables")
log = logging.getLogger(__name__)


@app.command(name="spl")
def ingest_spl() -> None:
    """Parse DailyMed OTC labels into spl_products.parquet and spl_ingredients.parquet."""
    settings = Settings()
    raw_dir = settings.raw_dir / "dailymed-otc"
    result = collect_labels(raw_dir)

    settings.bronze_dir.mkdir(parents=True, exist_ok=True)

    pl.DataFrame(result.products).write_parquet(settings.bronze_dir / "spl_products.parquet")
    pl.DataFrame(result.ingredients).write_parquet(settings.bronze_dir / "spl_ingredients.parquet")
    pl.DataFrame(result.failures).write_parquet(settings.bronze_dir / "spl_parse_failures.parquet")

    successful = result.files_processed - len(result.failures)
    if result.files_processed > 0:  # noqa: SIM108
        rate = successful / result.files_processed * 100
    else:
        rate = 0.0

    log.info(f"{successful} / {result.files_processed} labels parsed ({rate:.1f}%)")


@app.command(name="ndc")
def ingest_ndc() -> None:
    """Parse the openFDA NDC directory into ndc.parquet and ndc.stats.json."""
    settings = Settings()
    raw_dir = settings.raw_dir / "ndc"

    combined = NdcResult()
    for json_file in sorted(raw_dir.glob("*.json")):
        file_result = parse_ndc_file(json_file)
        combined.products.extend(file_result.products)
        combined.total_records += file_result.total_records
        combined.skipped_bad_ndc += file_result.skipped_bad_ndc

    combined.products.sort(key=lambda row: row.ndc11)

    settings.bronze_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(combined.products).write_parquet(settings.bronze_dir / "ndc.parquet")

    stats = compute_stats(combined)
    (settings.bronze_dir / "ndc.stats.json").write_text(json.dumps(stats, indent=2))

    log.info(
        f"{len(combined.products)} rows written from {combined.total_records} records "
        f"({combined.skipped_bad_ndc} bad NDCs skipped)"
    )
