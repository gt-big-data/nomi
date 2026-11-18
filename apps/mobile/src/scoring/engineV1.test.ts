import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { checkRecords, riskRows } from "../lib/referenceScores.ts";
import type { Profile, Ratings, ScoreResult } from "./engine.ts";
import {
  checkEvidence,
  scaleScore,
  scoreV1,
  type Evidence,
  type Insufficient,
  type RelativeRisk,
} from "./engineV1.ts";

const read = (path: string | URL) => JSON.parse(readFileSync(path, "utf8"));
const RATINGS: Ratings = read(new URL("./ratings.json", import.meta.url));
const EVIDENCE: Evidence = read(new URL("./evidence.json", import.meta.url));

const ADULT: Profile = { persona: "adult_18_64", conditions: [], medicationTypes: [] };
const cite = {
  source: "publication" as const,
  section: "Test 2020, Table 1",
  url: "https://example.org",
  citation: "Test A. 2020",
};

// One outcome id per dimension for the made-up rows (rule 18).
const OUTCOME: Record<string, string> = {
  liver: "acute_liver_injury",
  kidney: "aki_hospital",
  gi_bleeding: "upper_gi_bleeding",
  sedation_falls: "fall_injury",
  anticoagulant_bleeding: "major_bleeding",
};

function rr(
  dimension: string,
  estimate: number,
  applies: Partial<RelativeRisk> = {},
): RelativeRisk {
  return {
    dimension,
    persona: "all",
    condition: null,
    medication_type: null,
    outcome: OUTCOME[dimension] ?? null,
    comparator: "non_use",
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
const product = (uniis: string[]) => ({
  ndc11: "00000000000",
  ingredients: uniis.map((unii) => ({ unii, name: unii })),
});

function evidence(
  rowsA: RelativeRisk[],
  rowsB: RelativeRisk[] = [],
  baselines: Evidence["baselines"] = [],
): Evidence {
  const entry = (rows: RelativeRisk[]) => ({
    name: "x",
    relative_risks: rows,
    insufficient: [],
    faers: [],
  });
  return { course_days: 10, ingredients: { [A]: entry(rowsA), [B]: entry(rowsB) }, baselines };
}
const base = (dimension: string, annual: number, applies: Partial<RelativeRisk> = {}) => ({
  dimension,
  persona: "all",
  condition: null,
  medication_type: null,
  outcome: OUTCOME[dimension] ?? null,
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
  assert.equal(
    record.contributions.reduce((s, c) => s + c.points, 0),
    100 - record.score,
  );
});

test("an ingredient outside the evidence review is unrated", () => {
  const ev = evidence([]);
  delete ev.ingredients[B];
  const result = scoreV1(product([A, B]), ADULT, RATINGS, ev);
  assert.ok("status" in result && result.status === "unrated");
});

test("pregnancy uses the adult baseline over an all-ages one", () => {
  const ev = evidence(
    [rr("liver", 2)],
    [],
    [base("liver", 0.0365, { persona: "adult_18_64" }), base("liver", 0.365)],
  );
  const record = scored(scoreV1(product([A]), { ...ADULT, persona: "pregnant" }, RATINGS, ev));
  assert.equal(record.score, 50);
});

test("a risk under one point still counts and is explained", () => {
  // 1e-3 from liver takes 50 points; 1e-6 from kidney rounds to 0 but is still listed.
  const ev = evidence(
    [rr("liver", 2), rr("kidney", 2)],
    [],
    [base("liver", 0.0365), base("kidney", 0.0000365)],
  );
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.deepEqual(
    record.contributions.map((c) => c.dimension),
    ["liver"],
  );
  assert.ok(record.explanation.some((e) => e.template_id === "engine_v1_under_one_point"));
});

test("insufficient-evidence notes follow their scope", () => {
  const gap = (dimension: string, scope: Partial<Insufficient> = {}): Insufficient => ({
    dimension,
    personas: [],
    conditions: [],
    medication_types: [],
    reason: "",
    ...scope,
  });
  const ev = evidence([]);
  ev.ingredients[A].insufficient = [
    gap("liver", { conditions: ["liver_disease"] }),
    gap("pregnancy_lactation"),
    gap("anticoagulant_bleeding"),
    gap("kidney"),
  ];
  const note = (profile: Profile) => {
    const record = scored(scoreV1(product([A]), profile, RATINGS, ev));
    return record.explanation.find((e) => e.template_id === "engine_v1_insufficient")?.text ?? "";
  };
  const adult = note(ADULT);
  assert.ok(adult.includes("acute kidney injury"));
  assert.ok(!adult.includes("liver") && !adult.includes("pregnancy") && !adult.includes("major"));
  assert.ok(note({ ...ADULT, conditions: ["liver_disease"] }).includes("acute liver injury"));
  assert.ok(note({ ...ADULT, persona: "pregnant" }).includes("pregnancy"));
  assert.ok(note({ ...ADULT, medicationTypes: ["anticoagulants"] }).includes("major bleeding"));
});

test("a FAERS signal is cited on its row, falling back to all ages", () => {
  const ev = evidence([rr("liver", 2)], [], [base("liver", 0.0365)]);
  ev.ingredients[A].faers = [
    {
      dimension: "liver",
      age_band: "all",
      event_group: "hepatic_disorders",
      ic025: 1.5,
      reports: 900,
    },
  ];
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.ok(record.contributions[0].citations.some((c) => c.source === "faers"));
});

test("bad evidence numbers fail the check", () => {
  const ev = evidence([rr("liver", Number.NaN)]);
  assert.throws(() => checkEvidence(ev));
  assert.throws(() => scaleScore(Number.NaN));
});

test("a risk measured inside a group needs that group's baseline", () => {
  const diuretics = { ...ADULT, medicationTypes: ["diuretics"] };
  const rows = [
    rr("kidney", 1.2),
    rr("kidney", 3, { medication_type: "diuretics", comparator: "within_group" }),
  ];
  // Only a whole-population baseline: the group row can't use it, and the general row is not
  // used in its place.
  const without = evidence(rows, [], [base("kidney", 0.0365)]);
  const record = scored(scoreV1(product([A]), diuretics, RATINGS, without));
  assert.equal(record.score, 100);
  assert.ok(record.explanation.some((e) => e.template_id === "engine_v1_insufficient"));
  // With the diuretic users' own rate: 0.0365 * 2 * 10/365 = 2e-3.
  const withGroup = evidence(
    rows,
    [],
    [base("kidney", 0.0365), base("kidney", 0.0365, { medication_type: "diuretics" })],
  );
  const grouped = scored(scoreV1(product([A]), diuretics, RATINGS, withGroup));
  assert.equal(grouped.score, Math.round(100 - 25 * (Math.log10(2e-3) + 5)));
});

test("a risk pairs only with a baseline for the same outcome, and the larger outcome counts", () => {
  const ev = evidence(
    [rr("sedation_falls", 2, { outcome: "fracture" })],
    [rr("sedation_falls", 3)],
    [base("sedation_falls", 0.0365, { outcome: "fracture" }), base("sedation_falls", 0.00365)],
  );
  const record = scored(scoreV1(product([A, B]), ADULT, RATINGS, ev));
  // Fracture term 1e-3 beats the fall-injury term 2e-4; they are not added.
  assert.equal(record.score, 50);
});

test("stomach bleeding is not counted again for anticoagulant users", () => {
  const ev = evidence(
    [rr("gi_bleeding", 2), rr("anticoagulant_bleeding", 2, { medication_type: "anticoagulants" })],
    [],
    [
      base("gi_bleeding", 0.0365),
      base("anticoagulant_bleeding", 0.0365, { medication_type: "anticoagulants" }),
    ],
  );
  const onBloodThinner = { ...ADULT, medicationTypes: ["anticoagulants"] };
  const record = scored(scoreV1(product([A]), onBloodThinner, RATINGS, ev));
  assert.deepEqual(
    record.contributions.map((c) => c.dimension),
    ["anticoagulant_bleeding"],
  );
});

test("a source's own unexposed rate is the baseline before any outside rate", () => {
  const own = {
    annual_incidence: 0.0365,
    personas: ["adult_18_64"],
    as_reported: "x",
    citation: cite,
  };
  const ev = evidence([rr("kidney", 2, { unexposed_incidence: own })], [], [base("kidney", 0.365)]);
  // 0.0365 * 1 * 10/365 = 1e-3, not the outside rate's 1e-2.
  assert.equal(scored(scoreV1(product([A]), ADULT, RATINGS, ev)).score, 50);
});

test("a sentence names the outcome the study measured", () => {
  const ev = evidence(
    [rr("cardiovascular_bp", 2, { outcome: "mi" })],
    [],
    [base("cardiovascular_bp", 0.0365, { outcome: "mi" })],
  );
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.ok(record.explanation[0].text.startsWith("Heart attack:"));
});

test("a source's own rate is not used for ages its population leaves out", () => {
  const own = {
    annual_incidence: 0.0365,
    personas: ["adult_65_plus"],
    as_reported: "x",
    citation: cite,
  };
  const ev = evidence([rr("kidney", 2, { unexposed_incidence: own })], [], [base("kidney", 0.365)]);
  // The outside rate: 0.365 * 1 * 10/365 = 1e-2, score 25.
  assert.equal(scored(scoreV1(product([A]), ADULT, RATINGS, ev)).score, 25);
});

test("a credible interval is labelled as one", () => {
  const ev = evidence([rr("liver", 2, { interval: "credible" })], [], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A]), ADULT, RATINGS, ev));
  assert.ok(record.explanation[0].text.includes("credible interval"));
});

