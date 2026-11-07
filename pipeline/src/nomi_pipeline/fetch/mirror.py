"""Upload local raw files to the raw data store and merge them into manifest.json (NOMI-008)."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fsspec import AbstractFileSystem
from huggingface_hub import CommitOperationAdd, HfApi, HfFileSystem
from huggingface_hub.hf_file_system import HfFileSystemResolvedRepositoryPath

from nomi_pipeline.config import Settings
from nomi_pipeline.fetch import MANIFEST_NAME, SOURCES, _sha256, open_store

log = logging.getLogger(__name__)


def mirror(source: str, local_dir: Path, settings: Settings) -> dict[str, Any]:
    """Upload every file under local_dir and add it to the source's manifest.

    Entries already in the manifest are kept, so mirroring one new FAERS quarter does not
    drop the older quarters. A file with the same key replaces its old entry.
    """
    if source not in SOURCES:
        raise ValueError(f"unknown source {source!r}, expected one of {', '.join(SOURCES)}")
    fs, root = open_store(settings)

    files = sorted(p for p in local_dir.rglob("*") if p.is_file() and p.name != MANIFEST_NAME)
    if not files:
        raise RuntimeError(f"no files found in {local_dir}")

    manifest_path = f"{root}/{source}/{MANIFEST_NAME}"
    existing: dict[str, Any] = (
        json.loads(fs.cat_file(manifest_path)) if fs.exists(manifest_path) else {}
    )
    entries: dict[str, dict[str, Any]] = {e["key"]: e for e in existing.get("files", [])}

    uploads: list[tuple[Path, str]] = []
    for f in files:
        key = f"{source}/{f.relative_to(local_dir).as_posix()}"
        entries[key] = {"key": key, "sha256": _sha256(f), "size_bytes": f.stat().st_size}
        uploads.append((f, key))

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "files": [entries[k] for k in sorted(entries)],
    }
    body = json.dumps(manifest, indent=2).encode()
    log.info("uploading %d files to %s/", len(uploads), source)
    if isinstance(fs, HfFileSystem):
        _upload_hf(fs, root, uploads, f"{source}/{MANIFEST_NAME}", body, settings, source)
    else:
        for f, key in uploads:
            fs.put_file(str(f), f"{root}/{key}")
        fs.pipe_file(manifest_path, body)
    log.info("mirrored %d files to %s/ (%d in manifest)", len(uploads), source, len(entries))
    return manifest


def _upload_hf(
    fs: AbstractFileSystem,
    root: str,
    uploads: list[tuple[Path, str]],
    manifest_key: str,
    body: bytes,
    settings: Settings,
    source: str,
) -> None:
    """Upload files and manifest to a Hugging Face repo in one commit."""
    assert isinstance(fs, HfFileSystem)
    resolved = fs.resolve_path(root)
    if not isinstance(resolved, HfFileSystemResolvedRepositoryPath):
        raise RuntimeError(f"RAW_STORE must point at a Hugging Face dataset repo, got {root}")
    prefix = f"{resolved.path_in_repo}/" if resolved.path_in_repo else ""
    operations = [
        CommitOperationAdd(path_in_repo=f"{prefix}{key}", path_or_fileobj=str(f))
        for f, key in uploads
    ]
    operations.append(
        CommitOperationAdd(path_in_repo=f"{prefix}{manifest_key}", path_or_fileobj=body)
    )
    HfApi(token=settings.hf_token).create_commit(
        repo_id=resolved.repo_id,
        repo_type=resolved.repo_type,
        revision=resolved.revision,
        operations=operations,
        commit_message=f"Mirror {len(uploads)} {source} files",
    )
