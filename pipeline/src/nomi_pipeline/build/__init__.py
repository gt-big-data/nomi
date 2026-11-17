"""On-device SQLite dataset build, manifest and release (NOMI-038, 056, 059, 065)."""

import logging

import typer

from nomi_pipeline.build.build import build_database, build_time, publish, write_manifest
from nomi_pipeline.config import Settings

log = logging.getLogger(__name__)
DATASET_VERSION = "v0.1.0"


def run_build(
    publish_flag: bool = typer.Option(False, "--publish"),
    overwrite: bool = typer.Option(False, help="Replace this version if it is already published."),
) -> None:
    """Build nomi.sqlite and manifest.json from the identity stage's product records."""

    settings = Settings()
    settings.build_dir.mkdir(parents=True, exist_ok=True)

    product_parquet = settings.silver_dir / "product.parquet"
    identity_results = settings.silver_dir / "identity_results.parquet"
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
    log.info(f"built {DATASET_VERSION}: {manifest['counts']}")

    if publish_flag:
        prefix = publish(db_path, manifest_path, DATASET_VERSION, settings, overwrite)
        log.info(f"publish to {prefix}")
