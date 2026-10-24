"""Check ndc_candidates against the fixture shared with the TypeScript copy."""

import json
from pathlib import Path

import pytest

from nomi_pipeline.identity.barcode import ndc_candidates

FIXTURE = Path(__file__).resolve().parents[2] / "packages/schema/fixtures/barcodes.json"
CASES = json.loads(FIXTURE.read_text())


@pytest.mark.parametrize("case", CASES, ids=[c["description"] for c in CASES])
def test_ndc_candidates(case):
    expected = {"status": case["status"], "candidates": case["candidates"]}
    assert ndc_candidates(case["input"]) == expected


def test_fixture_covers_every_status():
    statuses = {c["status"] for c in CASES}
    assert statuses == {"ok", "invalid_format", "bad_check_digit", "not_ndc_barcode"}
