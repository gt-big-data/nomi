// Checks how onboarding answers turn into a profile.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  askAbout,
  asksPregnancy,
  type Draft,
  questionNumber,
  startingAge,
  startingDraft,
  toProfile,
  withRelation,
} from "./onboarding.ts";
import {
  conditionText,
  defaultProfile,
  medicationTypeText,
  personaText,
  toScoringProfile,
} from "../storage/profile.ts";

function readSchema(name: string) {
  const url = new URL(`../../../../packages/schema/schemas/${name}`, import.meta.url);
  return JSON.parse(readFileSync(url, "utf8"));
}

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

test("the age question starts on 18-64 for you, but on nothing for anyone else", () => {
  assert.equal(startingAge(startingDraft), "adult_18_64");
  assert.equal(startingAge({ ...startingDraft, relation: "child" }), null);
  assert.equal(startingAge({ ...startingDraft, relation: "someone_else" }), null);
  assert.equal(startingAge({ ...startingDraft, relation: "child", age: "child_2_5" }), "child_2_5");
});

test("switching to someone else clears the last person's answers", () => {
  const self: Draft = {
    ...startingDraft,
    age: "adult_18_64",
    pregnancy: "pregnant",
    conditions: ["asthma"],
    medicationTypes: ["ssri_snri"],
  };
  const parent = { ...withRelation(self, "someone_else"), age: "adult_65_plus" } as const;
  assert.equal(toProfile(parent).persona, "adult_65_plus");
  assert.deepEqual(toProfile(parent).conditions, []);
  assert.deepEqual(toProfile(parent).medication_types, []);
  assert.equal(withRelation(self, "self"), self);
});

test("the counter leaves out the pregnancy question for a child", () => {
  assert.deepEqual(questionNumber(startingDraft, "conditions"), { step: 4, total: 5 });
  const child = { ...startingDraft, relation: "child" } as const;
  assert.deepEqual(questionNumber(child, "conditions"), { step: 3, total: 4 });
  assert.deepEqual(questionNumber(child, "medicines"), { step: 4, total: 4 });
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

test("the scoring profile has only the fields and values the schema allows", () => {
  const profile = readSchema("score-record.schema.json").$defs.profile;
  assert.deepEqual(
    Object.keys(toScoringProfile(defaultProfile)).sort(),
    Object.keys(profile.properties).sort(),
  );
  const common = readSchema("common.schema.json").$defs;
  assert.deepEqual(Object.keys(personaText).sort(), [...common.persona.enum].sort());
  assert.deepEqual(Object.keys(conditionText).sort(), [...common.condition.enum].sort());
  assert.deepEqual(Object.keys(medicationTypeText).sort(), [...common.medication_type.enum].sort());
});

test("questions are worded for who the profile is for", () => {
  assert.equal(askAbout("self").are, "are you");
  assert.equal(askAbout("someone_else").do, "do they");
  assert.equal(askAbout("child").are, "is your child");
  assert.equal(askAbout("someone_else").your, "their");
});
