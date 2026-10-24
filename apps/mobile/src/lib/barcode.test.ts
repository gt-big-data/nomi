// Checks ndcCandidates against the fixture shared with the Python copy.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { ndcCandidates, type Status } from "./barcode.ts";

interface Case {
  description: string;
  input: string;
  status: Status;
  candidates: string[];
}

const fixture = new URL("../../../../packages/schema/fixtures/barcodes.json", import.meta.url);
const cases: Case[] = JSON.parse(readFileSync(fixture, "utf8"));

for (const c of cases) {
  test(c.description, () => {
    assert.deepEqual(ndcCandidates(c.input), { status: c.status, candidates: c.candidates });
  });
}

test("fixture covers every status", () => {
  const statuses = new Set(cases.map((c) => c.status));
  const expected = new Set(["ok", "invalid_format", "bad_check_digit", "not_ndc_barcode"]);
  assert.deepEqual(statuses, expected);
});
