from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from nomi_pipeline.config import Settings
from nomi_pipeline.fetch.mirror import mirror


class FakeR2:
    """In-memory stand-in for the R2 client, keyed by object key."""

    def __init__(self, objects: dict[str, bytes] | None = None) -> None:
        self.objects: dict[str, bytes] = dict(objects or {})

    def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:  # noqa: N803
        if Key not in self.objects:
            raise ClientError({"Error": {"Code": "NoSuchKey"}}, "GetObject")
        return {"Body": MagicMock(read=MagicMock(return_value=self.objects[Key]))}

    def upload_file(self, filename: str, bucket: str, key: str) -> None:
        self.objects[key] = Path(filename).read_bytes()

    def put_object(self, Bucket: str, Key: str, Body: bytes) -> None:  # noqa: N803
        self.objects[Key] = Body

    def manifest(self, source: str) -> dict[str, Any]:
        result: dict[str, Any] = json.loads(self.objects[f"{source}/manifest.json"])
        return result


def _settings(r2: FakeR2) -> Settings:
    m = MagicMock(spec=Settings)
    m.r2_bucket = "test-bucket"
    m.r2_client.return_value = r2
    return cast(Settings, m)


def _keys(manifest: dict[str, Any]) -> list[str]:
    return [e["key"] for e in manifest["files"]]


def test_mirror_adds_to_existing_manifest(tmp_path: Path) -> None:
    r2 = FakeR2()
    q1 = tmp_path / "q1"
    q1.mkdir()
    (q1 / "faers_2024Q1.zip").write_bytes(b"q1")
    mirror("faers", q1, _settings(r2))

    q2 = tmp_path / "q2"
    q2.mkdir()
    (q2 / "faers_2024Q2.zip").write_bytes(b"q2")
    mirror("faers", q2, _settings(r2))

    assert _keys(r2.manifest("faers")) == ["faers/faers_2024Q1.zip", "faers/faers_2024Q2.zip"]


def test_mirror_replaces_entry_for_same_key(tmp_path: Path) -> None:
    r2 = FakeR2()
    (tmp_path / "ndc.json").write_bytes(b"old")
    mirror("ndc", tmp_path, _settings(r2))
    (tmp_path / "ndc.json").write_bytes(b"new")
    mirror("ndc", tmp_path, _settings(r2))

    files = r2.manifest("ndc")["files"]
    assert len(files) == 1
    assert files[0]["sha256"] == hashlib.sha256(b"new").hexdigest()


def test_mirror_keeps_subfolders_in_keys(tmp_path: Path) -> None:
    r2 = FakeR2()
    for part in ("part1", "part2"):
        (tmp_path / part).mkdir()
        (tmp_path / part / "labels.zip").write_bytes(part.encode())
    mirror("dailymed-otc", tmp_path, _settings(r2))

    assert _keys(r2.manifest("dailymed-otc")) == [
        "dailymed-otc/part1/labels.zip",
        "dailymed-otc/part2/labels.zip",
    ]


def test_mirror_skips_local_manifest(tmp_path: Path) -> None:
    r2 = FakeR2()
    (tmp_path / "ndc.json").write_bytes(b"data")
    (tmp_path / "manifest.json").write_text("{}")
    mirror("ndc", tmp_path, _settings(r2))

    assert _keys(r2.manifest("ndc")) == ["ndc/ndc.json"]


def test_mirror_rejects_unknown_source(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown source"):
        mirror("nope", tmp_path, _settings(FakeR2()))
