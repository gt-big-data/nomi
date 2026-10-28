"""Barcode parsing and barcode-to-product resolution (NOMI-007, 025, 026, 037)."""

from pathlib import Path
from typing import Annotated

import typer

from nomi_pipeline._stage import placeholder_app
from nomi_pipeline.config import Settings
from nomi_pipeline.identity.resolver import build_identity

app = placeholder_app("identity")


@app.command()
def resolve(
    report: Annotated[Path, typer.Option()] = Path("pipeline/reports/identity_coverage.md"),
) -> None:
    """Join bronze products and labels, then measure synthetic barcode coverage."""
    settings = Settings()
    counts = build_identity(settings.bronze_dir, settings.silver_dir, report)
    typer.echo(f"Resolved {counts['resolved']}/{counts['total']} packages; report: {report}")
    if not counts["total"] or counts["resolved"] / counts["total"] < 0.9:
        raise typer.Exit(code=1)
