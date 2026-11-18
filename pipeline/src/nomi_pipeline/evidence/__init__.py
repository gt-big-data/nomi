"""FAERS name normalization, analysis tables and Bayesian signals (NOMI-033, 044, 046, 053)."""

import typer

from nomi_pipeline.config import Settings
from nomi_pipeline.evidence._faers_pairs import build_faers_pairs
from nomi_pipeline.evidence._faers_signals import build_faers_signals

app = typer.Typer(help="FAERS evidence processing: pairs, name normalization, signals.")


@app.command()
def pairs() -> None:
    """Build FAERS drug-reaction pairs table with demographics."""
    settings = Settings()
    build_faers_pairs(settings)


@app.command()
def signals() -> None:
    """Compute IC and IC025 per ingredient, event group, age band and sex."""
    settings = Settings()
    build_faers_signals(settings)
