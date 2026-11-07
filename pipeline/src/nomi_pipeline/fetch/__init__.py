"""Download raw sources from the raw data store into data/raw/ with checksums (NOMI-008).

The store is any fsspec URL in RAW_STORE, normally the Hugging Face dataset (see ADR-0003).
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from fsspec import AbstractFileSystem
from fsspec.core import url_to_fs

from nomi_pipeline.config import Settings

app = typer.Typer(help="Download raw sources from the raw data store into data/raw/.")
log = logging.getLogger(__name__)

SOURCES = ("ndc", "dailymed-otc", "faers")
MANIFEST_NAME = "manifest.json"


@app.command(name="all")
def fetch_all() -> None:
    """Fetch all raw sources."""
    settings = Settings()
    for source in SOURCES:
        _fetch_source(source, settings)


@app.command(name="ndc")
def fetch_ndc() -> None:
    """Fetch the openFDA NDC directory."""
    _fetch_source("ndc", Settings())


@app.command(name="dailymed-otc")
def fetch_dailymed_otc() -> None:
    """Fetch DailyMed OTC labels (XML only)."""
    _fetch_source("dailymed-otc", Settings())


@app.command(name="faers")
def fetch_faers() -> None:
    """Fetch FAERS quarterly reports."""
    _fetch_source("faers", Settings())


def open_store(settings: Settings) -> tuple[AbstractFileSystem, str]:
    """Return the filesystem and root path for RAW_STORE."""
    if not settings.raw_store:
        raise RuntimeError("RAW_STORE not configured. Copy .env.example to .env and fill it in.")
    options: dict[str, Any] = {}
    if settings.hf_token and settings.raw_store.startswith("hf://"):
        options["token"] = settings.hf_token
    fs, root = url_to_fs(settings.raw_store, **options)
    return fs, root.rstrip("/")


def _fetch_source(source: str, settings: Settings) -> None:
    fs, root = open_store(settings)

    dest = settings.raw_dir / source
    dest.mkdir(parents=True, exist_ok=True)

    log.info("fetching manifest for %s", source)
    manifest_path = f"{root}/{source}/{MANIFEST_NAME}"
    if not fs.exists(manifest_path):
        raise RuntimeError(
            f"no {MANIFEST_NAME} for {source} in {settings.raw_store}. Has it been mirrored? "
            "See 'Getting raw data' in pipeline/README.md."
        )
    manifest: dict[str, Any] = json.loads(fs.cat_file(manifest_path))

    files: list[dict[str, Any]] = manifest.get("files", [])
    for entry in files:
        key: str = entry["key"]
        expected: str = entry["sha256"]
        if not key.startswith(f"{source}/") or ".." in Path(key).parts:
            raise RuntimeError(f"manifest key {key!r} is outside {source}/")
        local = settings.raw_dir / key
        local.parent.mkdir(parents=True, exist_ok=True)

        if local.exists() and _sha256(local) == expected:
            log.info("already fresh: %s", key)
            continue

        log.info("downloading %s", key)
        fs.get_file(f"{root}/{key}", str(local))

        actual = _sha256(local)
        if actual != expected:
            local.unlink(missing_ok=True)
            raise RuntimeError(f"checksum mismatch for {key}: expected {expected}, got {actual}")
        log.info("verified %s", key)

    manifest["fetched_at"] = datetime.now(UTC).isoformat()
    (dest / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2))
    log.info("fetch complete: %s (%d files)", source, len(files))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
