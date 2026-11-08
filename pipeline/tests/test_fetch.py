from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from fsspec.core import url_to_fs
from nomi_pipeline.config import Settings
from nomi_pipeline.fetch import _fetch_source, _sha256


def _settings(tmp_path: Path) -> Settings:
    # Each test gets its own folder in fsspec's in-memory filesystem.
    return Settings(data_dir=tmp_path, raw_store=f"memory://{tmp_path.name}")


def _seed(
    settings: Settings, files: dict[str, bytes], manifest: dict[str, Any] | None = None
) -> None:
    assert settings.raw_store
    fs, root = url_to_fs(settings.raw_store)
    for key, content in files.items():
        fs.pipe_file(f"{root}/{key}", content)
    if manifest is None:
        manifest = {
            "files": [
                {"key": k, "sha256": hashlib.sha256(v).hexdigest(), "size_bytes": len(v)}
                for k, v in files.items()
            ]
        }
    source = next(iter(files)).split("/")[0]
    fs.pipe_file(f"{root}/{source}/manifest.json", json.dumps(manifest).encode())


def test_fetch_downloads_and_verifies(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed(settings, {"ndc/file.zip": b"ndc data"})

    _fetch_source("ndc", settings)

    assert (tmp_path / "raw" / "ndc" / "file.zip").read_bytes() == b"ndc data"
    assert "fetched_at" in json.loads((tmp_path / "raw" / "ndc" / "manifest.json").read_text())


def test_already_fresh_skips_download(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    content = b"existing data"
    manifest = {"files": [{"key": "ndc/file.zip", "sha256": hashlib.sha256(content).hexdigest()}]}
    # The store holds different bytes, so a download would fail the checksum.
    _seed(settings, {"ndc/file.zip": b"other bytes"}, manifest)
    local = tmp_path / "raw" / "ndc" / "file.zip"
    local.parent.mkdir(parents=True)
    local.write_bytes(content)

    _fetch_source("ndc", settings)

    assert local.read_bytes() == content


def test_stale_local_file_is_replaced(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    _seed(settings, {"ndc/file.zip": b"new data"})
    local = tmp_path / "raw" / "ndc" / "file.zip"
    local.parent.mkdir(parents=True)
    local.write_bytes(b"old data")

    _fetch_source("ndc", settings)

    assert local.read_bytes() == b"new data"


def test_corrupted_file_raises_and_cleans_up(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    manifest = {
        "files": [{"key": "ndc/file.zip", "sha256": hashlib.sha256(b"correct").hexdigest()}]
    }
    _seed(settings, {"ndc/file.zip": b"corrupt"}, manifest)

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        _fetch_source("ndc", settings)

    assert not (tmp_path / "raw" / "ndc" / "file.zip").exists()
    assert not (tmp_path / "raw" / "ndc" / "file.zip.partial").exists()


def test_failed_fetch_leaves_no_manifest(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    (tmp_path / "raw" / "ndc").mkdir(parents=True)
    (tmp_path / "raw" / "ndc" / "manifest.json").write_text("{}")
    manifest = {"files": [{"key": "ndc/file.zip", "sha256": "wrong"}]}
    _seed(settings, {"ndc/file.zip": b"data"}, manifest)

    with pytest.raises(RuntimeError):
        _fetch_source("ndc", settings)

    assert not (tmp_path / "raw" / "ndc" / "manifest.json").exists()


def test_missing_manifest_explains_mirroring(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="Has it been mirrored"):
        _fetch_source("faers", _settings(tmp_path))


def test_manifest_key_outside_source_is_rejected(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    manifest = {"files": [{"key": "ndc/../../evil", "sha256": "x"}]}
    _seed(settings, {"ndc/file.zip": b"data"}, manifest)

    with pytest.raises(RuntimeError, match="outside ndc/"):
        _fetch_source("ndc", settings)


def test_missing_raw_store_is_explained(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path, raw_store=None)
    with pytest.raises(RuntimeError, match="RAW_STORE not configured"):
        _fetch_source("ndc", settings)


def test_sha256_correctness(tmp_path: Path) -> None:
    f = tmp_path / "f.bin"
    f.write_bytes(b"hello world")
    assert _sha256(f) == hashlib.sha256(b"hello world").hexdigest()
