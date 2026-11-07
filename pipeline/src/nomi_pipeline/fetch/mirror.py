"""Upload local raw files to R2 and merge them into the source's manifest.json (NOMI-008)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from botocore.exceptions import ClientError

from nomi_pipeline.config import Settings
from nomi_pipeline.fetch import MANIFEST_NAME, SOURCES, _sha256

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

log = logging.getLogger(__name__)


def mirror(source: str, local_dir: Path, settings: Settings) -> dict[str, Any]:
    """Upload every file under local_dir to R2 and add it to the existing manifest.

    Entries already in the manifest are kept, so mirroring one new FAERS quarter does not
    drop the older quarters. A file with the same key replaces its old entry.
    """
    if source not in SOURCES:
        raise ValueError(f"unknown source {source!r}, expected one of {', '.join(SOURCES)}")
    bucket = settings.r2_bucket
    if not bucket:
        raise RuntimeError("R2_BUCKET not configured. Copy .env.example to .env and fill it in.")
    client = settings.r2_client()

    files = sorted(p for p in local_dir.rglob("*") if p.is_file() and p.name != MANIFEST_NAME)
    if not files:
        raise RuntimeError(f"no files found in {local_dir}")

    entries: dict[str, dict[str, Any]] = {
        e["key"]: e for e in _read_manifest(client, bucket, source).get("files", [])
    }
    for f in files:
        key = f"{source}/{f.relative_to(local_dir).as_posix()}"
        size = f.stat().st_size
        log.info("uploading %s (%s bytes)", key, f"{size:,}")
        client.upload_file(str(f), bucket, key)
        entries[key] = {"key": key, "sha256": _sha256(f), "size_bytes": size}

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "files": [entries[k] for k in sorted(entries)],
    }
    client.put_object(
        Bucket=bucket,
        Key=f"{source}/{MANIFEST_NAME}",
        Body=json.dumps(manifest, indent=2).encode(),
    )
    log.info("mirrored %d files to %s/ (%d in manifest)", len(files), source, len(entries))
    return manifest


def _read_manifest(client: S3Client, bucket: str, source: str) -> dict[str, Any]:
    try:
        obj = client.get_object(Bucket=bucket, Key=f"{source}/{MANIFEST_NAME}")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return {}
        raise
    manifest: dict[str, Any] = json.loads(obj["Body"].read())
    return manifest
