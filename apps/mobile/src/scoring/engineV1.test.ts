import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { test } from "node:test";

import { checkRecords, riskRows } from "../lib/referenceScores.ts";
import type { Profile, Ratings, ScoreResult } from "./engine.ts";
import {
  calibrate,
  calibrationLevels,
  calibrationPairs,
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
// A and B with no v0 ratings, so the made-up evidence alone decides (rules 31 to 36 add nothing).
const BARE: Ratings = {
  ...RATINGS,
  ingredients: {
    ...RATINGS.ingredients,
    [A]: { ...RATINGS.ingredients[A], ratings: [], modifiers: [] },
    [B]: { ...RATINGS.ingredients[B], ratings: [], modifiers: [] },
  },
};
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
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
  assert.equal(record.score, 50);
  assert.equal(record.contributions[0].points, 50);
});

test("relative risks multiply across ingredients", () => {
  // 1.5 * 2 = 3, so 0.0365 * 2 * 10/365 = 2e-3.
  const ev = evidence([rr("liver", 1.5)], [rr("liver", 2)], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A, B]), ADULT, BARE, ev));
  assert.equal(record.score, Math.round(100 - 25 * (Math.log10(2e-3) + 5)));
});

test("an estimate at or below 1 gives nothing", () => {
  const ev = evidence([rr("liver", 0.9)], [], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
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
  const general = scored(scoreV1(product([A]), ADULT, BARE, ev));
  const specific = scored(scoreV1(product([A]), drinker, BARE, ev));
  // 0.2e-3 for the general row, 2e-3 for the RR 3 row.
  assert.equal(general.score, Math.round(100 - 25 * (Math.log10(2e-4) + 5)));
  assert.equal(specific.score, Math.round(100 - 25 * (Math.log10(2e-3) + 5)));
});

test("no baseline means no points and an insufficient note", () => {
  const ev = evidence([rr("kidney", 4)]);
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
  assert.equal(record.score, 100);
  assert.ok(record.explanation.some((e) => e.template_id === "engine_v1_insufficient"));
});

test("pregnancy falls back to the adult baseline", () => {
  const ev = evidence([rr("liver", 2)], [], [base("liver", 0.0365, { persona: "adult_18_64" })]);
  const record = scored(scoreV1(product([A]), { ...ADULT, persona: "pregnant" }, BARE, ev));
  assert.equal(record.score, 50);
});

test("row points add up to 100 minus the score", () => {
  const ev = evidence(
    [rr("liver", 2), rr("kidney", 1.7), rr("gi_bleeding", 1.3)],
    [],
    [base("liver", 0.0365), base("kidney", 0.02), base("gi_bleeding", 0.001)],
  );
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
  assert.equal(
    record.contributions.reduce((s, c) => s + c.points, 0),
    100 - record.score,
  );
});

test("an ingredient outside the evidence review is unrated", () => {
  const ev = evidence([]);
  delete ev.ingredients[B];
  const result = scoreV1(product([A, B]), ADULT, BARE, ev);
  assert.ok("status" in result && result.status === "unrated");
});

test("pregnancy uses the adult baseline over an all-ages one", () => {
  const ev = evidence(
    [rr("liver", 2)],
    [],
    [base("liver", 0.0365, { persona: "adult_18_64" }), base("liver", 0.365)],
  );
  const record = scored(scoreV1(product([A]), { ...ADULT, persona: "pregnant" }, BARE, ev));
  assert.equal(record.score, 50);
});

test("a risk under one point still counts and is explained", () => {
  // 1e-3 from liver takes 50 points; 1e-6 from kidney rounds to 0 but is still listed.
  const ev = evidence(
    [rr("liver", 2), rr("kidney", 2)],
    [],
    [base("liver", 0.0365), base("kidney", 0.0000365)],
  );
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
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
    const record = scored(scoreV1(product([A]), profile, BARE, ev));
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
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
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
  const record = scored(scoreV1(product([A]), diuretics, BARE, without));
  assert.equal(record.score, 100);
  assert.ok(record.explanation.some((e) => e.template_id === "engine_v1_insufficient"));
  // With the diuretic users' own rate: 0.0365 * 2 * 10/365 = 2e-3.
  const withGroup = evidence(
    rows,
    [],
    [base("kidney", 0.0365), base("kidney", 0.0365, { medication_type: "diuretics" })],
  );
  const grouped = scored(scoreV1(product([A]), diuretics, BARE, withGroup));
  assert.equal(grouped.score, Math.round(100 - 25 * (Math.log10(2e-3) + 5)));
});

test("a risk pairs only with a baseline for the same outcome, and the larger outcome counts", () => {
  const ev = evidence(
    [rr("sedation_falls", 2, { outcome: "fracture" })],
    [rr("sedation_falls", 3)],
    [base("sedation_falls", 0.0365, { outcome: "fracture" }), base("sedation_falls", 0.00365)],
  );
  const record = scored(scoreV1(product([A, B]), ADULT, BARE, ev));
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
  const record = scored(scoreV1(product([A]), onBloodThinner, BARE, ev));
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
  assert.equal(scored(scoreV1(product([A]), ADULT, BARE, ev)).score, 50);
});

test("a sentence names the outcome the study measured", () => {
  const ev = evidence(
    [rr("cardiovascular_bp", 2, { outcome: "mi" })],
    [],
    [base("cardiovascular_bp", 0.0365, { outcome: "mi" })],
  );
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
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
  assert.equal(scored(scoreV1(product([A]), ADULT, BARE, ev)).score, 25);
});

test("a credible interval is labelled as one", () => {
  const ev = evidence([rr("liver", 2, { interval: "credible" })], [], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A]), ADULT, BARE, ev));
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
    scored(scoreV1(product([A]), profile, BARE, ev)).explanation.some(
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
    scoreV1(product([A]), { ...ADULT, conditions: ["heavy_alcohol_use"] }, BARE, ev),
  );
  const note = record.explanation.find((e) => e.template_id === "engine_v1_insufficient")!;
  assert.ok(note.text.includes("the general estimate is used"));
});

