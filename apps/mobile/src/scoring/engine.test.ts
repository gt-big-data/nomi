import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { checkRecords, profileNotes, riskRows } from "../lib/referenceScores.ts";
import { score, tier, type Profile, type Ratings, type ScoreResult } from "./engine.ts";

const EXAMPLES = new URL("../../../../packages/schema/examples/", import.meta.url);
const FOLDERS = readdirSync(EXAMPLES, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);
const read = (path: string | URL) => JSON.parse(readFileSync(path, "utf8"));

// The file ratingsData.ts bundles (Node can't load its JSON import).
const RATINGS: Ratings = read(new URL("./ratings.json", import.meta.url));

const scored = (result: ScoreResult) => {
  assert.ok(!("missing" in result), "unrated");
  return result;
};

const ADULT: Profile = { persona: "adult_18_64", conditions: [], medicationTypes: [] };

for (const folder of FOLDERS) {
  const product = read(new URL(`${folder}/product.json`, EXAMPLES));
  const records = read(new URL(`${folder}/expected-scores.json`, EXAMPLES));
  for (const expected of records) {
    const { persona, conditions, medication_types } = expected.profile;
    test(`${folder}, ${persona}: matches the hand-checked record`, () => {
      const profile = { persona, conditions, medicationTypes: medication_types };
      const record = scored(score(product, profile, RATINGS));
      assert.equal(record.score, expected.score);
      assert.equal(record.tier, expected.tier);
      assert.deepEqual(record.hard_stops_triggered, expected.hard_stops_triggered);
      const points = (r: { contributions: { dimension: string; points: number }[] }) =>
        r.contributions.map(({ dimension, points }) => ({ dimension, points }));
      assert.deepEqual(points(record), points(expected));
      assert.deepEqual(
        record.contributions.map((c) => c.ingredient_uniis),
        expected.contributions.map((c: { ingredient_uniis: string[] }) => c.ingredient_uniis),
      );
      // The result screen can show it: every risk row has its line, and no line is left over.
      checkRecords([record]);
      assert.equal(riskRows(record).length, record.contributions.length);
      assert.deepEqual(profileNotes(record), []);
    });
  }
}

test("a product with an unrated active ingredient is not scored", () => {
  const product = {
    ndc11: "00000000000",
    ingredients: [
      { unii: "362O9ITL9D", name: "acetaminophen" },
      { unii: "NOTRATED00", name: "mystery root" },
    ],
  };
  assert.deepEqual(score(product, ADULT, RATINGS), {
    status: "unrated",
    missing: ["mystery root"],
  });
  assert.deepEqual(score({ ...product, ingredients: [] }, ADULT, RATINGS), {
    status: "unrated",
    missing: [],
  });
});

test("a modifier for the profile raises the severity, capped at 3", () => {
  const product = {
    ndc11: "00000000000",
    ingredients: [{ unii: "362O9ITL9D", name: "acetaminophen" }],
  };
  const liver = (profile: Profile) =>
    scored(score(product, profile, RATINGS)).contributions.find((c) => c.dimension === "liver");
  const drinker = liver({ ...ADULT, conditions: ["heavy_alcohol_use"] })!;
  assert.equal(drinker.points, liver(ADULT)!.points);
  assert.ok(drinker.citations.length > liver(ADULT)!.citations.length);

  const onWarfarin = scored(
    score(product, { ...ADULT, medicationTypes: ["anticoagulants"] }, RATINGS),
  );
  assert.equal(
    onWarfarin.contributions.find((c) => c.dimension === "anticoagulant_bleeding")?.points,
    15,
  );
});

test("a pediatric 3 without a label hard stop gets one named for the ingredient", () => {
  const product = {
    ndc11: "00000000000",
    ingredients: [{ unii: "TC2D6JAD40", name: "diphenhydramine" }],
  };
  const record = scored(score(product, { ...ADULT, persona: "under_2" }, RATINGS));
  assert.deepEqual(
    record.hard_stops_triggered.map((stop) => stop.id),
    ["hs_TC2D6JAD40_under_2"],
  );
  assert.equal(record.tier, "red");
});

test("tiers: green 75+, yellow 50 to 74, red below 50 or with a hard stop", () => {
  assert.deepEqual(
    [75, 74, 50, 49].map((s) => tier(s, [])),
    ["green", "yellow", "yellow", "red"],
  );
  assert.equal(tier(100, [{ id: "x" }]), "red");
});
