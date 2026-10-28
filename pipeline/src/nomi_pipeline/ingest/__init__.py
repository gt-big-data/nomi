"""Load raw sources into typed bronze tables: NDC, DailyMed, FAERS, RxNorm."""

from __future__ import annotations

import logging

import typer

app = typer.Typer(help="Load raw sources into bronze Parquet tables.")
log = logging.getLogger(__name__)


@app.command(name="faers")
def ingest_faers() -> None:
    """Load and deduplicate FAERS adverse event reports since 2014."""
    from nomi_pipeline.config import Settings
    from nomi_pipeline.ingest._faers import ingest_faers as _run

    _run(Settings())


@app.command(name="ndc")
def ingest_ndc() -> None:
    """Load the openFDA NDC directory (not yet implemented)."""
    log.info("ingest ndc is not implemented yet")


@app.command(name="dailymed-otc")
def ingest_dailymed_otc() -> None:
    """Load DailyMed OTC labels (not yet implemented)."""
    log.info("ingest dailymed-otc is not implemented yet")
