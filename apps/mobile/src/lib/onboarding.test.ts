// Checks how onboarding answers turn into a profile.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { askAbout, asksPregnancy, startingAge, startingDraft, toProfile } from "./onboarding.ts";
import { defaultProfile, toScoringProfile } from "../storage/profile.ts";

test("skipping every question gives the default profile", () => {
  assert.deepEqual(toProfile(startingDraft), defaultProfile);
});

test("pregnant or breastfeeding replaces an adult or teen age group", () => {
  const adult = { ...startingDraft, age: "adult_18_64", pregnancy: "pregnant" } as const;
  assert.equal(asksPregnancy(adult), true);
  assert.equal(toProfile(adult).persona, "pregnant");
  assert.equal(
    toProfile({ ...startingDraft, age: "teen_12_17", pregnancy: "breastfeeding" }).persona,
    "breastfeeding",
  );
});

test("a child under 2 keeps their age when the parent answered breastfeeding", () => {
  const baby = {
    ...startingDraft,
    relation: "child",
    age: "under_2",
    pregnancy: "breastfeeding",
  } as const;
  assert.equal(asksPregnancy(baby), false);
  assert.equal(toProfile(baby).persona, "under_2");
});

test("a 6-11 year old is not asked about pregnancy, whoever is scanning", () => {
  const child = { ...startingDraft, relation: "someone_else", age: "child_6_11" } as const;
  assert.equal(asksPregnancy(child), false);
  assert.equal(toProfile({ ...child, pregnancy: "pregnant" }).persona, "child_6_11");
});

test("no and prefer not to say keep the age group", () => {
  assert.equal(toProfile({ ...startingDraft, pregnancy: "no" }).persona, "adult_18_64");
  assert.equal(toProfile({ ...startingDraft, pregnancy: "undisclosed" }).persona, "adult_18_64");
});

test("the age question starts on 18-64, but on nothing for a child", () => {
  assert.equal(startingAge(startingDraft), "adult_18_64");
  assert.equal(startingAge({ ...startingDraft, relation: "child" }), null);
  assert.equal(startingAge({ ...startingDraft, relation: "child", age: "child_2_5" }), "child_2_5");
});

test("conditions and medicine types carry over with the schema's field names", () => {
  const profile = toProfile({
    ...startingDraft,
    relation: "someone_else",
    conditions: ["hypertension", "glaucoma"],
    medicationTypes: ["anticoagulants"],
  });
  assert.equal(profile.relation, "someone_else");
  assert.deepEqual(profile.conditions, ["hypertension", "glaucoma"]);
  assert.deepEqual(profile.medication_types, ["anticoagulants"]);
});

test("the scoring profile has only the fields the schema allows", () => {
  const schema = JSON.parse(
    readFileSync(
      new URL("../../../../packages/schema/schemas/score-record.schema.json", import.meta.url),
      "utf8",
    ),
  );
  assert.deepEqual(
    Object.keys(toScoringProfile(defaultProfile)).sort(),
    Object.keys(schema.$defs.profile.properties).sort(),
  );
});

test("questions are worded for who the profile is for", () => {
  assert.equal(askAbout("self").are, "are you");
  assert.equal(askAbout("someone_else").do, "do they");
  assert.equal(askAbout("child").are, "is your child");
});