// Rules 31 to 36: v0 ratings on the v1 scale.
const rating = (dimension: string, severity: number, persona = "adult_18_64") => ({
  dimension,
  persona,
  severity,
  citations: [{ source: "fda_label" as const, quote: "may occur" }],
});
function rated(
  ratingsA: ReturnType<typeof rating>[],
  ratingsB: ReturnType<typeof rating>[],
  modifiersA: Ratings["ingredients"][string]["modifiers"] = [],
): Ratings {
  return {
    ...BARE,
    ingredients: {
      ...BARE.ingredients,
      [A]: { ...BARE.ingredients[A], ratings: ratingsA, modifiers: modifiersA },
      [B]: { ...BARE.ingredients[B], ratings: ratingsB },
    },
  };
}
const pair = (severity: number, ear: number) => ({
  unii: A,
  dimension: "liver",
  persona: "adult_18_64",
  severity,
  ear,
});

test("a severity means the mean excess risk of its pairs, made non-decreasing", () => {
  assert.deepEqual(calibrationLevels([pair(1, 0), pair(1, 2e-4), pair(2, 3e-4), pair(3, 1e-3)]), {
    1: 1e-4,
    2: 3e-4,
    3: 1e-3,
  });
  // 2 above 3 pools them: (4e-3 + 2e-3) / 2.
  assert.deepEqual(calibrationLevels([pair(1, 0), pair(2, 4e-3), pair(3, 2e-3)]), {
    1: 0,
    2: 3e-3,
    3: 3e-3,
  });
  // An empty severity takes the mean of its neighbours, or the one at an end.
  assert.deepEqual(calibrationLevels([pair(1, 0), pair(3, 2e-3)]), { 1: 0, 2: 1e-3, 3: 2e-3 });
  assert.deepEqual(calibrationLevels([pair(2, 1e-3)]), { 1: 1e-3, 2: 1e-3, 3: 1e-3 });
  assert.deepEqual(calibrationLevels([]), { 1: 0, 2: 0, 3: 0 });
});

test("a rating with no study counts as the excess risk its severity stands for", () => {
  // B's liver rating 2 is studied: 1e-3. So severity 2 means 1e-3, and A's kidney 2 counts 1e-3.
  const ev = evidence([], [rr("liver", 2)], [base("liver", 0.0365)]);
  const ratings = rated([rating("kidney", 2)], [rating("liver", 2)]);
  assert.deepEqual(calibrationPairs(ratings, ev).length, 1);
  const record = scored(scoreV1(product([A]), ADULT, ratings, ev));
  assert.equal(record.score, 50);
  assert.equal(record.contributions[0].dimension, "kidney");
  const line = record.explanation.find((e) => e.template_id === "engine_v1_kidney")!;
  assert.ok(line.text.includes("rated 2 of 3") && line.text.includes("may occur"));
});

test("a study and a rating of the same harm count once, the larger", () => {
  // B's study gives 1e-3; A's uncovered liver rating 3 also stands for 1e-3. Added they would be
  // 2e-3 (score 43); counted once, 50.
  const ev = evidence([], [rr("liver", 2)], [base("liver", 0.0365)]);
  const ratings = rated([rating("liver", 3)], [rating("liver", 2)]);
  const record = scored(scoreV1(product([A, B]), ADULT, ratings, ev));
  assert.equal(record.score, 50);
  assert.equal(record.contributions.length, 1);
});

test("a study that finds no excess risk replaces the rating", () => {
  const ev = evidence([rr("kidney", 0.8)], [rr("liver", 2)], [base("liver", 0.0365)]);
  const ratings = rated([rating("kidney", 2)], [rating("liver", 2)]);
  assert.equal(scored(scoreV1(product([A]), ADULT, ratings, ev)).score, 100);
});

