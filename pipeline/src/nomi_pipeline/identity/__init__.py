"""Barcode parsing and barcode-to-product resolution (NOMI-007, 025, 026, 037)."""

from pathlib import Path
from typing import Annotated

import typer

from nomi_pipeline.config import REPO_ROOT, Settings
from nomi_pipeline.identity.resolver import TARGET, build_identity

app = typer.Typer(help="Resolve barcodes to products")


@app.command()
def resolve(
    report: Annotated[Path, typer.Option()] = Path("pipeline/reports/identity_coverage.md"),
    overrides: Annotated[Path, typer.Option()] = (
        REPO_ROOT / "pipeline/knowledge/barcode_overrides.csv"
    ),
) -> None:
    """Resolve a barcode for every directory package; write product.parquet and the report."""
    settings = Settings()
    correct, total = build_identity(settings.bronze_dir, settings.silver_dir, report, overrides)
    typer.echo(f"Resolved {correct}/{total} packages; report: {report}")
    if not total or correct / total < TARGET:
        raise typer.Exit(code=1)
