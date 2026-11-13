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
    load_overrides,
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
            "active_ingredients": ["ACETAMINOPHEN"],
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
        assert result.product["labeler"] == "Labeler"
        assert result.product["marketing_category"] == "otc_monograph_drug"
        assert result.product["spl_version"] == 3
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


def test_a_package_only_on_a_label_blocks_another_split() -> None:
    # The box is 12345-678-90, on a label but not in the directory. The directory's 01234-5678-90
    # shares its digits; returning it would be a different product.
    ndc, labels, ingredients, _ = sources()
    other, box = package_codes("12345-678-90")
    labels.append({**labels[0], "spl_set_id": "label-b", "ndc11": other, "ndc_raw": "12345-678-90"})
    result = Resolver(ndc, labels, ingredients).resolve(box)
    assert result.status == "ambiguous_ndc"
    assert len(result.matches) == 2
    # A package on a label only is not found: the directory supplies the product's names.
    assert Resolver([], labels[1:], ingredients).resolve(box).status == "not_found"


def test_a_padded_ndc11_must_also_match_the_scanned_digits() -> None:
    # 12345-0678-9 and 12345-678-09 both pad to 12345067809, but their barcodes differ. Scanning
    # the label-only 12345-0678-9 must not return the directory's 12345-678-09.
    ndc, labels, ingredients, _ = sources("12345-678-09")
    label_only = {**labels[0], "spl_set_id": "label-b", "ndc_raw": "12345-0678-9"}
    _, scan = package_codes("12345-0678-9")
    assert Resolver(ndc, labels + [label_only], ingredients).resolve(scan).status == "not_found"
    assert Resolver(ndc, labels, ingredients).resolve(scan).status == "not_found"
    # The directory package's own barcode still resolves, to its own label only.
    _, own = package_codes("12345-678-09")
    result = Resolver(ndc, labels + [label_only], ingredients).resolve(own)
    assert result.status == "resolved"
    assert result.product is not None
    assert result.product["spl_set_id"] == "label-a"


def test_names_are_required() -> None:
    ndc, labels, ingredients, barcode = sources()
    for name in ("brand_name", "generic_name"):
        for empty in ("", None):
            broken = [{**ndc[0], name: empty}]
            assert Resolver(broken, labels, ingredients).resolve(barcode).status == "missing_name"


def test_parser_errors_pass_through() -> None:
    ndc, labels, ingredients, barcode = sources()
    resolver = Resolver(ndc, labels, ingredients)
    assert resolver.resolve("garbage").status == "invalid_format"
    wrong = barcode[:-1] + str((int(barcode[-1]) + 1) % 10)
    assert resolver.resolve(wrong).status == "bad_check_digit"
    # A valid UPC-A that does not start with 3 is a real barcode, just not a drug's.
    assert resolver.resolve("012345678905").status == "not_ndc_barcode"


def test_label_and_ingredient_failures() -> None:
    ndc, labels, ingredients, barcode = sources()
    assert Resolver(ndc, [], ingredients).resolve(barcode).status == "missing_label"
    assert Resolver(ndc, labels, []).resolve(barcode).status == "missing_ingredients"
    for bad in (
        {"strength": 0.0},
        {"strength": None},
        {"unit": None},
        {"per_amount": 5.0},
        {"per_amount": 0.0, "per_unit": "mL"},
        {"per_unit": "mL"},
        {"unii": None},
        {"unii": ""},
        {"name": None},
        {"name": ""},
    ):
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
    labels.append(
        {**labels[0], "product_index": 1, "ndc11": other_ndc11, "ndc_raw": "1234-5679-90"}
    )
    ingredients.append({**ingredients[0], "product_index": 1, "strength": 325.0})
    result = Resolver(ndc, labels, ingredients).resolve(barcode)
    assert result.product is not None
    assert [i["strength"] for i in result.product["ingredients"]] == [500.0]


def test_label_must_be_the_one_the_directory_names() -> None:
    ndc, labels, ingredients, barcode = sources()
    ndc[0]["spl_set_id"] = "label-z"
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "label_mismatch"


def test_label_and_directory_must_agree_on_ingredient_count() -> None:
    ndc, labels, ingredients, barcode = sources()
    ndc[0]["active_ingredients"] = ["ACETAMINOPHEN", "CAFFEINE"]
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "ingredient_conflict"
    none_listed: list[list[str] | None] = [[], None]
    for listed in none_listed:
        ndc[0]["active_ingredients"] = listed
        assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "resolved"