test("a study without the profile's condition does not cover the rating it raised", () => {
  const ev = evidence(
    [rr("kidney", 0.8)],
    [rr("liver", 2), rr("kidney", 3)],
    [base("liver", 0.0365), base("kidney", 0.0365)],
  );
  const ratings = rated(
    [rating("kidney", 1)],
    [rating("liver", 2), rating("kidney", 3)],
    [{ dimension: "kidney", condition: "kidney_disease", severity_change: 1, citations: [] }],
  );
  const sick = { ...ADULT, conditions: ["kidney_disease"] };
  assert.equal(scored(scoreV1(product([A]), ADULT, ratings, ev)).score, 100);
  assert.ok(scored(scoreV1(product([A]), sick, ratings, ev)).score < 100);
});

test("rule 37: a blood thinner's bleeding row never deletes a larger stomach-bleeding term", () => {
  // Stomach bleeding study 1e-3; blood-thinner bleeding rated 2, which means 1e-4 here.
  const ev = evidence(
    [rr("gi_bleeding", 2)],
    [rr("liver", 2)],
    [base("gi_bleeding", 0.0365), base("liver", 0.00365)],
  );
  const ratings = rated(
    [],
    [rating("liver", 2)],
    [
      {
        dimension: "anticoagulant_bleeding",
        medication_type: "anticoagulants",
        severity_change: 2,
        citations: [],
      },
    ],
  );
  const alone = scored(scoreV1(product([A]), ADULT, ratings, ev));
  const thinned = scored(
    scoreV1(product([A]), { ...ADULT, medicationTypes: ["anticoagulants"] }, ratings, ev),
  );
  assert.equal(alone.score, 50);
  assert.equal(thinned.score, 50);
  assert.deepEqual(
    thinned.contributions.map((c) => c.dimension),
    ["gi_bleeding"],
  );
});

test("rule 38: a ratio below 1 cancels no other ingredient's harm", () => {
  const ev = evidence([rr("liver", 2)], [rr("liver", 0.5)], [base("liver", 0.0365)]);
  const record = scored(scoreV1(product([A, B]), ADULT, BARE, ev));
  assert.equal(record.score, 50);
});

test("rule 39: a calibration pair needs a baseline even when its ratio is below 1", () => {
  const ev = evidence([rr("kidney", 0.8)], [rr("liver", 2)], [base("liver", 0.0365)]);
  const ratings = rated([rating("kidney", 2)], [rating("liver", 2)]);
  assert.deepEqual(
    calibrationPairs(ratings, ev).map((p) => p.dimension),
    ["liver"],
  );
  ev.baselines.push(base("kidney", 0.0365));
  assert.equal(calibrationPairs(ratings, ev).length, 2);
});

test("rule 40: a rating that is not a serious harm is a note with no points", () => {
  const ev = evidence([], [rr("liver", 2)], [base("liver", 0.0365)]);
  const ratings = rated(
    [rating("efficacy_evidence", 2), rating("rebound_overuse", 2)],
    [rating("liver", 2)],
  );
  const record = scored(scoreV1(product([A]), ADULT, ratings, ev));
  assert.equal(record.score, 100);
  assert.equal(record.contributions.length, 0);
  const notes = record.explanation.filter((e) => e.template_id.startsWith("engine_v1_note_"));
  assert.equal(notes.length, 2);
  assert.ok(notes.every((n) => !n.text.includes(" in ")));
});

test("the bundled evidence gives the calibration printed in v1-method.md section 13.2", () => {
  const { pairs, levels } = calibrate(RATINGS, EVIDENCE);
  assert.deepEqual(
    [1, 2, 3].map((s) => pairs.filter((p) => p.severity === s).length),
    [0, 9, 5],
  );
  assert.equal(levels[1], levels[2]);
  assert.equal(levels[2].toExponential(3), "1.042e-4");
  assert.equal(levels[3].toExponential(3), "4.096e-4");
});

// The bundled evidence: every reference product is rated for these personas, and the scores are
// pinned so a change to the evidence shows up here as a deliberate update.
const GOLDEN: Record<string, Record<string, number>> = {
  aleve: { adult_18_64: 68, adult_65_plus: 62, pregnant: 56 },
  nyquil: { adult_18_64: 63, adult_65_plus: 42, pregnant: 60 },
  "store-brand-diphenhydramine": { adult_18_64: 67, adult_65_plus: 42, pregnant: 63 },
  tylenol: { adult_18_64: 75, adult_65_plus: 75, pregnant: 75 },
  zzzquil: { adult_18_64: 67, adult_65_plus: 42, pregnant: 63 },
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
  // Rule 41.
  assert.ok(record.score <= 49);
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
