import pytest
from nomi_pipeline.ingest._ndc import normalize_ndc


def test_normalizes_a_valid_ndc() -> None:
    assert normalize_ndc("57344-212-03") == "57344021203"


def test_rejects_malformed_ndc() -> None:
    with pytest.raises(ValueError):
        normalize_ndc("not-an-ndc")


def test_rejects_ndc_with_oversized_segment() -> None:
    with pytest.raises(ValueError):
        normalize_ndc("123456-212-03")
