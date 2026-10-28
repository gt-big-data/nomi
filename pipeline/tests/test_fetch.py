from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from nomi_pipeline.config import Settings
from nomi_pipeline.fetch import _fetch_source, _sha256


def _mock_settings(tmp_path: Path) -> Settings:
    m = MagicMock(spec=Settings)
    m.raw_dir = tmp_path / "raw"
    m.r2_bucket = "test-bucket"
    return cast(Settings, m)


def _mock_client(manifest: dict[str, Any], file_contents: dict[str, bytes]) -> Any:
    client = MagicMock()
    client.get_object.return_value = {
        "Body": MagicMock(read=MagicMock(return_value=json.dumps(manifest).encode()))
    }

    def download_file(bucket: str, key: str, filename: str) -> None:
        Path(filename).write_bytes(file_contents.get(key, b""))

    client.download_file.side_effect = download_file
    return client


def test_fetch_downloads_and_verifies(tmp_path: Path) -> None:
    content = b"ndc data"
    sha = hashlib.sha256(content).hexdigest()
    manifest: dict[str, Any] = {
        "files": [{"key": "ndc/file.zip", "sha256": sha, "size_bytes": len(content)}]
    }
    settings = _mock_settings(tmp_path)
    settings.r2_client.return_value = _mock_client(manifest, {"ndc/file.zip": content})  # type: ignore[union-attr]

    _fetch_source("ndc", settings)

    assert (tmp_path / "raw" / "ndc" / "file.zip").read_bytes() == content
    assert (tmp_path / "raw" / "ndc" / "manifest.json").exists()


def test_already_fresh_skips_download(tmp_path: Path) -> None:
    content = b"existing data"
    sha = hashlib.sha256(content).hexdigest()
    manifest: dict[str, Any] = {
        "files": [{"key": "ndc/file.zip", "sha256": sha, "size_bytes": len(content)}]
    }
    local = tmp_path / "raw" / "ndc" / "file.zip"
    local.parent.mkdir(parents=True)
    local.write_bytes(content)

    settings = _mock_settings(tmp_path)
    client = _mock_client(manifest, {})
    settings.r2_client.return_value = client  # type: ignore[union-attr]

    _fetch_source("ndc", settings)

    client.download_file.assert_not_called()


def test_corrupted_file_raises_and_cleans_up(tmp_path: Path) -> None:
    good_sha = hashlib.sha256(b"correct").hexdigest()
    manifest: dict[str, Any] = {
        "files": [{"key": "ndc/file.zip", "sha256": good_sha, "size_bytes": 7}]
    }
    settings = _mock_settings(tmp_path)
    settings.r2_client.return_value = _mock_client(manifest, {"ndc/file.zip": b"corrupt"})  # type: ignore[union-attr]

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        _fetch_source("ndc", settings)

    assert not (tmp_path / "raw" / "ndc" / "file.zip").exists()


def test_sha256_correctness(tmp_path: Path) -> None:
    f = tmp_path / "f.bin"
    f.write_bytes(b"hello world")
    assert _sha256(f) == hashlib.sha256(b"hello world").hexdigest()
