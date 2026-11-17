import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import { isDeepStrictEqual } from "node:util";

import { FIXTURE_BARCODES, lookupFixture } from "./scanFixtures.ts";

test("each dev menu barcode opens its own state", () => {
  const states = Object.entries(FIXTURE_BARCODES).map(([name, barcode]) => {
    const result = lookupFixture(barcode);
    return [name, result.state === "invalid" ? result.reason : result.state];
  });
  assert.deepEqual(Object.fromEntries(states), {
    scored: "scored",
    preliminary: "preliminary",
    homeopathic: "homeopathic",
    not_found: "not_found",
    not_ndc: "not_ndc_barcode",
    misread: "bad_check_digit",
  });
});

test("finds a product from its EAN-13 form", () => {
  const result = lookupFixture("0" + FIXTURE_BARCODES.scored);
  assert.equal(result.state, "scored");
  assert.equal(result.barcode, "0" + FIXTURE_BARCODES.scored);
});

test("shows the Tylenol reference score for the profile it names", () => {
  const file = new URL(
    "../../../../packages/schema/examples/tylenol/expected-scores.json",
    import.meta.url,
  );
  const records: { score: number; tier: string; profile: unknown }[] = JSON.parse(
    readFileSync(file, "utf8"),
  );
  const result = lookupFixture(FIXTURE_BARCODES.scored);
  assert.ok(result.state === "scored");
  const record = records.find((r) => isDeepStrictEqual(r.profile, result.profile));
  assert.ok(record, "no expected-scores record for the fixture's profile");
  assert.deepEqual(
    { score: result.score, tier: result.tier },
    {
      score: record.score,
      tier: record.tier,
    },
  );
});
