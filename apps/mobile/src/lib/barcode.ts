/**
 * Turns the scanned barcode into candidate NDC11 codes.
 *
 * A mirror of pipeline/src/nomi_pipeline/identity/barcode.py.
 * Both must give identical output for every case in
 * packages/schema/fixtures/barcodes.json.
 */

export type Status = "ok" | "invalid_format" | "bad_check_digit" | "not_ndc_barcode";

export interface BarcodeResult {
  status: Status;
  candidates: string[];
}

/** Returns the expected check digit of a UPC-A barcode, given its first 11 digits. */
function checkDigit(first11: string): number {
  let odds = 0; // positions 1, 3, 5, 7, 9, 11
  let evens = 0; // positions 2, 4, 6, 8, 10
  for (let i = 0; i < 11; i++) {
    if (i % 2 === 0) {
      odds += Number(first11[i]);
    } else {
      evens += Number(first11[i]);
    }
  }
  const total = odds * 3 + evens;
  return (10 - total % 10) % 10;
}

function fail(status: Status): BarcodeResult {
  return { status, candidates: [] };
}

/**
 * Returns the status and NDC11 candidates for a scanned barcode.
 * Candidates is empty unless status is "ok".
 */
export function ndcCandidates(raw: string): BarcodeResult {
  let code = raw.trim();

  // Only ASCII 0-9.
  if (!/^[0-9]+$/.test(code)) {
    return fail("invalid_format");
  }

  // EAN-13 which has a leading 0.
  if (code.length === 13 && code[0] === "0") {
    code = code.slice(1);
  }
  if (code.length !== 12) {
    return fail("invalid_format");
  }

  // Checked before the "3" prefix so a misread is reported as a misread, not as a non-drug.
  if (checkDigit(code.slice(0, 11)) !== Number(code[11])) {
    return fail("bad_check_digit");
  }

  if (code[0] !== "3") {
    return fail("not_ndc_barcode");
  }

  const ndc10 = code.slice(1, 11);
  return {
    status: "ok",
    candidates: [
      "0" + ndc10, // 4-4-2
      ndc10.slice(0, 5) + "0" + ndc10.slice(5), // 5-3-2
      ndc10.slice(0, 9) + "0" + ndc10[9], // 5-4-1
    ],
  };
}
