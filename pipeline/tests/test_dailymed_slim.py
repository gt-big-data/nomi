from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pytest
from nomi_pipeline.fetch.dailymed import slim_otc_release


def _inner_zip(files: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


def test_slim_keeps_only_label_xml(tmp_path: Path) -> None:
    src = tmp_path / "dm_spl_release_human_otc_part1.zip"
    with zipfile.ZipFile(src, "w") as outer:
        outer.writestr(
            "otc/20261104_set-a.zip",
            _inner_zip({"doc-a.xml": b"<document/>", "photo.jpg": b"\xff" * 1000}),
        )
        outer.writestr(
            "otc/20261104_set-b.zip", _inner_zip({"doc-b.xml": b"<document>b</document>"})
        )
        outer.writestr("otc/20261104_set-c.zip", _inner_zip({"photo.jpg": b"\xff"}))
    dest = tmp_path / "dm_spl_release_human_otc_part1.xml.zip"

    count = slim_otc_release(src, dest)

    assert count == 2
    with zipfile.ZipFile(dest) as z:
        assert z.namelist() == ["20261104_set-a.xml", "20261104_set-b.xml"]
        assert z.read("20261104_set-b.xml") == b"<document>b</document>"
    assert not dest.with_suffix(".zip.partial").exists()


def test_slim_corrupt_inner_zip_leaves_no_output(tmp_path: Path) -> None:
    src = tmp_path / "dm_spl_release_human_otc_part1.zip"
    with zipfile.ZipFile(src, "w") as outer:
        outer.writestr("otc/20261104_set-a.zip", b"not a zip")
    dest = tmp_path / "out.xml.zip"

    with pytest.raises(zipfile.BadZipFile):
        slim_otc_release(src, dest)

    assert not dest.exists()
    assert not (tmp_path / "out.xml.zip.partial").exists()