test("an all-attributes note shows only to profiles with every attribute", () => {
  const ev = evidence([]);
  ev.ingredients[A].insufficient = [
    {
      dimension: "kidney",
      personas: ["adult_65_plus"],
      conditions: ["hypertension"],
      medication_types: [],
      require_all: true,
      reason: "",
    },
  ];
  const note = (profile: Profile) =>
    scored(scoreV1(product([A]), profile, RATINGS, ev)).explanation.some(
      (e) => e.template_id === "engine_v1_insufficient",
    );
  assert.equal(note({ ...ADULT, persona: "adult_65_plus" }), false);
  assert.equal(note({ ...ADULT, conditions: ["hypertension"] }), false);
  assert.equal(note({ ...ADULT, persona: "adult_65_plus", conditions: ["hypertension"] }), true);
});

test("a subgroup note says when the general estimate is still used", () => {
  const ev = evidence([rr("liver", 2)], [], [base("liver", 0.0365)]);
  ev.ingredients[A].insufficient = [
    {
      dimension: "liver",
      personas: [],
      conditions: ["heavy_alcohol_use"],
      medication_types: [],
      reason: "",
    },
  ];
  const record = scored(
    scoreV1(product([A]), { ...ADULT, conditions: ["heavy_alcohol_use"] }, RATINGS, ev),
  );
  const note = record.explanation.find((e) => e.template_id === "engine_v1_insufficient")!;
  assert.ok(note.text.includes("the general estimate is used"));
});

