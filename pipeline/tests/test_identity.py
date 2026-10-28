"""Identity failures must not be reported as successful barcode coverage."""

from pathlib import Path
from typing import Any

import polars as pl
from nomi_pipeline.identity.resolver import (
    Resolver,
    build_identity,
    coverage_report,
    evaluate,
    package_codes,
)


def sources() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], str]:
    ndc11, barcode = package_codes("1234-5678-90")
    ndc = [{"ndc11": ndc11, "package_ndc": "1234-5678-90"}]
    labels = [
        {"ndc11": ndc11, "spl_set_id": "label-a", "spl_version": 1, "brand_name": "Fixture product"}
    ]
    ingredients = [
        {
            "ndc11": ndc11,
            "spl_set_id": "label-a",
            "spl_version": 1,
            "unii": "362O9ITL9D",
            "name": "acetaminophen",
            "strength": 500,
            "unit": "mg",
        }
    ]
    return ndc, labels, ingredients, barcode


def test_each_layout_and_ean_resolves() -> None:
    for original, expected in [
        ("1234-5678-90", "01234567890"),
        ("12345-678-90", "12345067890"),
        ("12345-6789-0", "12345678900"),
    ]:
        code, barcode = package_codes(original)
        assert code == expected
        ndc, labels, ingredients, _ = sources()
        ndc[0].update(ndc11=code, package_ndc=original)
        labels[0]["ndc11"] = code
        ingredients[0]["ndc11"] = code
        resolver = Resolver(ndc, labels, ingredients)
        for scan in (barcode, "0" + barcode):
            result = resolver.resolve(scan)
            assert result.status == "resolved"
            assert result.product is not None
            assert result.product["ndc11"] == code
            assert result.product["ingredients"][0]["strength"] == 500


def test_missing_and_ambiguous_candidates() -> None:
    ndc, labels, ingredients, barcode = sources()
    assert Resolver([], labels, ingredients).resolve(barcode).status == "not_found"
    # Same unsegmented NDC10, different normalization: never choose the labeled candidate.
    other, _ = package_codes("12345-678-90")
    ndc.append({"ndc11": other, "package_ndc": "12345-678-90"})
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "ambiguous_ndc"


def test_label_and_ingredient_failure_states() -> None:
    ndc, labels, ingredients, barcode = sources()
    assert Resolver(ndc, [], ingredients).resolve(barcode).status == "missing_label"
    assert Resolver(ndc, labels, []).resolve(barcode).status == "missing_ingredients"
    ingredients[0]["strength"] = 0
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "invalid_ingredients"
    labels.append({**labels[0], "spl_set_id": "label-b"})
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "ambiguous_label"


def test_latest_version_and_package_specific_ingredients() -> None:
    ndc, labels, ingredients, barcode = sources()
    labels.append({**labels[0], "spl_version": 2})
    ingredients.extend(
        [
            {**ingredients[0], "spl_version": 2, "strength": 250},
            {**ingredients[0], "spl_version": 2, "ndc11": "99999000001", "strength": 999},
        ]
    )
    result = Resolver(ndc, labels, ingredients).resolve(barcode)
    assert result.product is not None
    assert result.product["spl_version"] == 2
    assert result.product["ingredients"] == [
        {"unii": "362O9ITL9D", "name": "acetaminophen", "strength": 250, "unit": "mg"}
    ]
    # A package removed in the latest version must not resolve against an old label.
    labels[-1]["ndc11"] = "99999000001"
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "missing_label"


def test_parser_errors_and_duplicate_candidates() -> None:
    ndc, labels, ingredients, barcode = sources()
    resolver = Resolver(ndc, labels, ingredients)
    assert resolver.resolve("garbage").status == "invalid_format"
    assert (
        resolver.resolve(barcode[:-1] + str((int(barcode[-1]) + 1) % 10)).status
        == "bad_check_digit"
    )
    # Several layouts can normalize to the same ID; count distinct matches only.
    code, scan = package_codes("00000-000-00")
    ndc[0]["ndc11"] = labels[0]["ndc11"] = ingredients[0]["ndc11"] = code
    assert Resolver(ndc, labels, ingredients).resolve(scan).status == "resolved"


