"""Download the raw sources from FDA and NLM, ready to slim and mirror.

Only the person mirroring needs this; everyone else runs `uv run pipeline fetch all`.
Files that are already complete (same size as the server reports) are skipped and partial
downloads resume, so the script can be rerun after an interruption.

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
import zipfile
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


class _Missing(Exception):
    """The server says the file does not exist (404)."""


def _remote_info(url: str) -> tuple[int, str | None]:
    """Return the file size and a validator (ETag or Last-Modified) for resuming safely."""
    # fis.fda.gov sends no Content-Length on HEAD, so ask for one byte and read Content-Range.
    request = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                headers = response.headers
                validator = headers.get("ETag") or headers.get("Last-Modified")
                total = headers.get("Content-Range", "").rpartition("/")[2]
                if total.isdigit():
                    return int(total), validator
                if response.status == 200 and headers.get("Content-Length", "").isdigit():
                    return int(headers["Content-Length"]), validator
                raise RuntimeError(f"{url}: server did not report a size")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise _Missing(url) from e
            if e.code < 500 or attempt == ATTEMPTS:
                raise
        except (TimeoutError, ConnectionError, urllib.error.URLError):
            if attempt == ATTEMPTS:
                raise
        time.sleep(5 * attempt)
    raise AssertionError("unreachable")


def _download(url: str, dest: Path) -> None:
    """Download url to dest unless it is already complete. Raises _Missing on 404."""
    size, validator = _remote_info(url)
    if dest.exists() and dest.stat().st_size == size:
        print(f"already complete: {dest.name}")
        return
    print(f"downloading {dest.name} ({size / 2**20:,.0f} MB)")
    tmp = dest.with_suffix(dest.suffix + ".partial")
    meta = dest.with_suffix(dest.suffix + ".partial.validator")
    # Only resume a partial file that came from this exact version of the file. NDC and
    # DailyMed keep the same URL when their contents change.
    if tmp.exists() and (not validator or not meta.exists() or meta.read_text() != validator):
        tmp.unlink()
    if validator:
        meta.write_text(validator)
    for attempt in range(1, ATTEMPTS + 1):
        # Resume from the partial file; fis.fda.gov often stalls partway through a quarter.
        have = tmp.stat().st_size if tmp.exists() else 0
        if have > size:
            tmp.unlink()
            have = 0
        if have == size:
            break
        headers = {"Range": f"bytes={have}-", "If-Range": validator} if have and validator else {}
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                # 206 means the server is continuing our partial file; 200 means start over.
                mode = "ab" if response.status == 206 else "wb"
                with tmp.open(mode) as f:
                    shutil.copyfileobj(response, f, length=1 << 20)
        except (TimeoutError, ConnectionError, urllib.error.URLError) as e:
            if attempt == ATTEMPTS:
                raise
            done = tmp.stat().st_size if tmp.exists() else 0
            print(f"  stalled at {done / 2**20:,.0f} MB ({e}), resuming in {5 * attempt}s")
            time.sleep(5 * attempt)
    if not tmp.exists() or tmp.stat().st_size != size:
        got = tmp.stat().st_size if tmp.exists() else 0
        raise RuntimeError(f"{dest.name}: got {got} bytes, expected {size}")
    try:
        with zipfile.ZipFile(tmp) as z:
            bad = z.testzip()
    except zipfile.BadZipFile as e:
        bad = str(e)
    if bad:
        tmp.unlink()
        raise RuntimeError(f"{dest.name}: corrupt zip ({bad}), deleted; rerun to download again")
    tmp.replace(dest)
    meta.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=("ndc", "dailymed-otc", "faers"))
    parser.add_argument("dest_dir", type=Path)
    args = parser.parse_args()
    args.dest_dir.mkdir(parents=True, exist_ok=True)

    failed: list[str] = []

    def fetch(url: str) -> bool:
        """Download one file. Returns False if it is not published or could not be fetched."""
        name = url.rsplit("/", 1)[1]
        try:
            _download(url, args.dest_dir / name)
            return True
        except _Missing:
            return False
        except (OSError, RuntimeError, urllib.error.URLError) as e:
            print(f"  giving up on {name} for now: {e}")
            failed.append(name)
            return False

    if args.source == "ndc":
        fetch(NDC_URL)
    elif args.source == "dailymed-otc":
        # Parts are numbered from 1; stop at the first missing one (or the first failure,
        # since we can't tell whether more parts follow it).
        n = 1
        while fetch(DAILYMED_URL.format(n=n)):
            n += 1
    else:
        this_year = datetime.now(UTC).year
        for year in range(FAERS_FIRST_YEAR, this_year + 1):
            for quarter in range(1, 5):
                url = FAERS_URL.format(year=year, quarter=quarter)
                if not fetch(url) and url.rsplit("/", 1)[1] not in failed:
                    print(f"not published yet: {year}Q{quarter}")

    if failed:
        print(f"{len(failed)} files failed; rerun to resume them: {', '.join(failed)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
