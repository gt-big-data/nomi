"""Load raw sources into typed bronze tables: NDC directory, DailyMed SPL, FAERS, RxNorm (NOMI-009, 010, 023, 024)."""

import json
import logging
from dataclasses import fields
from pathlib import Path
from typing import Annotated

import polars as pl
import typer

from nomi_pipeline.config import REPO_ROOT, Settings
from nomi_pipeline.ingest.ndc import NdcResult, compute_stats, dedupe_and_sort, parse_ndc_file
from nomi_pipeline.ingest.sections import SectionRow, collect_sections, coverage_report
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
    failures = pl.DataFrame(result.failures, schema={"file": pl.String, "error": pl.String})
    failures.write_parquet(settings.bronze_dir / "spl_parse_failures.parquet")

    successful = result.files_processed - len(result.failures)
    if result.files_processed > 0:  # noqa: SIM108
        rate = successful / result.files_processed * 100
    else:
        rate = 0.0

    log.info(f"{successful} / {result.files_processed} labels parsed ({rate:.1f}%)")
    log.info(f"{result.superseded} older or duplicate label versions dropped")


@app.command(name="sections")
def ingest_sections(
    report: Annotated[Path, typer.Option()] = REPO_ROOT
    / "pipeline"
    / "reports"
    / "spl-section-coverage.md",
) -> None:
    """Split DailyMed OTC labels into Drug Facts sections in spl_sections.parquet."""
    settings = Settings()
    result = collect_sections(settings.raw_dir / "dailymed-otc")

    settings.bronze_dir.mkdir(parents=True, exist_ok=True)
    # An explicit schema keeps the columns when there are no rows.
    schema = {f.name: pl.String for f in fields(SectionRow)} | {
        "spl_version": pl.Int64,
        "section_index": pl.Int64,
    }
    sections = pl.DataFrame(result.sections, schema=schema).select(
        [f.name for f in fields(SectionRow)]
    )
    sections.write_parquet(settings.bronze_dir / "spl_sections.parquet")

    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(coverage_report(result))

    log.info(
        f"{len(result.sections)} sections from {result.labels} labels "
        f"({len(result.failures)} parse failures); report: {report}"
    )


@app.command(name="ndc")
def ingest_ndc() -> None:
    """Parse the openFDA NDC directory into ndc.parquet and ndc.stats.json."""
    settings = Settings()
    raw_dir = settings.raw_dir / "ndc"

    # pipeline fetch delivers drug-ndc-0001-of-0001.json.zip. A loose .json is used only when there
    # is no zip, so unzipping next to it doesn't count every product twice.
    files = sorted(raw_dir.glob("*.json.zip")) or sorted(
        f for f in raw_dir.glob("*.json") if f.name != "manifest.json"
    )
    if not files:
        log.error(f"No NDC directory file in {raw_dir}; run `pipeline fetch` first")
        raise typer.Exit(1)

    combined = NdcResult()
    for json_file in files:
        file_result = parse_ndc_file(json_file)
        combined.products.extend(file_result.products)
        combined.total_records += file_result.total_records
        combined.skipped_bad_ndc += file_result.skipped_bad_ndc
        combined.bad_ndcs.extend(file_result.bad_ndcs)
        combined.skipped_unfinished += file_result.skipped_unfinished
        combined.records_without_packages += file_result.records_without_packages
        combined.duplicate_ndcs += file_result.duplicate_ndcs
    dedupe_and_sort(combined)

    settings.bronze_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(combined.products).write_parquet(settings.bronze_dir / "ndc.parquet")

    stats = compute_stats(combined)
    (settings.bronze_dir / "ndc.stats.json").write_text(json.dumps(stats, indent=2))

    log.info(
        f"{len(combined.products)} rows written from {combined.total_records} records "
        f"({combined.skipped_bad_ndc} bad NDCs skipped)"
    )
    if combined.bad_ndcs:
        log.warning(f"Bad NDCs: {', '.join(combined.bad_ndcs[:20])}")


@app.command(name="faers")
def ingest_faers() -> None:
    """Load and deduplicate FAERS adverse event reports since 2014."""
    from nomi_pipeline.ingest._faers import ingest_faers as _run

    _run(Settings())
