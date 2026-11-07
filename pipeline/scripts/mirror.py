"""Upload a local directory of raw files to the raw data store and update manifest.json.

Run this after downloading new files from the public URLs. Files are added to the existing
manifest, so you can mirror just the new FAERS quarter without losing the older ones.
Requires RAW_STORE and a write-scoped HF_TOKEN in .env (see ADR-0003).

Usage:
    uv run python pipeline/scripts/mirror.py ndc /path/to/ndc/files
    uv run python pipeline/scripts/mirror.py dailymed-otc /path/to/slimmed/dailymed  (see slim_dailymed.py)
    uv run python pipeline/scripts/mirror.py faers /path/to/faers/files

Get the files with download_sources.py.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from nomi_pipeline.config import Settings
from nomi_pipeline.fetch import SOURCES
from nomi_pipeline.fetch.mirror import mirror


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=SOURCES)
    parser.add_argument("local_dir", type=Path, help="directory of downloaded files")
    args = parser.parse_args()

    if not args.local_dir.is_dir():
        print(f"not a directory: {args.local_dir}", file=sys.stderr)
        sys.exit(1)

    settings = Settings()
    logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s: %(message)s")
    try:
        mirror(args.source, args.local_dir, settings)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
