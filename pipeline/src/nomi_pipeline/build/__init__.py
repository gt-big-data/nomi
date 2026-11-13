"""On-device SQLite dataset build, manifest and release (NOMI-038, 056, 059, 065)."""

import logging

import typer

from nomi_pipeline.build.build import build_database, publish, write_manifest
from nomi_pipeline.config import Settings

log = logging.getLogger(__name__)
DATASET_VERSION = "v0.1.0"


def run_build(publish_flag: bool = typer.Option(False, "--publish")) -> None:
    """Build nomi.sqlite and manifest.json from data/silver/product.parquet."""

    settings = Settings()
    settings.build_dir.mkdir(parents=True, exist_ok=True)

    product_parquet = settings.silver_dir / "product.parquet"
    db_path = settings.build_dir / "nomi.sqlite"
    manifest_path = settings.build_dir / "manifest.json"

    counts = build_database(
        product_parquet=product_parquet, db_path=db_path, dataset_version=DATASET_VERSION
    )
    manifest = write_manifest(
        product_parquet=product_parquet,
        counts=counts,
        dataset_version=DATASET_VERSION,
        manifest_path=manifest_path,
    )
    log.info(f"built {DATASET_VERSION}: {manifest['counts']}")

    if publish_flag:
        prefix = publish(db_path, manifest_path, DATASET_VERSION, settings)
        log.info(f"publish to {prefix}")
