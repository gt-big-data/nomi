import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

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

test("shows Tylenol's reference score for an adult 18-64", () => {
  const file = new URL(
    "../../../../packages/schema/examples/tylenol/expected-scores.json",
    import.meta.url,
  );
  const records: { score: number; tier: string; profile: { persona: string } }[] = JSON.parse(
    readFileSync(file, "utf8"),
  );
  const adult = records.find((record) => record.profile.persona === "adult_18_64");
  const result = lookupFixture(FIXTURE_BARCODES.scored);
  assert.ok(result.state === "scored");
  assert.deepEqual(
    { score: result.score, tier: result.tier },
    {
      score: adult?.score,
      tier: adult?.tier,
    },
  );
});