// The bundled evidence: every reference product is rated for these personas, and the scores are
// pinned so a change to the evidence shows up here as a deliberate update.
const GOLDEN: Record<string, Record<string, number>> = {
  aleve: { adult_18_64: 78, adult_65_plus: 62, pregnant: 78 },
  nyquil: { adult_18_64: 82, adult_65_plus: 45, pregnant: 82 },
  "store-brand-diphenhydramine": { adult_18_64: 100, adult_65_plus: 45, pregnant: 100 },
  tylenol: { adult_18_64: 82, adult_65_plus: 82, pregnant: 82 },
  zzzquil: { adult_18_64: 100, adult_65_plus: 45, pregnant: 100 },
};
const EXAMPLES = new URL("../../../../packages/schema/examples/", import.meta.url);
for (const folder of readdirSync(EXAMPLES, { withFileTypes: true }).filter((e) =>
  e.isDirectory(),
)) {
  const p = read(new URL(`${folder.name}/product.json`, EXAMPLES));
  const scorable = {
    ndc11: p.ndc11,
    setId: p.spl_set_id,
    ingredients: p.ingredients.map((i: { unii: string; name: string }) => ({
      unii: i.unii,
      name: i.name,
    })),
  };
  for (const persona of ["adult_18_64", "adult_65_plus", "pregnant"]) {
    test(`${folder.name}, ${persona}: the bundled evidence gives the pinned score`, () => {
      const record = scored(scoreV1(scorable, { ...ADULT, persona }, RATINGS, EVIDENCE));
      checkRecords([record]);
      riskRows(record);
      assert.equal(record.score, GOLDEN[folder.name]?.[persona]);
    });
  }
}

test("a hard stop from the label makes the record red", () => {
  // ZzzQuil's label forbids under 12.
  const p = read(new URL("zzzquil/product.json", EXAMPLES));
  const result = scoreV1(
    { ndc11: p.ndc11, setId: p.spl_set_id, ingredients: p.ingredients },
    { ...ADULT, persona: "child_6_11" },
    RATINGS,
    EVIDENCE,
  );
  const record = scored(result);
  assert.ok(record.hard_stops_triggered.length > 0);
  assert.equal(record.tier, "red");
});

test("a child whose age the label wasn't checked for is unrated", () => {
  const result = scoreV1(
    product([A]),
    { ...ADULT, persona: "child_6_11" },
    RATINGS,
    EVIDENCE.ingredients[A] ? EVIDENCE : evidence([]),
  );
  assert.ok("status" in result && result.reason === "child_label");
});
