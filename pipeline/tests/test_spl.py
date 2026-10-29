import shutil
from pathlib import Path

import pytest
from nomi_pipeline.ingest.spl import ParseError, collect_labels, parse_label

FIXTURES = Path(__file__).parent / "fixtures" / "spl"


def test_parses_products_from_ibuprofen_fixture() -> None:
    label = parse_label(FIXTURES / "ibuprofen_otc.xml")

    assert len(label.products) == 2
    ndcs = {product.ndc11 for product in label.products}
    assert ndcs == {"57344021203", "57344021205"}
    for product in label.products:
        assert product.spl_set_id == "4aba1bf2-8146-04fa-e063-6294a90a8a21"
        assert product.spl_version == 2


def test_parses_ingredients_from_ibuprofen_fixture() -> None:
    label = parse_label(FIXTURES / "ibuprofen_otc.xml")

    assert len(label.ingredients) == 11

    active = [i for i in label.ingredients if i.role == "active"]
    assert len(active) == 1
    assert active[0].name == "IBUPROFEN"
    assert active[0].unii == "WK2XYI10QM"
    assert active[0].strength == 200
    assert active[0].unit == "mg"

    inactive = [i for i in label.ingredients if i.role == "inactive"]
    assert len(inactive) == 10


def test_raises_parse_error_when_set_id_missing() -> None:
    with pytest.raises(ParseError):
        parse_label(FIXTURES / "missing_set_id.xml")


def test_raises_parse_error_when_xml_invalid() -> None:
    with pytest.raises(ParseError):
        parse_label(FIXTURES / "not_xml.xml")


def test_inactive_ingredient_without_unii_is_null_not_a_failure() -> None:
    label = parse_label(FIXTURES / "missing_unii.xml")

    inactive = [i for i in label.ingredients if i.role == "inactive"]
    assert len(inactive) == 1
    assert inactive[0].name == "MYSTERY INGREDIENT"
    assert inactive[0].unii is None


def test_malformed_package_ndc_is_skipped_not_a_file_failure() -> None:
    label = parse_label(FIXTURES / "malformed_ndc.xml")

    assert len(label.products) == 1
    assert label.products[0].ndc11 == "12345067890"


def test_multi_product_kit_assigns_distinct_product_index() -> None:
    label = parse_label(FIXTURES / "kit_two_products.xml")

    assert len(label.products) == 2
    indices = {product.product_index for product in label.products}
    assert indices == {0, 1}

    part_a = next(p for p in label.products if p.product_name == "Kit Part A")
    part_b = next(p for p in label.products if p.product_name == "Kit Part B")
    assert part_a.product_index != part_b.product_index

    ingredient_a = next(i for i in label.ingredients if i.name == "PART A ACTIVE")
    ingredient_b = next(i for i in label.ingredients if i.name == "PART B ACTIVE")
    assert ingredient_a.product_index == part_a.product_index
    assert ingredient_b.product_index == part_b.product_index


def test_collect_labels_gathers_rows_and_tracks_failures(tmp_path: Path) -> None:
    shutil.copy(FIXTURES / "ibuprofen_otc.xml", tmp_path / "ibuprofen_otc.xml")
    shutil.copy(FIXTURES / "not_xml.xml", tmp_path / "not_xml.xml")

    result = collect_labels(tmp_path)

    assert len(result.products) == 2
    assert len(result.ingredients) == 11
    assert len(result.failures) == 1
    assert result.failures[0]["file"] == "not_xml.xml"
    assert result.files_processed == 2


def test_collect_labels_handles_empty_directory(tmp_path: Path) -> None:
    result = collect_labels(tmp_path)

    assert result.products == []
    assert result.ingredients == []
    assert result.failures == []
    assert result.files_processed == 0