def test_coverage_preserves_misses_and_deduplicates() -> None:
    ndc, labels, ingredients, _ = sources()
    ndc.extend(
        [
            ndc[0].copy(),
            {"ndc11": "99999000001", "package_ndc": "invalid"},
            {"ndc11": "88888000001", "package_ndc": "99999-0000-1"},
        ]
    )
    products, results = evaluate(Resolver(ndc, labels, ingredients))
    assert len(products) == 1
    assert len(results) == 3
    assert {row["status"] for row in results} == {
        "resolved",
        "invalid_package_ndc",
        "ndc_normalization_mismatch",
    }
    report = coverage_report(results)
    assert "1/3 (33.33%)" in report
    assert "NOT MET" in report
    assert "invalid" in report
    assert "99999-0000-1" in report
    assert "NOT MET" in coverage_report([])


def test_parquet_build_and_empty_rebuild(tmp_path: Path) -> None:
    ndc, labels, ingredients, _ = sources()
    bronze = tmp_path / "bronze"
    bronze.mkdir()
    for name, rows in [("ndc", ndc), ("spl_products", labels), ("spl_ingredients", ingredients)]:
        pl.from_dicts(rows).write_parquet(bronze / f"{name}.parquet")
    silver = tmp_path / "silver"
    report = tmp_path / "reports" / "coverage.md"
    assert build_identity(bronze, silver, report) == {"total": 1, "resolved": 1}
    saved = pl.read_parquet(silver / "product.parquet").to_dicts()
    assert saved[0]["ingredients"][0]["strength"] == 500
    assert "PASS" in report.read_text()
    # Identical input produces identical outputs.
    first = (silver / "product.parquet").read_bytes()
    build_identity(bronze, silver, report)
    assert first == (silver / "product.parquet").read_bytes()
    pl.from_dicts(labels).clear().write_parquet(bronze / "spl_products.parquet")
    assert build_identity(bronze, silver, report) == {"total": 1, "resolved": 0}
    assert pl.read_parquet(silver / "product.parquet").is_empty()
    assert pl.read_parquet(silver / "identity_results.parquet")["status"].to_list() == [
        "missing_label"
    ]


def test_cli_threshold_keeps_diagnostics(tmp_path: Path, monkeypatch: Any) -> None:
    from nomi_pipeline.cli import app
    from typer.testing import CliRunner

    ndc, labels, ingredients, _ = sources()
    bronze = tmp_path / "bronze"
    bronze.mkdir()
    ndc.append({"ndc11": "99999000001", "package_ndc": "invalid"})
    for name, rows in [("ndc", ndc), ("spl_products", labels), ("spl_ingredients", ingredients)]:
        pl.from_dicts(rows).write_parquet(bronze / f"{name}.parquet")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    report = tmp_path / "coverage.md"
    result = CliRunner().invoke(app, ["identity", "resolve", "--report", str(report)])
    assert result.exit_code == 1, result.output
    assert "1/2" in result.stdout
    assert "50.00%" in report.read_text()
    assert (tmp_path / "silver" / "identity_results.parquet").exists()
    pl.from_dicts(ndc[:1]).write_parquet(bronze / "ndc.parquet")
    result = CliRunner().invoke(app, ["identity", "resolve", "--report", str(report)])
    assert result.exit_code == 0, result.output


def test_no_matching_label_version_never_uses_old_ingredients() -> None:
    ndc, labels, ingredients, barcode = sources()
    labels.append({**labels[0], "spl_version": 2})
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "missing_ingredients"


def test_empty_directory_build(tmp_path: Path) -> None:
    ndc, labels, ingredients, _ = sources()
    for name, rows in [("ndc", ndc), ("spl_products", labels), ("spl_ingredients", ingredients)]:
        pl.from_dicts(rows).clear().write_parquet(tmp_path / f"{name}.parquet")
    counts = build_identity(tmp_path, tmp_path / "silver", tmp_path / "report.md")
    assert counts == {"total": 0, "resolved": 0}
    assert "NOT MET" in (tmp_path / "report.md").read_text()
    assert pl.read_parquet(tmp_path / "silver" / "identity_results.parquet").is_empty()
