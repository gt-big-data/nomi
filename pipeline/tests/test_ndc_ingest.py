import json
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


def _write_records(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"results": records}))
    return path


def _record(product_ndc: str, package_ndcs: list[str], **extra: object) -> dict[str, object]:
    return {
        "product_type": "HUMAN OTC DRUG",
        "product_ndc": product_ndc,
        "spl_id": f"spl-{product_ndc}",
        "finished": True,
        "packaging": [{"package_ndc": n, "description": "1 BOTTLE"} for n in package_ndcs],
        **extra,
    }


def test_keeps_ingredients_and_one_row_per_ndc(tmp_path: Path) -> None:
    ingredients = [{"name": "IBUPROFEN", "strength": "200 mg/1"}]
    result = parse_ndc_file(
        _write_records(
            tmp_path / "ndc.json",
            [
                _record("72043-2500", ["72043-2500-1"], active_ingredients=ingredients),
                _record("72043-2500", ["72043-2500-1"], active_ingredients=ingredients),
            ],
        )
    )

    assert [row.ndc11 for row in result.products] == ["72043250001"]
    assert result.duplicate_ndcs == 1
    assert result.products[0].active_ingredients == ["IBUPROFEN"]
    assert result.products[0].active_strengths == ["200 mg/1"]


def test_skips_unfinished_and_unpackaged_records(tmp_path: Path) -> None:
    result = parse_ndc_file(
        _write_records(
            tmp_path / "ndc.json",
            [_record("0363-0710", ["0363-0710-08"], finished=False), _record("0363-0711", [])],
        )
    )

    assert result.products == []
    assert result.skipped_unfinished == 1
    assert result.records_without_packages == 1
