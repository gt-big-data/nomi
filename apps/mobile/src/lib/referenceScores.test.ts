import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { DatabaseSync } from "node:sqlite";
import { test } from "node:test";

import { buildDataset, referenceProducts } from "../../scripts/fixture.mts";
import { ndcCandidates } from "./barcode.ts";
import { lookupBarcode, type Dataset } from "./db.ts";
import { DEMO_PROFILES } from "./demoProfiles.ts";
import {
  checkRecords,
  DIMENSION_NAMES,
  findScore,
  profileNotes,
  recordTier,
  riskRows,
} from "./referenceScores.ts";
import { REFERENCE_BARCODES, STATE_BARCODES } from "./testBarcodes.ts";

const EXAMPLES = new URL("../../../../packages/schema/examples/", import.meta.url);
const FOLDERS = readdirSync(EXAMPLES, { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name);

// The files referenceScoreData.ts bundles (Node can't load its JSON imports, so read them here).
const RECORDS = checkRecords(
  FOLDERS.flatMap((folder) =>
    JSON.parse(readFileSync(new URL(`${folder}/expected-scores.json`, EXAMPLES), "utf8")),
  ),
);

const profile = (id: string) => DEMO_PROFILES.find((p) => p.id === id)!;
const [ADULT, OLDER, CHILD] = [profile("adult"), profile("older"), profile("child")];

function fixtureDb(): Dataset {
  const db = new DatabaseSync(":memory:");
  buildDataset(db, referenceProducts(), "test");
  return {
    getAllAsync: async <T>(sql: string, params: (string | number)[]) =>
      db.prepare(sql).all(...params) as T[],
  };
}

test("checkRecords refuses a record the screen can't show safely", () => {
  const [good] = RECORDS;
  assert.throws(() => checkRecords([{ ...good, tier: "orange" }]), /unknown tier/);
  assert.throws(() => checkRecords([{ ...good, score: undefined }]), /no score/);
  assert.throws(
    () => checkRecords([{ ...good, profile: { persona: "adult_18_64" } }]),
    /incomplete profile/,
  );
  const [first] = good.contributions;
  assert.throws(
    () =>
      checkRecords([{ ...good, contributions: [{ ...first, citations: [{ source: "blog" }] }] }]),
    /unknown citation source blog/,
  );
  // A risk that took points off must come with its sentence.
  assert.throws(() => checkRecords([{ ...good, explanation: [] }]), /no explanation line/);
  assert.throws(
    () => checkRecords([{ ...good, contributions: [{ ...first, dimension: "teeth" }] }]),
    /unknown dimension/,
  );
  assert.throws(
    () => checkRecords([{ ...good, hard_stops_triggered: [{ id: "hs_x", message: "" }] }]),
    /hard stop without id or message/,
  );
  const stop = { id: "hs_x", message: "Do not use." };
  assert.throws(
    () => checkRecords([{ ...good, hard_stops_triggered: [stop, stop] }]),
    /hard stop hs_x twice/,
  );
});

test("every reference barcode finds its product and a score for every demo profile", async () => {
  const db = fixtureDb();
  for (const { barcode, name } of REFERENCE_BARCODES) {
    const lookup = await lookupBarcode(barcode, db);
    assert.equal(lookup.status, "resolved", name);
    assert.ok("product" in lookup);
    for (const profile of DEMO_PROFILES) {
      assert.ok(findScore(RECORDS, lookup.product.ndc11, profile), `${name}, ${profile.id}`);
    }
  }
});

test("the state barcodes show the states they are named for", async () => {
  const db = fixtureDb();
  const statuses = await Promise.all(
    STATE_BARCODES.map(async ({ barcode }) => (await lookupBarcode(barcode, db)).status),
  );
  assert.deepEqual(statuses, ["not_found", "not_ndc_barcode", "bad_check_digit"]);
  // The made-up drug barcode is a well-formed NDC barcode, so "not found" is the real answer.
  assert.equal(ndcCandidates(STATE_BARCODES[0].barcode).status, "ok");
});

test("a score is only found for the exact profile it was worked out for", () => {
  const aleve = "00280608020";
  const older = findScore(RECORDS, aleve, OLDER)!;
  assert.equal(older.score, 0);
  // Same persona without the condition: no record, rather than the 65+ hypertension one.
  assert.equal(findScore(RECORDS, aleve, { ...OLDER, conditions: [] }), undefined);
  // Order doesn't matter, but every item does: two of one condition isn't one of each.
  const two = { ...OLDER, conditions: ["hypertension", "kidney_disease"] };
  assert.equal(
    findScore(
      [
        {
          ...older,
          profile: {
            ...older.profile,
            conditions: ["kidney_disease", "hypertension"],
          },
        },
      ],
      aleve,
      two,
    )?.score,
    0,
  );
  assert.equal(
    findScore(
      [
        {
          ...older,
          profile: {
            ...older.profile,
            conditions: ["hypertension", "hypertension"],
          },
        },
      ],
      aleve,
      two,
    ),
    undefined,
  );
  assert.equal(findScore(RECORDS, "00000000000", OLDER), undefined);
});

test("risk rows are largest first, named, explained and sourced", () => {
  for (const record of RECORDS) {
    const rows = riskRows(record);
    const points = rows.map((row) => row.points);
    assert.deepEqual(
      points,
      [...points].sort((a, b) => b - a),
    );
    for (const row of rows) {
      const where = `${record.ndc11} ${record.profile.persona} ${row.dimension}`;
      assert.ok(DIMENSION_NAMES[row.dimension], `no name: ${where}`);
      assert.ok(row.detail, `no explanation: ${where}`);
      assert.ok(row.citations.length > 0, `no source: ${where}`);
      const keys = row.citations.map((c) => `${c.source} ${c.url ?? c.section}`);
      assert.equal(new Set(keys).size, keys.length, `repeated source: ${where}`);
    }
  }
});

test("the not-enough-evidence note is not shown", () => {
  const record = {
    ...RECORDS[0],
    explanation: [
      ...RECORDS[0].explanation,
      { template_id: "engine_v1_insufficient", text: "Not enough published evidence to rate: x." },
    ],
  };
  assert.ok(!profileNotes(record).some((note) => note.startsWith("Not enough published")));
});

test("the label banner shows only the label's words, never engine notes", () => {
  const record = {
    ...RECORDS[0],
    explanation: [
      ...RECORDS[0].explanation,
      {
        template_id: "engine_v1_note_rebound_overuse",
        text: 'Overuse: Acetaminophen is rated 2 of 3 for this profile. Not scored separately. Label: "do not use for more than 10 days"',
      },
      {
        template_id: "engine_v1_note_skin",
        text: 'Skin: X is rated 1 of 3 for this profile. Not scored separately. Source: "a guideline"',
      },
      { template_id: "engine_v1_note_excipients", text: "Excipients: X is rated 1 of 3." },
      { template_id: "engine_v1_under_one_point", text: "Under one point each: x." },
    ],
  };
  const notes = profileNotes(record);
  assert.ok(notes.includes("Do not use for more than 10 days."));
  assert.ok(!notes.some((note) => /rated \d of 3|Under one point|a guideline/.test(note)));
});

test("every explanation line reaches the screen, except the draft note and what a hard stop says", () => {
  for (const record of RECORDS) {
    const shown = new Set([...riskRows(record).map((row) => row.detail), ...profileNotes(record)]);
    const stopped = record.hard_stops_triggered.length > 0;
    for (const line of record.explanation) {
      if (line.template_id.endsWith("_fixture_draft")) continue;
      if (stopped && line.template_id.endsWith("_child_directions")) continue;
      assert.ok(shown.has(line.text), `${record.ndc11} ${record.profile.persona}: ${line.text}`);
    }
  }
});

test("child directions are shown, and ZzzQuil is do-not-use for a child", () => {
  const equate = findScore(RECORDS, "79903029710", CHILD)!;
  assert.ok(profileNotes(equate).some((note) => note.includes("induce sleep in children")));

  const zzzquil = findScore(RECORDS, "84126031604", CHILD)!;
  assert.equal(recordTier(zzzquil), "stop");
  // Its banner says it; the directions line saying the same would be a second, weaker banner.
  assert.deepEqual(profileNotes(zzzquil), []);
  assert.equal(profileNotes(findScore(RECORDS, "84126031604", ADULT)!).length, 0);

  // A hard stop that isn't about age leaves the age directions to say.
  const interaction = { id: "hs_blood_thinner", message: "Ask a doctor first." };
  const withOtherStop = { ...equate, hard_stops_triggered: [interaction] };
  assert.deepEqual(profileNotes(withOtherStop), profileNotes(equate));
});

test("Aleve shows the profile change the demo relies on", () => {
  const adultScore = findScore(RECORDS, "00280608020", ADULT)!;
  const olderScore = findScore(RECORDS, "00280608020", OLDER)!;
  assert.deepEqual([adultScore.score, adultScore.tier], [55, "yellow"]);
  assert.deepEqual([olderScore.score, olderScore.tier], [0, "red"]);
  assert.deepEqual(
    riskRows(olderScore).map((row) => row.dimension),
    ["cardiovascular_bp", "gi_bleeding", "kidney"],
  );
});
