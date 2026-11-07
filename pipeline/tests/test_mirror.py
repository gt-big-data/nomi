from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from fsspec.core import url_to_fs
from nomi_pipeline.config import Settings
from nomi_pipeline.fetch import _fetch_source
from nomi_pipeline.fetch.mirror import mirror


def _settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data", raw_store=f"memory://{tmp_path.name}")


def _manifest(settings: Settings, source: str) -> dict[str, Any]:
    assert settings.raw_store
    fs, root = url_to_fs(settings.raw_store)
    result: dict[str, Any] = json.loads(fs.cat_file(f"{root}/{source}/manifest.json"))
    return result


def _keys(manifest: dict[str, Any]) -> list[str]:
    return [e["key"] for e in manifest["files"]]


def _folder(tmp_path: Path, name: str, files: dict[str, bytes]) -> Path:
    folder = tmp_path / name
    for rel, content in files.items():
        (folder / rel).parent.mkdir(parents=True, exist_ok=True)
        (folder / rel).write_bytes(content)
    return folder


def test_mirror_adds_to_existing_manifest(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    mirror("faers", _folder(tmp_path, "q1", {"faers_2024Q1.zip": b"q1"}), settings)
    mirror("faers", _folder(tmp_path, "q2", {"faers_2024Q2.zip": b"q2"}), settings)

    assert _keys(_manifest(settings, "faers")) == [
        "faers/faers_2024Q1.zip",
        "faers/faers_2024Q2.zip",
    ]


def test_mirror_replaces_entry_for_same_key(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    mirror("ndc", _folder(tmp_path, "a", {"ndc.json": b"old"}), settings)
    mirror("ndc", _folder(tmp_path, "b", {"ndc.json": b"new"}), settings)

    files = _manifest(settings, "ndc")["files"]
    assert len(files) == 1
    assert files[0]["sha256"] == hashlib.sha256(b"new").hexdigest()


def test_mirror_keeps_subfolders_in_keys(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    folder = _folder(tmp_path, "dm", {"part1/labels.zip": b"1", "part2/labels.zip": b"2"})
    mirror("dailymed-otc", folder, settings)

    assert _keys(_manifest(settings, "dailymed-otc")) == [
        "dailymed-otc/part1/labels.zip",
        "dailymed-otc/part2/labels.zip",
    ]


def test_mirror_skips_local_manifest(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    mirror("ndc", _folder(tmp_path, "n", {"ndc.json": b"data", "manifest.json": b"{}"}), settings)

    assert _keys(_manifest(settings, "ndc")) == ["ndc/ndc.json"]


def test_mirror_then_fetch_round_trip(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    mirror("faers", _folder(tmp_path, "q", {"faers_2024Q1.zip": b"reports"}), settings)

    _fetch_source("faers", settings)

    assert (tmp_path / "data" / "raw" / "faers" / "faers_2024Q1.zip").read_bytes() == b"reports"


def test_mirror_rejects_unknown_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown source"):
        mirror("nope", tmp_path, _settings(tmp_path))
