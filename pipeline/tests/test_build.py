import hashlib
import json
import sqlite3
import subprocess
from pathlib import Path

import polars as pl
import pytest
from fsspec.core import url_to_fs
from nomi_pipeline.build import build
from nomi_pipeline.build.build import (
    SCHEMA_PATH,
    build_database,
    build_time,
    publish,
    write_manifest,
)
from nomi_pipeline.config import REPO_ROOT, Settings
from nomi_pipeline.identity.resolver import RESULT_SCHEMA

FIXTURES = Path(__file__).parent / "fixtures" / "build"
REFERENCE_PRODUCTS_DIR = REPO_ROOT / "packages" / "schema" / "examples"
BUILT_AT = "2025-01-01T00:00:00Z"

# Package NDCs of the fixture and reference products (NOMI-015). The fixtures' NDC11s are made up.
PACKAGES = {
    "00363071008": "0363-0710-08",
    "76176013501": "76176-135-01",
    "11111111111": "1111-1111-11",
    "22222222222": "2222-2222-22",
    "33333333333": "3333-3333-33",
    "00280608020": "0280-6080-20",
    "50580044905": "50580-449-05",
    "69423099516": "69423-995-16",
    "79903029710": "79903-297-10",
    "84126031604": "84126-316-04",
}

# apps/mobile/src/lib/db.ts LOOKUP_SQL: the app's one query per scan.
LOOKUP_SQL = """
  SELECT p.package_ndc, p.ndc11, p.brand, p.generic, p.form, p.scope_flag, p.review_status,
         pi.unii, i.name, pi.strength, pi.unit, pi.per_amount, pi.per_unit
  FROM products p
  LEFT JOIN product_ingredients pi ON pi.package_ndc = p.package_ndc
  LEFT JOIN ingredients i ON i.unii = pi.unii
  WHERE p.ndc10 = ?
  ORDER BY p.package_ndc, i.name"""


@pytest.fixture
def identity_results(tmp_path: Path) -> Path:
    """The identity stage's results, with every product in PACKAGES resolved."""
    return write_identity(
        tmp_path / "identity_results.parquet",
        [(package, ndc11, "resolved", [ndc11]) for ndc11, package in PACKAGES.items()],
    )


def write_identity(path: Path, rows: list[tuple[str, str, str, list[str]]]) -> Path:
    """identity_results.parquet rows: package NDC, its NDC11, status and matching NDC11s."""
    pl.DataFrame(
        [
            {"ndc_raw": package, "expected_ndc11": ndc11, "status": status, "matches": matches}
            for package, ndc11, status, matches in rows
        ],
        schema=RESULT_SCHEMA,
    ).write_parquet(path)
    return path


def build_fixture(products: Path, identity_results: Path, db_path: Path) -> dict[str, int]:
    return build_database(products, identity_results, db_path, "v0.1.0", BUILT_AT)


def reference_products() -> list[dict[str, object]]:
    products = []
    for entry in sorted(REFERENCE_PRODUCTS_DIR.iterdir()):
        if entry.is_dir():
            product = json.loads((entry / "product.json").read_text())
            for ingredient in product["ingredients"]:
                ingredient["strength"] = float(ingredient["strength"])
                ingredient.setdefault("per_amount", None)
                ingredient.setdefault("per_unit", None)
            products.append(product)
    return products


def write_products(path: Path, products: list[dict[str, object]]) -> Path:
    pl.DataFrame(products).write_parquet(path)
    return path


