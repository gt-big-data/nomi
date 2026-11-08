"""Identity failures must not be reported as successful barcode coverage (NOMI-025)."""

from pathlib import Path
from typing import Any

import polars as pl
import pytest
from nomi_pipeline.identity.resolver import (
    Resolver,
    build_identity,
    coverage_report,
    evaluate,
    package_codes,
)

Rows = list[dict[str, Any]]


def sources(ndc_raw: str = "1234-5678-90") -> tuple[Rows, Rows, Rows, str]:
    """One package on one label, shaped like the bronze tables."""
    ndc11, barcode = package_codes(ndc_raw)
    ndc = [
        {
            "ndc11": ndc11,
            "ndc_raw": ndc_raw,
            "spl_set_id": "label-a",
            "brand_name": "Fixture",
            "generic_name": "acetaminophen",
            "labeler_name": "Labeler",
            "dosage_form": "TABLET",
            "route": "ORAL",
            "marketing_category": "OTC MONOGRAPH DRUG",
            "sample": False,
        }
    ]
    labels = [
        {
            "spl_set_id": "label-a",
            "spl_version": 3,
            "product_index": 0,
            "product_name": "Fixture",
            "ndc11": ndc11,
            "ndc_raw": ndc_raw,
        }
    ]
    ingredients = [
        {
            "spl_set_id": "label-a",
            "product_index": 0,
            "part_index": None,
            "role": "active",
            "class_code": "ACTIB",
            "unii": "362O9ITL9D",
            "name": "ACETAMINOPHEN",
            "strength": 500.0,
            "unit": "mg",
            "per_amount": None,
            "per_unit": None,
        }
    ]
    return ndc, labels, ingredients, barcode


@pytest.mark.parametrize(
    ("ndc_raw", "ndc11"),
    [
        ("1234-5678-90", "01234567890"),
        ("12345-678-90", "12345067890"),
        ("12345-6789-0", "12345678900"),
    ],
)
def test_each_layout_and_ean_resolves(ndc_raw: str, ndc11: str) -> None:
    ndc, labels, ingredients, barcode = sources(ndc_raw)
    assert package_codes(ndc_raw)[0] == ndc11
    resolver = Resolver(ndc, labels, ingredients)
    for scan in (barcode, "0" + barcode):
        result = resolver.resolve(scan)
        assert result.status == "resolved"
        assert result.product is not None
        assert result.product["ndc11"] == ndc11
        assert result.product["brand_name"] == "Fixture"
        assert result.product["ingredients"] == [
            {
                "unii": "362O9ITL9D",
                "name": "ACETAMINOPHEN",
                "strength": 500.0,
                "unit": "mg",
                "per_amount": None,
                "per_unit": None,
            }
        ]


def test_package_codes_rejects_undashed_and_bad_digits() -> None:
    for bad in ("1234567890", "1234-567-890", "12a4-5678-90"):
        with pytest.raises(ValueError):
            package_codes(bad)


def test_missing_and_ambiguous_candidates() -> None:
    ndc, labels, ingredients, barcode = sources()
    assert Resolver([], labels, ingredients).resolve(barcode).status == "not_found"
    # The same 10 digits split another way is a different package: never pick one.
    other, _ = package_codes("12345-678-90")
    ndc.append({**ndc[0], "ndc11": other, "ndc_raw": "12345-678-90"})
    result = Resolver(ndc, labels, ingredients).resolve(barcode)
    assert result.status == "ambiguous_ndc"
    assert len(result.matches) == 2


def test_parser_errors_pass_through() -> None:
    ndc, labels, ingredients, barcode = sources()
    resolver = Resolver(ndc, labels, ingredients)
    assert resolver.resolve("garbage").status == "invalid_format"
    wrong = barcode[:-1] + str((int(barcode[-1]) + 1) % 10)
    assert resolver.resolve(wrong).status == "bad_check_digit"


def test_label_and_ingredient_failures() -> None:
    ndc, labels, ingredients, barcode = sources()
    assert Resolver(ndc, [], ingredients).resolve(barcode).status == "missing_label"
    assert Resolver(ndc, labels, []).resolve(barcode).status == "missing_ingredients"
    inactive = [{**ingredients[0], "role": "inactive"}]
    assert Resolver(ndc, labels, inactive).resolve(barcode).status == "missing_ingredients"
    for bad in ({"strength": 0.0}, {"strength": None}, {"unit": None}, {"per_amount": 5.0}):
        broken = [{**ingredients[0], **bad}]
        assert Resolver(ndc, labels, broken).resolve(barcode).status == "invalid_ingredients"
    kit = [{**ingredients[0], "part_index": 1}]
    assert Resolver(ndc, labels, kit).resolve(barcode).status == "kit"


def test_package_on_two_labels_uses_the_directory_set_id() -> None:
    ndc, labels, ingredients, barcode = sources()
    labels.append({**labels[0], "spl_set_id": "label-b", "product_name": "Other"})
    ingredients.append({**ingredients[0], "spl_set_id": "label-b", "strength": 250.0})
    result = Resolver(ndc, labels, ingredients).resolve(barcode)
    assert result.status == "resolved"
    assert result.product is not None
    assert result.product["spl_set_id"] == "label-a"
    assert result.product["ingredients"][0]["strength"] == 500.0
    # Without a set id in the directory there is no safe choice.
    ndc[0]["spl_set_id"] = None
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "ambiguous_label"