def test_directory_split_ingredient_name_is_not_a_conflict() -> None:
    # openFDA's directory splits an ingredient name at ";", so one label active becomes two.
    ndc, labels, ingredients, barcode = sources()
    ndc[0]["active_ingredients"] = ["HYDROLYSED BOVINE COLLAGEN (ENZYMATIC", "3500 MW)"]
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "resolved"
    # A fragment that closes a parenthesis it never opened is not rejoined.
    ndc[0]["active_ingredients"] = ["ACETAMINOPHEN)", "CAFFEINE"]
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "ingredient_conflict"


def test_real_ingredient_count_conflict_is_still_flagged() -> None:
    ndc, labels, ingredients, barcode = sources()
    ndc[0]["active_ingredients"] = ["ACETAMINOPHEN (AS SALT)", "CAFFEINE"]
    assert Resolver(ndc, labels, ingredients).resolve(barcode).status == "ingredient_conflict"


STORE_UPC = "012345678905"  # A valid UPC-A without an embedded NDC.


def test_override_resolves_a_barcode_without_an_ndc() -> None:
    ndc, labels, ingredients, _ = sources()
    resolver = Resolver(ndc, labels, ingredients, overrides={STORE_UPC: "01234567890"})
    for scan in (STORE_UPC, "0" + STORE_UPC):
        result = resolver.resolve(scan)
        assert result.status == "resolved"
        assert result.product is not None
        assert result.product["ndc11"] == "01234567890"
    # Without an override it is still just not a drug barcode.
    assert Resolver(ndc, labels, ingredients).resolve(STORE_UPC).status == "not_ndc_barcode"
    # An override to a package the directory does not have is not found, never guessed.
    missing = Resolver(ndc, labels, ingredients, overrides={STORE_UPC: "99999999999"})
    assert missing.resolve(STORE_UPC).status == "not_found"


def test_override_still_runs_every_package_check() -> None:
    ndc, labels, ingredients, _ = sources()
    kit = [{**ingredients[0], "part_index": 1}]
    resolver = Resolver(ndc, labels, kit, overrides={STORE_UPC: "01234567890"})
    assert resolver.resolve(STORE_UPC).status == "kit"


OVERRIDE_HEADER = "barcode,ndc11,reviewed_by,reviewed_on,source\n"


def write_overrides(path: Path, *rows: str) -> Path:
    path.write_text(OVERRIDE_HEADER + "".join(row + "\n" for row in rows), encoding="utf-8")
    return path


def test_load_overrides_reads_reviewed_rows(tmp_path: Path) -> None:
    path = write_overrides(
        tmp_path / "o.csv",
        f"{STORE_UPC},01234567890,A Reviewer,2026-11-01,photo of the box",
        # Scanned as EAN-13: kept as the UPC-A the parser reads.
        "0036000291452,01234567891,A Reviewer,2026-11-01,photo of the box",
    )
    assert load_overrides(path) == {STORE_UPC: "01234567890", "036000291452": "01234567891"}
    assert load_overrides(write_overrides(tmp_path / "empty.csv")) == {}


