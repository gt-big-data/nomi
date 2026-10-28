"""Download raw sources from the R2 mirror into data/raw/ with checksums (NOMI-008)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer

from nomi_pipeline.config import Settings

app = typer.Typer(help="Download raw sources from R2 into data/raw/.")
log = logging.getLogger(__name__)

SOURCES = ("ndc", "dailymed-otc", "faers")


@app.command(name="all")
def fetch_all() -> None:
    """Fetch all raw sources from R2."""
    settings = Settings()
    for source in SOURCES:
        _fetch_source(source, settings)


@app.command(name="ndc")
def fetch_ndc() -> None:
    """Fetch the openFDA NDC directory."""
    _fetch_source("ndc", Settings())


@app.command(name="dailymed-otc")
def fetch_dailymed_otc() -> None:
    """Fetch DailyMed OTC labels."""
    _fetch_source("dailymed-otc", Settings())


@app.command(name="faers")
def fetch_faers() -> None:
    """Fetch FAERS quarterly reports."""
    _fetch_source("faers", Settings())


def _fetch_source(source: str, settings: Settings) -> None:
    bucket = settings.r2_bucket
    if not bucket:
        raise RuntimeError("R2_BUCKET not configured. Copy .env.example to .env and fill it in.")
    client = settings.r2_client()

    dest = settings.raw_dir / source
    dest.mkdir(parents=True, exist_ok=True)

    log.info("fetching manifest for %s", source)
    obj = client.get_object(Bucket=bucket, Key=f"{source}/manifest.json")
    manifest: dict[str, Any] = json.loads(obj["Body"].read())

    files: list[dict[str, Any]] = manifest.get("files", [])
    for entry in files:
        key: str = entry["key"]
        expected: str = entry["sha256"]
        local = settings.raw_dir / key
        local.parent.mkdir(parents=True, exist_ok=True)

        if local.exists() and _sha256(local) == expected:
            log.info("already fresh: %s", key)
            continue

        log.info("downloading %s", key)
        client.download_file(bucket, key, str(local))

        actual = _sha256(local)
        if actual != expected:
            local.unlink(missing_ok=True)
            raise RuntimeError(
                f"checksum mismatch for {key}: expected {expected}, got {actual}"
            )
        log.info("verified %s", key)

    manifest["fetched_at"] = datetime.now(timezone.utc).isoformat()
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2))
    log.info("fetch complete: %s (%d files)", source, len(files))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