def test_ingredients_come_from_the_packages_own_product() -> None:
    # One label, two products with different strengths: join on product index, not set id.
    ndc, labels, ingredients, barcode = sources()
    other_ndc11, _ = package_codes("1234-5679-90")
    labels.append({**labels[0], "product_index": 1, "ndc11": other_ndc11})
    ingredients.append({**ingredients[0], "product_index": 1, "strength": 325.0})
    result = Resolver(ndc, labels, ingredients).resolve(barcode)
    assert result.product is not None
    assert [i["strength"] for i in result.product["ingredients"]] == [500.0]


def test_only_the_latest_label_version_counts() -> None:
    ndc, labels, ingredients, barcode = sources()
    other_ndc11, _ = package_codes("1234-5679-90")
    # Version 4 no longer lists this package, so the old version must not resolve it.
    labels.append({**labels[0], "spl_version": 4, "ndc11": other_ndc11})
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "missing_label"


def test_homeopathic_products_resolve_without_ingredients() -> None:
    ndc, _, _, barcode = sources()
    ndc[0]["marketing_category"] = "UNAPPROVED HOMEOPATHIC"
    result = Resolver(ndc, [], []).resolve(barcode)
    assert result.status == "homeopathic"
    assert result.product is not None
    assert result.product["ingredients"] == []


def test_coverage_keeps_every_miss_and_skips_samples() -> None:
    ndc, labels, ingredients, _ = sources()
    ndc += [
        {**ndc[0], "ndc11": "99999000001", "ndc_raw": "invalid"},
        {**ndc[0], "ndc11": "88888000001", "ndc_raw": "99999-0000-1"},
        {**ndc[0], "ndc11": "77777000001", "ndc_raw": "77777-0000-1", "sample": True},
        {
            **ndc[0],
            "ndc11": "66666000001",
            "ndc_raw": "66666-0000-1",
            "marketing_category": "UNAPPROVED HOMEOPATHIC",
        },
    ]
    products, results = evaluate(Resolver(ndc, labels, ingredients))
    assert [p["ndc11"] for p in products] == ["01234567890", "66666000001"]
    assert {r["expected_ndc11"]: r["status"] for r in results} == {
        "01234567890": "resolved",
        "99999000001": "invalid_package_ndc",
        "88888000001": "ndc_mismatch",
        "66666000001": "homeopathic",
    }
    report = coverage_report(results)
    assert "Correct: 1 of 3 (33.33%)" in report
    assert "not met" in report
    assert "| invalid |" in report
    assert "| 99999-0000-1 |" in report
    assert "66666-0000-1" not in report
    assert "not met" in coverage_report([])


def write_bronze(folder: Path, ndc: Rows, labels: Rows, ingredients: Rows) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    for name, rows in [("ndc", ndc), ("spl_products", labels), ("spl_ingredients", ingredients)]:
        pl.from_dicts(rows, infer_schema_length=None).write_parquet(folder / f"{name}.parquet")


def test_parquet_build_is_repeatable_and_survives_empty_input(tmp_path: Path) -> None:
    ndc, labels, ingredients, _ = sources()
    bronze, silver, report = tmp_path / "bronze", tmp_path / "silver", tmp_path / "r" / "c.md"
    write_bronze(bronze, ndc, labels, ingredients)
    assert build_identity(bronze, silver, report) == (1, 1)
    saved = pl.read_parquet(silver / "product.parquet").to_dicts()
    assert saved[0]["ingredients"][0]["strength"] == 500.0
    first = (silver / "product.parquet").read_bytes()
    build_identity(bronze, silver, report)
    assert first == (silver / "product.parquet").read_bytes()
    # An empty label table must not leave the previous products behind.
    pl.from_dicts(labels).clear().write_parquet(bronze / "spl_products.parquet")
    assert build_identity(bronze, silver, report) == (0, 1)
    assert pl.read_parquet(silver / "product.parquet").is_empty()
    assert pl.read_parquet(silver / "identity_results.parquet")["status"].to_list() == [
        "missing_label"
    ]


def test_cli_fails_below_target_but_keeps_diagnostics(tmp_path: Path, monkeypatch: Any) -> None:
    from nomi_pipeline.cli import app
    from typer.testing import CliRunner

    ndc, labels, ingredients, _ = sources()
    write_bronze(
        tmp_path / "bronze",
        ndc + [{**ndc[0], "ndc11": "99999000001", "ndc_raw": "x"}],
        labels,
        ingredients,
    )
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    report = tmp_path / "coverage.md"
    result = CliRunner().invoke(app, ["identity", "resolve", "--report", str(report)])
    assert result.exit_code == 1, result.output
    assert "1/2" in result.stdout
    assert "50.00%" in report.read_text()
    assert (tmp_path / "silver" / "identity_results.parquet").exists()
    write_bronze(tmp_path / "bronze", ndc, labels, ingredients)
    result = CliRunner().invoke(app, ["identity", "resolve", "--report", str(report)])
    assert result.exit_code == 0, result.output
