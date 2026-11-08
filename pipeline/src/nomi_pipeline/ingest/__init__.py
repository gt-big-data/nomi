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
