"""Strip downloaded DailyMed OTC release zips down to label XML, ready to mirror.

Usage:
    uv run python pipeline/scripts/slim_dailymed.py /path/to/release-zips /path/to/slim
    uv run python pipeline/scripts/mirror.py dailymed-otc /path/to/slim
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from nomi_pipeline.fetch.dailymed import slim_otc_release


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("src_dir", type=Path, help="folder of dm_spl_release_human_otc_part*.zip")
    parser.add_argument("dest_dir", type=Path, help="folder for the XML-only zips")
    args = parser.parse_args()

    parts = sorted(args.src_dir.glob("dm_spl_release_human_otc_part*.zip"))
    if not parts:
        print(f"no dm_spl_release_human_otc_part*.zip in {args.src_dir}", file=sys.stderr)
        sys.exit(1)

    logging.basicConfig(level="INFO", format="%(levelname)s %(name)s: %(message)s")
    args.dest_dir.mkdir(parents=True, exist_ok=True)
    total = slimmed = 0
    for part in parts:
        dest = args.dest_dir / part.name.replace(".zip", ".xml.zip")
        if dest.exists():
            print(f"skipping {part.name}, {dest.name} already exists")
            continue
        total += slim_otc_release(part, dest)
        slimmed += 1
    print(f"done: {total} labels from {slimmed} new parts ({len(parts) - slimmed} skipped)")


if __name__ == "__main__":
    main()
