"""Upload local raw files to the raw data store and merge them into manifest.json (NOMI-008)."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from fsspec import AbstractFileSystem
from huggingface_hub import CommitOperationAdd, HfApi, HfFileSystem
from huggingface_hub.hf_file_system import HfFileSystemResolvedRepositoryPath

from nomi_pipeline.config import Settings
from nomi_pipeline.fetch import MANIFEST_NAME, SOURCES, _sha256, open_store

log = logging.getLogger(__name__)

# Only these files may be mirrored. The store is public, so anything else in the folder
# (partial downloads, .DS_Store, a stray .env) must never be uploaded.
SOURCE_FILES: dict[str, str] = {
    "ndc": "drug-ndc-*.json.zip",
    "dailymed-otc": "dm_spl_release_human_otc_part*.xml.zip",
    "faers": "faers_ascii_*.zip",
}


def mirror(source: str, local_dir: Path, settings: Settings) -> dict[str, Any]:
    """Upload new or changed source files from local_dir and add them to the manifest.

    Entries already in the manifest are kept, so mirroring one new FAERS quarter does not
    drop the older quarters. A file with the same key replaces its old entry, and files whose
    checksum is unchanged are not uploaded again.
    """
    if source not in SOURCES:
        raise ValueError(f"unknown source {source!r}, expected one of {', '.join(SOURCES)}")
    fs, root = open_store(settings)

    files, ignored = _source_files(source, local_dir)
    if ignored:
        log.warning("not mirroring %d files: %s", len(ignored), ", ".join(ignored))
    if not files:
        raise RuntimeError(f"no {SOURCE_FILES[source]} files found in {local_dir}")

    # Note the head commit before reading the manifest, so a concurrent mirror fails the
    # commit instead of silently dropping entries.
    parent = _hf_head(fs, root, settings) if isinstance(fs, HfFileSystem) else None
    manifest_path = f"{root}/{source}/{MANIFEST_NAME}"
    existing: dict[str, Any] = (
        json.loads(fs.cat_file(manifest_path)) if fs.exists(manifest_path) else {}
    )
    entries: dict[str, dict[str, Any]] = {e["key"]: e for e in existing.get("files", [])}

    uploads: list[tuple[Path, str]] = []
    for f in files:
        key = f"{source}/{f.name}"
        entry = {"key": key, "sha256": _sha256(f), "size_bytes": f.stat().st_size}
        if entries.get(key) == entry:
            continue
        entries[key] = entry
        uploads.append((f, key))
    if not uploads:
        log.info("%s/ is already up to date (%d in manifest)", source, len(entries))
        return existing

    manifest = {
        "generated_at": datetime.now(UTC).isoformat(),
        "files": [entries[k] for k in sorted(entries)],
    }
    body = json.dumps(manifest, indent=2).encode()
    log.info("uploading %d files to %s/", len(uploads), source)
    if isinstance(fs, HfFileSystem):
        _upload_hf(fs, root, uploads, f"{source}/{MANIFEST_NAME}", body, settings, parent)
    else:
        for f, key in uploads:
            fs.put_file(str(f), f"{root}/{key}")
        fs.pipe_file(manifest_path, body)
    log.info("mirrored %d files to %s/ (%d in manifest)", len(uploads), source, len(entries))
    return manifest


def _source_files(source: str, local_dir: Path) -> tuple[list[Path], list[str]]:
    """Split local_dir's entries into mirrorable source files and everything else."""
    files: list[Path] = []
    ignored: list[str] = []
    for p in sorted(local_dir.iterdir()):
        if p.name == MANIFEST_NAME:
            continue
        if p.is_file() and not p.is_symlink() and fnmatch(p.name, SOURCE_FILES[source]):
            files.append(p)
        else:
            ignored.append(p.name)
    return files, ignored


def _resolve_hf(fs: HfFileSystem, root: str) -> HfFileSystemResolvedRepositoryPath:
    resolved = fs.resolve_path(root)
    if not isinstance(resolved, HfFileSystemResolvedRepositoryPath):
        raise RuntimeError(f"RAW_STORE must point at a Hugging Face dataset repo, got {root}")
    if resolved.revision and re.fullmatch(r"[0-9a-f]{40}", resolved.revision):
        raise RuntimeError("RAW_STORE is pinned to a commit; remove @<commit> to mirror")
    return resolved


def _hf_head(fs: HfFileSystem, root: str, settings: Settings) -> str | None:
    resolved = _resolve_hf(fs, root)
    info = HfApi(token=settings.hf_token).repo_info(
        resolved.repo_id, repo_type=resolved.repo_type, revision=resolved.revision
    )
    fs.invalidate_cache()  # read the manifest as of that commit, not a cached copy
    return info.sha


def _upload_hf(
    fs: AbstractFileSystem,
    root: str,
    uploads: list[tuple[Path, str]],
    manifest_key: str,
    body: bytes,
    settings: Settings,
    parent: str | None,
) -> None:
    """Upload files and manifest to a Hugging Face repo in one commit."""
    assert isinstance(fs, HfFileSystem)
    resolved = _resolve_hf(fs, root)
    prefix = f"{resolved.path_in_repo}/" if resolved.path_in_repo else ""
    operations = [
        CommitOperationAdd(path_in_repo=f"{prefix}{key}", path_or_fileobj=str(f))
        for f, key in uploads
    ]
    operations.append(
        CommitOperationAdd(path_in_repo=f"{prefix}{manifest_key}", path_or_fileobj=body)
    )
    source = manifest_key.split("/")[0]
    HfApi(token=settings.hf_token).create_commit(
        repo_id=resolved.repo_id,
        repo_type=resolved.repo_type,
        revision=resolved.revision,
        operations=operations,
        commit_message=f"Mirror {len(uploads)} {source} files",
        parent_commit=parent,
    )
