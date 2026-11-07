"""Upload a local directory of raw files to R2 and update manifest.json.

Run this after downloading new files from the public URLs. Files are added to the existing
manifest, so you can mirror just the new FAERS quarter without losing the older ones.
Requires write credentials in .env (R2_ACCESS_KEY_ID with Object Read & Write permission).

Usage:
    uv run python pipeline/scripts/mirror.py ndc /path/to/ndc/files
    uv run python pipeline/scripts/mirror.py dailymed-otc /path/to/dailymed/files
    uv run python pipeline/scripts/mirror.py faers /path/to/faers/files

Where to get the files:
    ndc:          https://open.fda.gov/apis/drug/ndc/  (bulk download JSON)
    dailymed-otc: https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm
    faers:        https://www.fda.gov/drugs/...faers-latest-quarterly-data-files (ASCII ZIPs)
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
