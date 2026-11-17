"""On-device SQLite dataset build, manifest and release (NOMI-038, 056, 059, 065)."""

from typing import Annotated

import typer

from nomi_pipeline.build.build import build_database, build_time, publish, write_manifest
from nomi_pipeline.config import Settings

DATASET_VERSION = "v0.1.0"

app = typer.Typer(help="Build and publish the app's SQLite dataset")


@app.command()
def dataset(
    publish_flag: Annotated[bool, typer.Option("--publish")] = False,
    overwrite: Annotated[
        bool, typer.Option(help="Replace this version if it is already published.")
    ] = False,
) -> None:
    """Build nomi.sqlite and manifest.json from the identity stage's product records."""
    settings = Settings()
    product_parquet = settings.silver_dir / "product.parquet"
    identity_results = settings.silver_dir / "identity_results.parquet"
    for path in (product_parquet, identity_results):
        if not path.exists():
            typer.echo(f"error: {path} not found; run `pipeline identity resolve` first", err=True)
            raise typer.Exit(1)

    settings.build_dir.mkdir(parents=True, exist_ok=True)
    db_path = settings.build_dir / "nomi.sqlite"
    manifest_path = settings.build_dir / "manifest.json"

    counts = build_database(
        product_parquet=product_parquet,
        identity_results=identity_results,
        db_path=db_path,
        dataset_version=DATASET_VERSION,
        built_at=build_time(),
    )
    manifest = write_manifest(
        inputs=[product_parquet, identity_results],
        db_path=db_path,
        counts=counts,
        dataset_version=DATASET_VERSION,
        manifest_path=manifest_path,
    )
    typer.echo(f"Built {DATASET_VERSION}: {manifest['counts']}")

    if publish_flag:
        try:
            prefix = publish(db_path, manifest_path, DATASET_VERSION, settings, overwrite)
        except FileExistsError as e:
            typer.echo(f"error: {e}; pass --overwrite to replace it", err=True)
            raise typer.Exit(1) from e
        typer.echo(f"Published to {prefix}")
