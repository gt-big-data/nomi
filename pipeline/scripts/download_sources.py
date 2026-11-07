"""Download the raw sources from FDA and NLM, ready to slim and mirror.

Only the person mirroring needs this; everyone else runs `uv run pipeline fetch all`.
Files that are already complete (same size as the server reports) are skipped, so the
script can be rerun after an interruption.

Usage:
    uv run python pipeline/scripts/download_sources.py ndc /path/to/downloads/ndc
    uv run python pipeline/scripts/download_sources.py dailymed-otc /path/to/downloads/dailymed
    uv run python pipeline/scripts/download_sources.py faers /path/to/downloads/faers
"""

from __future__ import annotations

import argparse
import shutil
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

NDC_URL = "https://download.open.fda.gov/drug/ndc/drug-ndc-0001-of-0001.json.zip"
DAILYMED_URL = (
    "https://dailymed-data.nlm.nih.gov/public-release-files/dm_spl_release_human_otc_part{n}.zip"
)
FAERS_URL = "https://fis.fda.gov/content/Exports/faers_ascii_{year}q{quarter}.zip"
FAERS_FIRST_YEAR = 2014


def _remote_size(url: str) -> int | None:
    """Return the file size, or None if the server says it does not exist."""
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            length = response.headers.get("Content-Length")
            return int(length) if length else -1
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def _download(url: str, dest: Path) -> bool:
    """Download url to dest unless it is already complete. Returns False on 404."""
    size = _remote_size(url)
    if size is None:
        return False
    if dest.exists() and dest.stat().st_size == size:
        print(f"already complete: {dest.name}")
        return True
    print(f"downloading {dest.name} ({size / 2**20:,.0f} MB)")
    tmp = dest.with_suffix(dest.suffix + ".partial")
    with urllib.request.urlopen(url, timeout=60) as response, tmp.open("wb") as f:
        shutil.copyfileobj(response, f, length=1 << 20)
    tmp.replace(dest)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("ndc", "dailymed-otc", "faers"))
    parser.add_argument("dest_dir", type=Path)
    args = parser.parse_args()
    args.dest_dir.mkdir(parents=True, exist_ok=True)

    if args.source == "ndc":
        _download(NDC_URL, args.dest_dir / NDC_URL.rsplit("/", 1)[1])
    elif args.source == "dailymed-otc":
        n = 1
        while _download(url := DAILYMED_URL.format(n=n), args.dest_dir / url.rsplit("/", 1)[1]):
            n += 1
    else:
        this_year = datetime.now(UTC).year
        for year in range(FAERS_FIRST_YEAR, this_year + 1):
            for quarter in range(1, 5):
                url = FAERS_URL.format(year=year, quarter=quarter)
                if not _download(url, args.dest_dir / url.rsplit("/", 1)[1]):
                    print(f"not published yet: {year}Q{quarter}")


if __name__ == "__main__":
    main()
