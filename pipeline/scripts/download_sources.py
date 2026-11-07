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
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import truststore

# Use the OS certificate store; python.org builds and campus proxies fail with the default one.
truststore.inject_into_ssl()

NDC_URL = "https://download.open.fda.gov/drug/ndc/drug-ndc-0001-of-0001.json.zip"
DAILYMED_URL = (
    "https://dailymed-data.nlm.nih.gov/public-release-files/dm_spl_release_human_otc_part{n}.zip"
)
FAERS_URL = "https://fis.fda.gov/content/Exports/faers_ascii_{year}q{quarter}.zip"
FAERS_FIRST_YEAR = 2014
TIMEOUT = 120
ATTEMPTS = 8


def _remote_size(url: str) -> int | None:
    """Return the file size, or None if the server says it does not exist."""
    # fis.fda.gov sends no Content-Length on HEAD, so ask for one byte and read Content-Range.
    request = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            content_range = response.headers.get("Content-Range", "")
            if "/" in content_range:
                return int(content_range.rsplit("/", 1)[1])
            return int(response.headers["Content-Length"])
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
    for attempt in range(1, ATTEMPTS + 1):
        # Resume from the partial file; fis.fda.gov often stalls partway through a quarter.
        have = tmp.stat().st_size if tmp.exists() else 0
        if have >= size:
            break
        request = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                resumed = response.status == 206
                with tmp.open("ab" if resumed else "wb") as f:
                    shutil.copyfileobj(response, f, length=1 << 20)
            break
        except (TimeoutError, ConnectionError, urllib.error.URLError) as e:
            if attempt == ATTEMPTS:
                raise
            done = tmp.stat().st_size if tmp.exists() else 0
            print(f"  stalled at {done / 2**20:,.0f} MB ({e}), resuming in {5 * attempt}s")
            time.sleep(5 * attempt)
    if tmp.stat().st_size != size:
        raise RuntimeError(f"{dest.name}: got {tmp.stat().st_size} bytes, expected {size}")
    tmp.replace(dest)
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("ndc", "dailymed-otc", "faers"))
    parser.add_argument("dest_dir", type=Path)
    args = parser.parse_args()
    args.dest_dir.mkdir(parents=True, exist_ok=True)

    failed: list[str] = []

    def fetch(url: str) -> bool:
        """Download one file; on repeated failure note it and keep going with the rest."""
        name = url.rsplit("/", 1)[1]
        try:
            return _download(url, args.dest_dir / name)
        except (OSError, RuntimeError, urllib.error.URLError) as e:
            print(f"  giving up on {name} for now: {e}")
            failed.append(name)
            return True

    if args.source == "ndc":
        fetch(NDC_URL)
    elif args.source == "dailymed-otc":
        n = 1
        while fetch(DAILYMED_URL.format(n=n)):
            n += 1
    else:
        this_year = datetime.now(UTC).year
        for year in range(FAERS_FIRST_YEAR, this_year + 1):
            for quarter in range(1, 5):
                if not fetch(FAERS_URL.format(year=year, quarter=quarter)):
                    print(f"not published yet: {year}Q{quarter}")

    if failed:
        print(f"{len(failed)} files failed; rerun to resume them: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
