import hashlib
import json
import os
import sqlite3
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl
from fsspec.core import url_to_fs

from nomi_pipeline.config import REPO_ROOT, Settings

# The app's tables; the app refuses a file whose user_version differs from its own.
SCHEMA_PATH = REPO_ROOT / "packages" / "schema" / "sqlite" / "nomi.sql"


def git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def build_time() -> str:
    """SOURCE_DATE_EPOCH, else the commit time, so rebuilding the same inputs gives the same file."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH") or git("log", "-1", "--format=%ct")
    return datetime.fromtimestamp(int(epoch), UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def scope_flag(product: dict[str, Any]) -> str:
    """The app scores only in_scope, so a product without a scope yet (#26) is never in_scope."""
    if product["marketing_category"] == "unapproved_homeopathic":
        return "homeopathic"
    return str(product.get("scope") or "out_of_scope")


def build_database(
    product_parquet: Path,
    identity_results: Path,
    db_path: Path,
    dataset_version: str,
    built_at: str,
) -> dict[str, int]:
    """Write the resolved products to db_path.

    Product records keep only the NDC11, which can't be turned back into the barcode's digits, so
    each product's dashed package NDC comes from the identity stage's resolved results.
    """
    db_path.unlink(missing_ok=True)
    products = pl.read_parquet(product_parquet).to_dicts()
    package_ndcs = dict(
        pl.read_parquet(identity_results)
        .filter(pl.col("status") == "resolved")
        .select("expected_ndc11", "ndc_raw")
        .iter_rows()
    )

    con = sqlite3.connect(str(db_path))
    con.executescript(SCHEMA_PATH.read_text())

    counts = {"products": 0, "product_ingredients": 0, "ingredients": 0}
    seen_uniis: set[str] = set()
    for product in products:
        package_ndc = package_ndcs[product["ndc11"]]
        con.execute(
            "INSERT INTO products (package_ndc, ndc10, ndc11, set_id, brand, generic, form, "
            "category, scope_flag, review_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                package_ndc,
                package_ndc.replace("-", ""),
                product["ndc11"],
                product["spl_set_id"],
                product["brand_name"],
                product["generic_name"],
                product["dosage_form"],
                # otc_category comes from #26, review_status from no ticket yet;
                # .get() avoids crashing until #26 lands
                product.get("otc_category"),
                scope_flag(product),
                product.get("review_status"),
            ),
        )
        counts["products"] += 1

        for ingredient in product["ingredients"]:
            con.execute(
                "INSERT INTO product_ingredients "
                "(package_ndc, unii, strength, unit, per_amount, per_unit) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    package_ndc,
                    ingredient["unii"],
                    ingredient["strength"],
                    ingredient["unit"],
                    ingredient["per_amount"],
                    ingredient["per_unit"],
                ),
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

    con.execute(
        "INSERT INTO meta (dataset_version, model_version, rubric_version, built_at) "
        "VALUES (?, ?, ?, ?)",
        (dataset_version, None, None, built_at),
    )

    con.commit()
    con.close()
    return counts


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(
    inputs: list[Path],
    db_path: Path,
    counts: dict[str, int],
    dataset_version: str,
    manifest_path: Path,
) -> dict[str, Any]:
    manifest = {
        "version": dataset_version,
        "sha256": sha256(db_path),
        "size": db_path.stat().st_size,
        "input_hashes": {path.name: sha256(path) for path in inputs},
        "commit": git("rev-parse", "HEAD"),
        # Uncommitted changes mean the commit alone can't rebuild this file.
        "dirty": bool(git("status", "--porcelain")),
        "counts": counts,
    }

    manifest_path.write_text(json.dumps(manifest, indent=2))
    return manifest


def publish(
    db_path: Path,
    manifest_path: Path,
    dataset_version: str,
    settings: Settings,
    overwrite: bool = False,
) -> str:
    options: dict[str, Any] = {}
    if settings.hf_token and settings.dataset_store.startswith("hf://"):
        options["token"] = settings.hf_token

    fs, root = url_to_fs(settings.dataset_store, **options)
    root = root.rstrip("/")
    prefix = f"{root}/datasets/{dataset_version}"
    # The manifest goes up last, so it marks a finished publish.
    if not overwrite and fs.exists(f"{prefix}/manifest.json"):
        raise FileExistsError(f"{dataset_version} is already published at {prefix}")
    fs.put_file(str(db_path), f"{prefix}/nomi.sqlite")
    fs.put_file(str(manifest_path), f"{prefix}/manifest.json")

    return prefix
