"""Upload a local directory of raw files to R2 and write manifest.json.

Run this once per source after downloading the files from the public URLs.
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
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

VALID_SOURCES = ("ndc", "dailymed-otc", "faers")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def mirror(source: str, local_dir: Path) -> None:
    from nomi_pipeline.config import Settings

    settings = Settings()
    client = settings.r2_client()
    bucket = settings.r2_bucket
    if not bucket:
        print("R2_BUCKET not set in .env", file=sys.stderr)
        sys.exit(1)

    files = sorted(p for p in local_dir.rglob("*") if p.is_file())
    if not files:
        print(f"no files found in {local_dir}", file=sys.stderr)
        sys.exit(1)

    entries = []
    for f in files:
        key = f"{source}/{f.name}"
        digest = _sha256(f)
        size = f.stat().st_size
        print(f"uploading {key} ({size:,} bytes)...")
        client.upload_file(str(f), bucket, key)
        entries.append({"key": key, "sha256": digest, "size_bytes": size})

    manifest = {"generated_at": datetime.now(UTC).isoformat(), "files": entries}
    client.put_object(
        Bucket=bucket,
        Key=f"{source}/manifest.json",
        Body=json.dumps(manifest, indent=2).encode(),
    )
    print(f"done — uploaded {len(entries)} files and manifest to {source}/")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", choices=VALID_SOURCES)
    parser.add_argument("local_dir", type=Path, help="directory of downloaded files")
    args = parser.parse_args()

    if not args.local_dir.is_dir():
        print(f"not a directory: {args.local_dir}", file=sys.stderr)
        sys.exit(1)

    mirror(args.source, args.local_dir)


if __name__ == "__main__":
    main()
