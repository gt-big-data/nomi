from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fsspec.core import url_to_fs
from huggingface_hub import HfApi, HfFileSystem
from huggingface_hub.hf_file_system import HfFileSystemResolvedRepositoryPath
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
    mirror("faers", _folder(tmp_path, "q1", {"faers_ascii_2024q1.zip": b"q1"}), settings)
    mirror("faers", _folder(tmp_path, "q2", {"faers_ascii_2024q2.zip": b"q2"}), settings)

    assert _keys(_manifest(settings, "faers")) == [
        "faers/faers_ascii_2024q1.zip",
        "faers/faers_ascii_2024q2.zip",
    ]


def test_mirror_replaces_entry_for_same_key(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    mirror("ndc", _folder(tmp_path, "a", {"drug-ndc-0001-of-0001.json.zip": b"old"}), settings)
    mirror("ndc", _folder(tmp_path, "b", {"drug-ndc-0001-of-0001.json.zip": b"new"}), settings)

    files = _manifest(settings, "ndc")["files"]
    assert len(files) == 1
    assert files[0]["sha256"] == hashlib.sha256(b"new").hexdigest()


def test_mirror_uploads_only_source_files(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    folder = _folder(
        tmp_path,
        "f",
        {
            "faers_ascii_2024q1.zip": b"q1",
            "faers_ascii_2024q2.zip.partial": b"half",
            ".DS_Store": b"",
            ".env": b"HF_TOKEN=secret",
            "sub/faers_ascii_2024q3.zip": b"q3",
        },
    )
    mirror("faers", folder, settings)

    assert _keys(_manifest(settings, "faers")) == ["faers/faers_ascii_2024q1.zip"]
    fs, root = url_to_fs(settings.raw_store or "")
    assert sorted(fs.ls(f"{root}/faers", detail=False)) == [
        f"{root}/faers/faers_ascii_2024q1.zip",
        f"{root}/faers/manifest.json",
    ]


def test_mirror_with_no_source_files_fails(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="no faers_ascii"):
        mirror("faers", _folder(tmp_path, "f", {"notes.txt": b"x"}), _settings(tmp_path))


def test_mirror_skips_unchanged_files(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    folder = _folder(tmp_path, "f", {"faers_ascii_2024q1.zip": b"q1"})
    first = mirror("faers", folder, settings)
    second = mirror("faers", folder, settings)

    assert second["generated_at"] == first["generated_at"]


def _fake_hf_repo(monkeypatch: pytest.MonkeyPatch, revision: str = "main") -> None:
    # Keep the Hugging Face tests offline: resolve paths without asking the Hub.
    resolved = HfFileSystemResolvedRepositoryPath("dataset", "org/raw", revision, "")
    monkeypatch.setattr(HfFileSystem, "resolve_path", lambda self, path, **k: resolved)


def test_mirror_to_hugging_face_makes_one_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: dict[str, Any] = {}

    def fake_commit(self: HfApi, **kwargs: Any) -> None:
        calls.update(kwargs)

    monkeypatch.setattr(HfApi, "create_commit", fake_commit)
    monkeypatch.setattr(HfApi, "repo_info", lambda self, *a, **k: SimpleNamespace(sha="abc123"))
    monkeypatch.setattr(HfFileSystem, "exists", lambda self, path, **k: False)
    _fake_hf_repo(monkeypatch)
    settings = Settings(data_dir=tmp_path, raw_store="hf://datasets/org/raw")

    mirror("ndc", _folder(tmp_path, "n", {"drug-ndc-0001-of-0001.json.zip": b"d"}), settings)

    assert calls["repo_id"] == "org/raw"
    assert calls["repo_type"] == "dataset"
    assert calls["parent_commit"] == "abc123"
    assert [op.path_in_repo for op in calls["operations"]] == [
        "ndc/drug-ndc-0001-of-0001.json.zip",
        "ndc/manifest.json",
    ]


def test_mirror_refuses_pinned_hugging_face_store(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_hf_repo(monkeypatch, revision="a" * 40)
    settings = Settings(data_dir=tmp_path, raw_store=f"hf://datasets/org/raw@{'a' * 40}")
    folder = _folder(tmp_path, "n", {"drug-ndc-0001-of-0001.json.zip": b"d"})
    with pytest.raises(RuntimeError, match="pinned to a commit"):
        mirror("ndc", folder, settings)


def test_mirror_skips_local_manifest(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    mirror(
        "ndc",
        _folder(tmp_path, "n", {"drug-ndc-0001-of-0001.json.zip": b"data", "manifest.json": b"{}"}),
        settings,
    )

    assert _keys(_manifest(settings, "ndc")) == ["ndc/drug-ndc-0001-of-0001.json.zip"]


def test_mirror_then_fetch_round_trip(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    mirror("faers", _folder(tmp_path, "q", {"faers_ascii_2024q1.zip": b"reports"}), settings)

    _fetch_source("faers", settings)

    assert (
        tmp_path / "data" / "raw" / "faers" / "faers_ascii_2024q1.zip"
    ).read_bytes() == b"reports"


def test_mirror_rejects_unknown_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown source"):
        mirror("nope", tmp_path, _settings(tmp_path))
