import json
import sqlite3
from pathlib import Path

import polars as pl
from fsspec.core import url_to_fs
from nomi_pipeline.build.build import build_database, publish, write_manifest
from nomi_pipeline.config import Settings

SCHEMA_PATH = Path(__file__).parent.parent / "src" / "nomi_pipeline" / "build" / "schema.sql"

EXPECTED_TABLES = {
    "meta",
    "products",
    "product_ingredients",
    "ingredients",
    "product_uses",
    "label_warnings",
    "terms",
    "hard_stops",
    "benchmarks",
    "alternatives",
    "citations",
    "templates",
    "products_fts",
    "interactions",
}


def test_schema_creates_all_expected_tables() -> None:
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA_PATH.read_text())

    rows = con.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view')").fetchall()
    table_names = {row[0] for row in rows}

    for expected in EXPECTED_TABLES:
        assert expected in table_names, f"missing table: {expected}"


FIXTURES = Path(__file__).parent / "fixtures" / "build"


def test_build_database_populates_product_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_database(FIXTURES / "product.parquet", db_path, dataset_version="v0.1.0")

    assert counts["products"] == 2
    assert counts["product_ingredients"] == 3
    assert counts["ingredients"] == 3
    assert counts["product_uses"] == 3

    con = sqlite3.connect(str(db_path))
    row = con.execute(
        "SELECT brand, generic, form, review_status FROM products WHERE ndc11 = ?",
        ("76176013501",),
    ).fetchone()
    assert row == (
        "Vaporizing Chest Rub",
        "camphor, menthol, eucalyptus oil",
        "OINTMENT",
        "preliminary",
    )


def test_shared_ingredient_is_not_duplicated(tmp_path: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_database(
        FIXTURES / "shared_ingredient.parquet", db_path, dataset_version="v0.1.0"
    )

    assert counts["products"] == 2
    assert counts["product_ingredients"] == 2
    assert counts["ingredients"] == 1

    con = sqlite3.connect(str(db_path))
    rows = con.execute(
        "SELECT unii, name FROM ingredients WHERE unii = ?", ("362O9ITL9D",)
    ).fetchall()
    assert len(rows) == 1


def test_meta_data_table(tmp_path: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    build_database(FIXTURES / "product.parquet", db_path, dataset_version="v0.1.0")
    con = sqlite3.connect(str(db_path))
    rows = con.execute("SELECT dataset_version, model_version, built_at FROM meta").fetchall()

    assert len(rows) == 1

    dataset_version, model_version, built_at = rows[0]
    assert dataset_version == "v0.1.0"
    assert model_version is None
    assert built_at is not None


def test_write_manifest_has_expected_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_database(FIXTURES / "product.parquet", db_path, dataset_version="v0.1.0")

    manifest_path = tmp_path / "manifest.json"
    manifest = write_manifest(FIXTURES / "product.parquet", counts, "v0.1.0", manifest_path)

    assert manifest["version"] == "v0.1.0"
    assert manifest["counts"]["products"] == 2
    assert "product.parquet" in manifest["input_hashes"]
    assert len(manifest["input_hashes"]["product.parquet"]) == 64
    assert manifest["commit"]

    import json

    on_disk = json.loads(manifest_path.read_text())
    assert on_disk == manifest

def test_db_handles_real_shape_without_otc_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_database(FIXTURES / "real_shape_product.parquet", db_path=db_path, dataset_version="v0.1.0")

    assert counts["products"] == 1
    assert counts["product_ingredients"] == 1
    assert counts["product_uses"] == 0

    con = sqlite3.connect(str(db_path))
    row = con.execute("SELECT category, scope_flag, review_status FROM products WHERE ndc11 = ?", ("33333333333",),).fetchone()
    assert row == (None, None, None)

def test_publish_uploads_db_and_manifest(tmp_path: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    manifest_path = tmp_path / "manifest.json"
    db_path.write_text("fake db bytes")
    manifest_path.write_text('{"version": "v0.1.0"}')

    settings = Settings(data_dir=tmp_path / "data", dataset_store=f"memory://{tmp_path.name}")
    prefix = publish(db_path, manifest_path, "v0.1.0", settings)
    fs, root = url_to_fs(settings.dataset_store)
    assert fs.exists(f"{prefix}/nomi.sqlite")
    assert fs.exists(f"{prefix}/manifest.json")
    assert fs.cat(f"{prefix}/nomi.sqlite") == b"fake db bytes"

REFERENCE_PRODUCTS_DIR = Path(__file__).parents[2] / "packages" / "schema" / "examples"

def test_build_handles_five_reference_products(tmp_path: Path) -> None:
    product_dir = []
    for entry in sorted(REFERENCE_PRODUCTS_DIR.iterdir()):
        if entry.is_dir():
            product_dir.append(entry)

    products = []
    for p in product_dir:
        product_json = ( p / "product.json").read_text()
        product = json.loads(product_json)
        for ingredient in product["ingredients"]:
            ingredient["strength"] = float(ingredient["strength"])
        products.append(product)

    assert len(products) == 5

    parquet_path = tmp_path / "product.parquet"
    pl.DataFrame(products).write_parquet(parquet_path)

    db_path = tmp_path / "nomi.sqlite"
    counts = build_database(parquet_path, db_path, dataset_version="v0.1.0")

    assert counts["products"] == 5
    assert counts["ingredients"] == 5
    assert counts["product_ingredients"] == 7
    assert counts["product_uses"] == 13

    con = sqlite3.connect(str(db_path))
    meta_row = con.execute("SELECT COUNT(*) FROM meta").fetchone()
    assert meta_row[0] == 1

    not_yet_populated = [
        "hard_stops", "terms", "benchmarks", "alternatives",
        "citations", "templates", "label_warnings", "interactions",
    ]
    for table in not_yet_populated:
        row_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert row_count == 0, f"{table} should be empty until its ticket is committed"