def test_build_creates_the_apps_tables(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    build_fixture(FIXTURES / "product.parquet", identity_results, db_path)
    app = sqlite3.connect(":memory:")
    app.executescript(SCHEMA_PATH.read_text())

    con = sqlite3.connect(str(db_path))
    schema = "SELECT type, name, sql FROM sqlite_master ORDER BY name"
    assert con.execute(schema).fetchall() == app.execute(schema).fetchall()
    # The app's checkDataset: its schema version and exactly one meta row.
    assert con.execute("PRAGMA user_version").fetchone() == (1,)
    assert con.execute("SELECT count(*) FROM meta").fetchone() == (1,)


def test_build_database_populates_product_tables(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_fixture(FIXTURES / "product.parquet", identity_results, db_path)

    assert counts == {"products": 2, "product_ingredients": 3, "ingredients": 3}

    con = sqlite3.connect(str(db_path))
    row = con.execute(
        "SELECT package_ndc, ndc11, brand, generic, form, scope_flag, review_status "
        "FROM products WHERE ndc10 = ?",
        ("7617613501",),
    ).fetchone()
    assert row == (
        "76176-135-01",
        "76176013501",
        "Vaporizing Chest Rub",
        "camphor, menthol, eucalyptus oil",
        "OINTMENT",
        "in_scope",
        "preliminary",
    )


def test_liquid_strength_keeps_its_per_amount(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    build_fixture(FIXTURES / "product.parquet", identity_results, db_path)

    con = sqlite3.connect(str(db_path))
    rows = con.execute(
        "SELECT package_ndc, unii, strength, unit, per_amount, per_unit "
        "FROM product_ingredients ORDER BY package_ndc, unii"
    ).fetchall()
    assert rows == [
        ("0363-0710-08", "TC2D6JAD40", 12.5, "mg", 5.0, "mL"),
        ("76176-135-01", "L7T10EIP3A", 1.0, "g", 100.0, "g"),
        ("76176-135-01", "N20HL7Y976", 4.7, "g", 100.0, "g"),
    ]


def test_shared_ingredient_is_not_duplicated(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_fixture(FIXTURES / "shared_ingredient.parquet", identity_results, db_path)

    assert counts == {"products": 2, "product_ingredients": 2, "ingredients": 1}


def test_meta_data_table(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    build_fixture(FIXTURES / "product.parquet", identity_results, db_path)
    con = sqlite3.connect(str(db_path))
    rows = con.execute("SELECT dataset_version, model_version, built_at FROM meta").fetchall()

    assert rows == [("v0.1.0", None, BUILT_AT)]


def test_same_input_builds_the_same_file(tmp_path: Path, identity_results: Path) -> None:
    first = tmp_path / "first.sqlite"
    second = tmp_path / "second.sqlite"
    build_fixture(FIXTURES / "product.parquet", identity_results, first)
    build_fixture(FIXTURES / "product.parquet", identity_results, second)

    assert first.read_bytes() == second.read_bytes()


def test_build_time_uses_source_date_epoch(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1735689600")

    assert build_time() == BUILT_AT


def test_write_manifest_has_expected_fields(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_fixture(FIXTURES / "product.parquet", identity_results, db_path)

    manifest_path = tmp_path / "manifest.json"
    manifest = write_manifest(
        [FIXTURES / "product.parquet", identity_results], db_path, counts, "v0.1.0", manifest_path
    )

    assert manifest["version"] == "v0.1.0"
    assert manifest["sha256"] == hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert manifest["size"] == db_path.stat().st_size
    assert manifest["counts"]["products"] == 2
    assert set(manifest["input_hashes"]) == {"product.parquet", "identity_results.parquet"}
    assert json.loads(manifest_path.read_text()) == manifest


def test_manifest_records_the_repo_commit_and_dirty_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    db_path = tmp_path / "nomi.sqlite"
    db_path.write_text("db")

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()

    git("init", "-q")
    (repo / "file").write_text("one")
    git("add", "file")
    git("commit", "-qm", "one")
    monkeypatch.setattr(build, "REPO_ROOT", repo)
    # Run from elsewhere: the commit must come from the repo, not the working directory.
    monkeypatch.chdir(tmp_path)

    manifest = write_manifest([], db_path, {}, "v0.1.0", tmp_path / "manifest.json")
    assert manifest["commit"] == git("rev-parse", "HEAD")
    assert manifest["dirty"] is False

    # Untracked files (a local .env, say) can't change what the commit builds.
    (repo / "untracked").write_text("x")
    manifest = write_manifest([], db_path, {}, "v0.1.0", tmp_path / "manifest.json")
    assert manifest["dirty"] is False

    (repo / "file").write_text("two")
    manifest = write_manifest([], db_path, {}, "v0.1.0", tmp_path / "manifest.json")
    assert manifest["dirty"] is True


def test_product_without_scope_is_out_of_scope(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    counts = build_fixture(FIXTURES / "real_shape_product.parquet", identity_results, db_path)

    assert counts["products"] == 1

    con = sqlite3.connect(str(db_path))
    row = con.execute(
        "SELECT category, scope_flag, review_status FROM products WHERE ndc11 = ?",
        ("33333333333",),
    ).fetchone()
    assert row == (None, "out_of_scope", None)


def test_homeopathic_product_is_never_in_scope(tmp_path: Path, identity_results: Path) -> None:
    product = reference_products()[0]
    product["marketing_category"] = "unapproved_homeopathic"
    products = write_products(tmp_path / "product.parquet", [product])
    db_path = tmp_path / "nomi.sqlite"
    build_fixture(products, identity_results, db_path)

    con = sqlite3.connect(str(db_path))
    assert con.execute("SELECT scope_flag FROM products").fetchall() == [("homeopathic",)]


def test_app_finds_the_five_reference_products(tmp_path: Path, identity_results: Path) -> None:
    products = reference_products()
    assert len(products) == 5
    parquet_path = write_products(tmp_path / "product.parquet", products)
    db_path = tmp_path / "nomi.sqlite"
    counts = build_fixture(parquet_path, identity_results, db_path)

    assert counts == {"products": 5, "product_ingredients": 7, "ingredients": 5}

    con = sqlite3.connect(str(db_path))
    for product in products:
        package_ndc = PACKAGES[str(product["ndc11"])]
        rows = con.execute(LOOKUP_SQL, (package_ndc.replace("-", ""),)).fetchall()
        ingredients = product["ingredients"]
        assert isinstance(ingredients, list)
        expected = [
            (
                package_ndc,
                product["ndc11"],
                product["brand_name"],
                product["generic_name"],
                product["dosage_form"],
                product["scope"],
                product["review_status"],
                i["unii"],
                i["name"],
                i["strength"],
                i["unit"],
                i["per_amount"],
                i["per_unit"],
            )
            for i in ingredients
        ]
        assert rows == sorted(expected, key=lambda row: str(row[8]))


def lookup_status(con: sqlite3.Connection, ndc10: str) -> str:
    """The status apps/mobile/src/lib/db.ts lookupBarcode returns for these rows."""
    rows = con.execute(LOOKUP_SQL, (ndc10,)).fetchall()
    packages = {row[0] for row in rows}
    if not packages:
        return "not_found"
    if len(packages) > 1:
        return "ambiguous_ndc"
    scope = str(rows[0][5])
    return "resolved" if scope == "in_scope" else scope


def test_app_lookup_status_for_each_identity_status(tmp_path: Path) -> None:
    tylenol = next(p for p in reference_products() if p["ndc11"] == "50580044905")
    products = write_products(tmp_path / "product.parquet", [tylenol])
    # 1234567890 is two packages: one in the directory, one known only from a label.
    identity = write_identity(
        tmp_path / "identity_results.parquet",
        [
            ("50580-449-05", "50580044905", "resolved", ["50580044905"]),
            ("0220-1234-56", "00220123456", "homeopathic", ["00220123456"]),
            ("1234-5678-90", "01234567890", "ambiguous_ndc", ["01234567890", "12345067890"]),
            ("0000-0000-01", "00000000001", "missing_label", ["00000000001"]),
        ],
    )
    db_path = tmp_path / "nomi.sqlite"
    counts = build_fixture(products, identity, db_path)

    assert counts["products"] == 4
    con = sqlite3.connect(str(db_path))
    assert lookup_status(con, "5058044905") == "resolved"
    assert lookup_status(con, "0220123456") == "homeopathic"
    assert lookup_status(con, "1234567890") == "ambiguous_ndc"
    assert lookup_status(con, "0000000001") == "not_found"
    assert con.execute(
        "SELECT package_ndc, ndc11, brand, scope_flag FROM products WHERE ndc10 = ?",
        ("1234567890",),
    ).fetchall() == [
        ("1234-5678-90", "01234567890", None, "out_of_scope"),
        ("12345-678-90", "12345067890", None, "out_of_scope"),
    ]
    homeopathic = con.execute(
        "SELECT p.brand, pi.unii FROM products p "
        "LEFT JOIN product_ingredients pi ON pi.package_ndc = p.package_ndc WHERE p.ndc10 = ?",
        ("0220123456",),
    ).fetchall()
    assert homeopathic == [(None, None)]


def test_lookup_uses_the_ndc10_index(tmp_path: Path, identity_results: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    build_fixture(FIXTURES / "product.parquet", identity_results, db_path)

    con = sqlite3.connect(str(db_path))
    plan = con.execute(f"EXPLAIN QUERY PLAN {LOOKUP_SQL}", ("7617613501",)).fetchall()
    details = [row[-1] for row in plan]
    assert any("USING INDEX products_ndc10" in detail for detail in details)
    assert not any(detail.startswith("SCAN") for detail in details)


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


def test_publish_refuses_to_overwrite_a_published_version(tmp_path: Path) -> None:
    db_path = tmp_path / "nomi.sqlite"
    manifest_path = tmp_path / "manifest.json"
    db_path.write_text("first")
    manifest_path.write_text('{"version": "v0.1.0"}')
    settings = Settings(data_dir=tmp_path / "data", dataset_store=f"memory://{tmp_path.name}")
    prefix = publish(db_path, manifest_path, "v0.1.0", settings)

    db_path.write_text("second")
    with pytest.raises(FileExistsError):
        publish(db_path, manifest_path, "v0.1.0", settings)
    fs, _ = url_to_fs(settings.dataset_store)
    assert fs.cat(f"{prefix}/nomi.sqlite") == b"first"

    publish(db_path, manifest_path, "v0.1.0", settings, overwrite=True)
    assert fs.cat(f"{prefix}/nomi.sqlite") == b"second"
