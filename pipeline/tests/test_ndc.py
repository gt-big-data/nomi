import pytest
from nomi_pipeline.identity.barcode import ndc_candidates
from nomi_pipeline.ingest._ndc import normalize_ndc


def test_normalizes_a_valid_ndc() -> None:
    assert normalize_ndc("57344-212-03") == "57344021203"


def test_rejects_malformed_ndc() -> None:
    with pytest.raises(ValueError):
        normalize_ndc("not-an-ndc")


def test_rejects_ndc_with_oversized_segment() -> None:
    with pytest.raises(ValueError):
        normalize_ndc("123456-212-03")


@pytest.mark.parametrize(
    ("raw", "ndc11"),
    [
        ("0363-0710-08", "00363071008"),
        ("57344-212-03", "57344021203"),
        ("72043-2500-1", "72043250001"),
    ],
)
def test_normalizes_every_ndc10_layout(raw: str, ndc11: str) -> None:
    assert normalize_ndc(raw) == ndc11


def test_matches_the_barcode_candidates() -> None:
    # The NDC table is joined to scans through barcode.ndc_candidates, so they must agree.
    for raw in ("0363-0710-08", "57344-212-03", "72043-2500-1"):
        ndc10 = raw.replace("-", "")
        upc = "3" + ndc10
        check = (
            10 - sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(upc))) % 10
        ) % 10
        assert normalize_ndc(raw) in ndc_candidates(upc + str(check))["candidates"]


@pytest.mark.parametrize("raw", ["1-1-1", "12345-6789-012", "１234-5678-90"])
def test_rejects_ndc_without_ten_ascii_digits(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_ndc(raw)
