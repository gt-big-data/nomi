"""FAERS name normalization, analysis tables and Bayesian signals (NOMI-033, 044, 046, 053)."""

import typer

from nomi_pipeline.config import Settings
from nomi_pipeline.evidence._faers_pairs import build_faers_pairs

app = typer.Typer(help="FAERS evidence processing: pairs, name normalization, signals.")


@app.command()
def pairs() -> None:
    """Build FAERS drug-reaction pairs table with demographics."""
    settings = Settings()
    build_faers_pairs(settings)


@app.command(name="map-drugs")
def map_drugs() -> None:
    """Map FAERS drug rows to active ingredients (NOMI-046)."""
    from nomi_pipeline.evidence._faers_mapping import build_faers_drug_mapping

    settings = Settings()
    build_faers_drug_mapping(settings)
