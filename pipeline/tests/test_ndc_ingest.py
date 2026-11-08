import zipfile
from pathlib import Path

import pytest
from nomi_pipeline.ingest.ndc import NdcParseError, compute_stats, parse_ndc_file

FIXTURES = Path(__file__).parent / "fixtures" / "ndc"


def test_filters_to_otc_and_normalizes_ndc() -> None:
    result = parse_ndc_file(FIXTURES / "sample.json")

    assert len(result.products) == 2
    row = next(p for p in result.products if p.brand_name == "Vaporizing Chest Rub")
    assert row.ndc11 == "76176013501"
    assert row.spl_id == "5e2e190d-83ae-79ea-e063-6394a90adabf"
    assert result.skipped_bad_ndc == 1
    assert result.total_records == 4


def test_products_are_sorted_by_ndc11() -> None:
    result = parse_ndc_file(FIXTURES / "sample.json")

    ndcs = [p.ndc11 for p in result.products]
    assert ndcs == sorted(ndcs)
    assert ndcs == ["00363071008", "76176013501"]


def test_raises_error_when_invalid_json() -> None:
    with pytest.raises(NdcParseError):
        parse_ndc_file(FIXTURES / "not_json.txt")


def test_raises_error_when_results_key_missing() -> None:
    with pytest.raises(NdcParseError):
        parse_ndc_file(FIXTURES / "missing_results.json")


def test_compute_stats_counts_rows_and_null_rates() -> None:
    result = parse_ndc_file(FIXTURES / "sample.json")

    stats = compute_stats(result)
    assert stats["total_rows"] == 2
    assert stats["total_records_seen"] == 4
    assert stats["skipped_bad_ndc"] == 1
    assert stats["null_rates"]["spl_set_id"] == 0.5
    assert stats["null_rates"]["ndc11"] == 0.0


def test_reads_the_zipped_file_from_fetch(tmp_path: Path) -> None:
    zipped = tmp_path / "drug-ndc-0001-of-0001.json.zip"
    with zipfile.ZipFile(zipped, "w") as z:
        z.write(FIXTURES / "sample.json", "drug-ndc-0001-of-0001.json")

    assert parse_ndc_file(zipped).products == parse_ndc_file(FIXTURES / "sample.json").products
