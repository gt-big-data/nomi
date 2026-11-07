"""Strip DailyMed OTC release zips down to their label XML before mirroring (ADR-0003).

Each release part holds one inner zip per label (otc/<date>_<setid>.zip) with the SPL XML
and product images. The XML is under 1% of the bytes and is all the pipeline reads.
"""

from __future__ import annotations

import io
import logging
import zipfile
from pathlib import Path, PurePosixPath

log = logging.getLogger(__name__)


def slim_otc_release(src: Path, dest: Path) -> int:
    """Write a zip of only the label XML in src, named <date>_<setid>.xml. Returns the count."""
    count = 0
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with zipfile.ZipFile(src) as outer, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for info in outer.infolist():
            if not info.filename.endswith(".zip"):
                continue
            stem = PurePosixPath(info.filename).stem
            with zipfile.ZipFile(io.BytesIO(outer.read(info))) as inner:
                xmls = [n for n in inner.namelist() if n.lower().endswith(".xml")]
                if not xmls:
                    log.warning("no XML in %s", info.filename)
                for name in xmls:
                    arcname = f"{stem}.xml" if len(xmls) == 1 else f"{stem}_{name}"
                    out.writestr(arcname, inner.read(name))
                    count += 1
    tmp.replace(dest)
    log.info("slimmed %s to %s (%d labels)", src.name, dest.name, count)
    return count
