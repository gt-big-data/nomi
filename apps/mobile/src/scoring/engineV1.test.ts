import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { checkRecords, riskRows } from "../lib/referenceScores.ts";
import type { Profile, Ratings, ScoreResult } from "./engine.ts";
import { scaleScore, scoreV1, type Evidence, type RelativeRisk } from "./engineV1.ts";

const read = (path: string | URL) => JSON.parse(readFileSync(path, "utf8"));
const RATINGS: Ratings = read(new URL("./ratings.json", import.meta.url));
const EVIDENCE: Evidence = read(new URL("./evidence.json", import.meta.url));

const ADULT: Profile = { persona: "adult_18_64", conditions: [], medicationTypes: [] };
const cite = { source: "publication" as const, section: "Test 2020, Table 1", url: "https://example.org", citation: "Test A. 2020" };

function rr(dimension: string, estimate: number, applies: Partial<RelativeRisk> = {}): RelativeRisk {
  return {
    dimension,
    persona: "all",
    condition: null,
    medication_type: null,
    measure: "RR",
    estimate,
    ci95: [estimate * 0.8, estimate * 1.2],
    grade: "meta_analysis",
    citation: cite,
    ...applies,
  };
}

// Two real UNIIs with made-up evidence, scored for an adult (no v0 hard stops), so only the v1
// arithmetic is under test.
const [A, B] = Object.keys(RATINGS.ingredients).sort();
const product = (uniis: string[]) => ({ ndc11: "00000000000", ingredients: uniis.map((unii) => ({ unii, name: unii })) });

function evidence(rowsA: RelativeRisk[], rowsB: RelativeRisk[] = [], baselines: Evidence["baselines"] = []): Evidence {
  const entry = (rows: RelativeRisk[]) => ({ name: "x", relative_risks: rows, insufficient: [], faers: [] });
  return { course_days: 10, ingredients: { [A]: entry(rowsA), [B]: entry(rowsB) }, baselines };
}
const base = (dimension: string, annual: number, applies: Partial<RelativeRisk> = {}) => ({
  dimension,
  persona: "all",
  condition: null,
  medication_type: null,
  annual_incidence: annual,
  as_reported: "",
  citation: cite,
  ...applies,
});

const scored = (result: ScoreResult) => {
  assert.ok(!("status" in result), "unrated");
  return result;
};

test("the scale is anchored to the CIOMS bands", () => {
  assert.equal(scaleScore(0), 100);
  assert.equal(scaleScore(1e-5), 100);
  assert.equal(scaleScore(1e-4), 75);
  assert.equal(scaleScore(1e-3), 50);
  assert.equal(scaleScore(1e-2), 25);
  assert.equal(scaleScore(1e-1), 0);
  assert.equal(scaleScore(1), 0);
});

test("excess risk is baseline times (RR minus 1) over a 10-day course", () => {
  // 0.0365 a year * (2 - 1) * 10/365 = 1e-3, so 50.
  const ev = evidence([rr("liver", 2)], [], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.equal(record.score, 50);
  assert.equal(record.contributions[0].points, 50);
});

test("relative risks multiply across ingredients", () => {
  // 1.5 * 2 = 3, so 0.0365 * 2 * 10/365 = 2e-3.
  const ev = evidence([rr("liver", 1.5)], [rr("liver", 2)], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A, B]), ADULT, RATINGS, ev));
  assert.equal(record.score, Math.round(100 - 25 * (Math.log10(2e-3) + 5)));
});

test("an estimate at or below 1 gives nothing", () => {
  const ev = evidence([rr("liver", 0.9)], [], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.equal(record.score, 100);
  assert.equal(record.contributions.length, 0);
});

test("a row for the profile replaces the general one, largest first", () => {
  const rows = [
    rr("liver", 1.2),
    rr("liver", 3, { condition: "heavy_alcohol_use" }),
    rr("liver", 2, { persona: "adult_65_plus" }),
  ];
  const ev = evidence(rows, [], [base("liver", 0.0365)]);
  const drinker = { ...ADULT, persona: "adult_65_plus", conditions: ["heavy_alcohol_use"] };
  const general = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  const specific = scored(scoreV1(product([A]), drinker, RATINGS, ev));
  // 0.2e-3 for the general row, 2e-3 for the RR 3 row.
  assert.equal(general.score, Math.round(100 - 25 * (Math.log10(2e-4) + 5)));
  assert.equal(specific.score, Math.round(100 - 25 * (Math.log10(2e-3) + 5)));
});

test("no baseline means no points and an insufficient note", () => {
  const ev = evidence([rr("kidney", 4)]);
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.equal(record.score, 100);
  assert.ok(record.explanation.some((e) => e.template_id === "engine_v1_insufficient"));
});

test("pregnancy falls back to the adult baseline", () => {
  const ev = evidence([rr("liver", 2)], [], [base("liver", 0.0365, { persona: "adult_18_64" })]);
  const record = scored(scoreV1(product([A]), { ...ADULT, persona: "pregnant" }, RATINGS, ev));
  assert.equal(record.score, 50);
});

test("row points add up to 100 minus the score", () => {
  const ev = evidence(
    [rr("liver", 2), rr("kidney", 1.7), rr("gi_bleeding", 1.3)],
    [],
    [base("liver", 0.0365), base("kidney", 0.02), base("gi_bleeding", 0.001)],
  );
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.equal(record.contributions.reduce((s, c) => s + c.points, 0), 100 - record.score);
});

test("an ingredient outside the evidence review is unrated", () => {
  const ev = evidence([]);
  delete ev.ingredients[B];
  const result = scoreV1(product([A, B]), ADULT, RATINGS, ev);
  assert.ok("status" in result && result.status === "unrated");
});

// Every reference product and persona the bundled evidence covers makes a record the screen can show.
const EXAMPLES = new URL("../../../../packages/schema/examples/", import.meta.url);
for (const folder of readdirSync(EXAMPLES, { withFileTypes: true }).filter((e) => e.isDirectory())) {
  const p = read(new URL(`${folder.name}/product.json`, EXAMPLES));
  const scorable = {
    ndc11: p.ndc11,
    setId: p.spl_set_id,
    ingredients: p.ingredients.map((i: { unii: string; name: string }) => ({ unii: i.unii, name: i.name })),
  };
  for (const persona of ["adult_18_64", "adult_65_plus", "pregnant"]) {
    test(`${folder.name}, ${persona}: the bundled evidence gives a valid record`, () => {
      const result = scoreV1(scorable, { ...ADULT, persona }, RATINGS, EVIDENCE);
      if ("status" in result) return;
      checkRecords([result]);
      riskRows(result);
    });
  }
}