@pytest.mark.parametrize(
    "rows",
    [
        # Already a "3" + NDC barcode: the generated barcode resolves it, so no override.
        (f"{package_codes('1234-5678-90')[1]},01234567890,A Reviewer,2026-11-01,box",),
        # Bad check digit.
        ("012345678906,01234567890,A Reviewer,2026-11-01,box",),
        # The same barcode twice, even as UPC-A and EAN-13.
        (
            f"{STORE_UPC},01234567890,A Reviewer,2026-11-01,box",
            f"0{STORE_UPC},01234567891,A Reviewer,2026-11-01,box",
        ),
        # Not reviewed.
        (f"{STORE_UPC},01234567890,,2026-11-01,box",),
        (f"{STORE_UPC},01234567890,A Reviewer,,box",),
        # Not an NDC11.
        (f"{STORE_UPC},1234567890,A Reviewer,2026-11-01,box",),
        (f"{STORE_UPC},0123456789a,A Reviewer,2026-11-01,box",),
    ],
)
def test_load_overrides_rejects_bad_rows(tmp_path: Path, rows: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        load_overrides(write_overrides(tmp_path / "o.csv", *rows))


def test_build_reports_every_override(tmp_path: Path) -> None:
    ndc, labels, ingredients, _ = sources()
    bronze, silver, report = tmp_path / "bronze", tmp_path / "silver", tmp_path / "c.md"
    write_bronze(bronze, ndc, labels, ingredients)
    overrides = write_overrides(
        tmp_path / "o.csv", f"{STORE_UPC},01234567890,A Reviewer,2026-11-01,box"
    )
    # Overrides never change the coverage of generated barcodes.
    assert build_identity(bronze, silver, report, overrides) == (1, 1)
    text = report.read_text()
    assert "## Barcode overrides" in text
    assert f"| {STORE_UPC} | 01234567890 | resolved |" in text


def test_unknown_marketing_category_maps_to_other() -> None:
    ndc, labels, ingredients, barcode = sources()
    ndc[0]["marketing_category"] = "UNAPPROVED MEDICAL GAS"
    result = Resolver(ndc, labels, ingredients).resolve(barcode)
    assert result.product is not None
    assert result.product["marketing_category"] == "other"


def test_homeopathic_products_are_identified_without_a_product() -> None:
    ndc, labels, ingredients, barcode = sources()
    ndc[0]["marketing_category"] = "UNAPPROVED HOMEOPATHIC"
    result = Resolver(ndc, [], []).resolve(barcode)
    assert result.status == "homeopathic"
    # No label, so no ingredients: it cannot be a schema-valid product record.
    assert result.product is None
    # With a label it resolves like any other package.
    labelled = Resolver(ndc, labels, ingredients).resolve(barcode)
    assert labelled.status == "resolved"
    assert labelled.product is not None
    assert labelled.product["marketing_category"] == "unapproved_homeopathic"


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
    assert [p["ndc11"] for p in products] == ["01234567890"]
    assert {r["expected_ndc11"]: r["status"] for r in results} == {
        "01234567890": "resolved",
        "99999000001": "invalid_package_ndc",
        "88888000001": "ndc_mismatch",
        "66666000001": "homeopathic",
    }
    report = coverage_report(results)
    assert "Scored packages resolved: 1 of 3 (33.33%)" in report
    assert "all packages: 2 of 4 (50.00%)" in report
    assert "With a full product record (label and ingredients), all packages: 1 of 4" in report
    assert "not met" in report
    assert "| invalid |" in report
    assert "| 99999-0000-1 |" in report
    # Identified homeopathic packages are not misses; unidentified ones get their own list.
    assert "66666-0000-1" not in report
    assert "## Every homeopathic miss" in report
    assert "not met" in coverage_report([])
    # The target is 95%: 19 of 20 meets it, 18 of 20 does not.
    for hits, verdict in ((19, "Target 95%: met"), (18, "Target 95%: not met")):
        rows = [{**results[0], "status": "resolved"}] * hits
        rows += [{**results[0], "status": "not_found"}] * (20 - hits)
        assert verdict in coverage_report(rows)


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


@pytest.mark.parametrize(("resolved", "exit_code"), [(19, 0), (18, 1)])
def test_cli_exit_code_follows_the_95_percent_target(
    tmp_path: Path, monkeypatch: Any, resolved: int, exit_code: int
) -> None:
    from nomi_pipeline.cli import app
    from typer.testing import CliRunner

    base_ndc, base_labels, base_ingredients, _ = sources()
    ndc, labels, ingredients = [], [], []
    for i in range(20):
        ndc_raw = f"1234-{5000 + i}-90"
        ndc11, _ = package_codes(ndc_raw)
        ndc.append({**base_ndc[0], "ndc11": ndc11, "ndc_raw": ndc_raw})
        if i < resolved:
            labels.append(
                {**base_labels[0], "ndc11": ndc11, "ndc_raw": ndc_raw, "product_index": i}
            )
            ingredients.append({**base_ingredients[0], "product_index": i})
    write_bronze(tmp_path / "bronze", ndc, labels, ingredients)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    report = tmp_path / "coverage.md"
    result = CliRunner().invoke(app, ["identity", "resolve", "--report", str(report)])
    assert result.exit_code == exit_code, result.output
