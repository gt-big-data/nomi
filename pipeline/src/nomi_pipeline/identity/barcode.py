"""Turns scanned barcode digits into candidate NDC11 codes.

A drug UPC-A barcode is "3" + NDC10 + check digit. The NDC10 has no dashes, so it could be split
4-4-2, 5-3-2 or 5-4-1. We return the NDC11 for all three splits, in that order; the product lookup
decides which one exists. The TypeScript copy in apps/mobile/src/lib/barcode.ts must return
identical output for every case in packages/schema/fixtures/barcodes.json.
"""

from typing import Literal, TypedDict

Status = Literal["ok", "invalid_format", "bad_check_digit", "not_ndc_barcode"]


class BarcodeResult(TypedDict):
    status: Status
    candidates: list[str]


# Trimmed explicitly: str.strip() and JS trim() disagree on some characters, e.g. the BOM.
_TRIM = " \t\n\r\v\f\ufeff"


def _check_digit(data: str) -> int:
    """Returns the expected check digit of a UPC-A or EAN-13 barcode, given every digit but the last.

    Digits are weighted 3, 1, 3, ... starting from the rightmost one.
    """
    total = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(data)))
    return (10 - total % 10) % 10


def _fail(status: Status) -> BarcodeResult:
    return {"status": status, "candidates": []}


def normalize(raw: str) -> str:
    """Returns the barcode as it is parsed: trimmed, and an EAN-13 with a leading 0 as its UPC-A."""
    code = raw.strip(_TRIM)
    return code[1:] if len(code) == 13 and code[0] == "0" else code


def ndc_candidates(raw: str) -> BarcodeResult:
    """Returns the status and NDC11 candidates for a scanned barcode.

    Candidates is empty unless status is "ok".
    """
    code = normalize(raw)

    # isascii() rejects other Unicode digits that isdigit() accepts.
    if not (code.isascii() and code.isdigit()):
        return _fail("invalid_format")

    # Any valid EAN-13 left after normalize() is a real barcode, just not a drug.
    if len(code) == 13:
        if _check_digit(code[:12]) != int(code[12]):
            return _fail("bad_check_digit")
        return _fail("not_ndc_barcode")

    if len(code) != 12:
        return _fail("invalid_format")

    # Checked before the "3" prefix so a misread is reported as a misread, not as a non-drug.
    if _check_digit(code[:11]) != int(code[11]):
        return _fail("bad_check_digit")

    if code[0] != "3":
        return _fail("not_ndc_barcode")

    ndc10 = code[1:11]
    return {
        "status": "ok",
        "candidates": [
            "0" + ndc10,  # 4-4-2
            ndc10[:5] + "0" + ndc10[5:],  # 5-3-2
            ndc10[:9] + "0" + ndc10[9],  # 5-4-1
        ],
    }
