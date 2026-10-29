"""Load raw sources into typed bronze tables: NDC directory, DailyMed SPL, FAERS, RxNorm (NOMI-009, 010, 023, 024)."""

import logging

import polars as pl
import typer

from nomi_pipeline.config import Settings
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
