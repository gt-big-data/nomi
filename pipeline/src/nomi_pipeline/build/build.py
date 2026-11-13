import hashlib
import json
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl
from fsspec.core import url_to_fs

from nomi_pipeline.config import Settings

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def build_database(product_parquet: Path, db_path: Path, dataset_version: str) -> dict[str, int]:
    db_path.unlink(missing_ok=True)
    products = pl.read_parquet(product_parquet).to_dicts()

    con = sqlite3.connect(str(db_path))
    con.executescript(SCHEMA_PATH.read_text())

    counts = {"products": 0, "product_ingredients": 0, "ingredients": 0, "product_uses": 0}
    seen_uniis: set[str] = set()
    for product in products:
        con.execute(
            "INSERT INTO products (ndc11, set_id, brand, generic, form, category, scope_flag, review_status)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                product["ndc11"],
                product["spl_set_id"],
                product["brand_name"],
                product["generic_name"],
                product["dosage_form"],
                # otc_category/scope come from #26, review_status from no ticket yet;
                # .get() avoids crashing until #26 lands
                product.get("otc_category"),
                product.get("scope"),
                product.get("review_status"),
            ),
        )
        counts["products"] += 1

        for ingredient in product["ingredients"]:
            con.execute(
                "INSERT INTO product_ingredients (ndc11, unii, strength, unit) VALUES (?, ?, ?, ?)",
                (product["ndc11"], ingredient["unii"], ingredient["strength"], ingredient["unit"]),
            )
            counts["product_ingredients"] += 1

            unii = ingredient["unii"]
            if unii not in seen_uniis:
                con.execute(
                    "INSERT INTO ingredients (unii, name) VALUES (?, ?)",
                    (unii, ingredient["name"]),
                )
                counts["ingredients"] += 1
                seen_uniis.add(unii)

        # no ticket populates uses on product.parquet yet; default to [] so this loop
        for use in product.get("uses", []):
            con.execute(
                "INSERT INTO product_uses (ndc11, use) VALUES (?, ?)",
                (product["ndc11"], use),
            )
            counts["product_uses"] += 1

    con.execute(
        "INSERT INTO meta (dataset_version, model_version, rubric_version, built_at) "
        "VALUES (?, ?, ?, ?)",
        (dataset_version, None, None, datetime.now(UTC).isoformat()),
    )

    con.commit()
    con.close()
    return counts


def write_manifest(
    product_parquet: Path, counts: dict[str, int], dataset_version: str, manifest_path: Path
) -> dict[str, Any]:
    digest = hashlib.sha256(product_parquet.read_bytes()).hexdigest()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()

    manifest = {
        "version": dataset_version,
        "input_hashes": {product_parquet.name: digest},
        "commit": commit,
        "counts": counts,
    }

    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def publish(db_path: Path, manifest_path: Path, dataset_version: str, settings: Settings) -> str:
    if not settings.dataset_store:
        raise RuntimeError(
            "DATASET_STORE not configured. Copy .env.example to .env and fill it in."
        )

    options: dict[str, Any] = {}
    if settings.hf_token and settings.dataset_store.startswith("hf://"):
        options["token"] = settings.hf_token

    fs, root = url_to_fs(settings.dataset_store, **options)
    root = root.rstrip("/")
    prefix = f"{root}/datasets/{dataset_version}"
    fs.put_file(str(db_path), f"{prefix}/nomi.sqlite")
    fs.put_file(str(manifest_path), f"{prefix}/manifest.json")

    return prefix
