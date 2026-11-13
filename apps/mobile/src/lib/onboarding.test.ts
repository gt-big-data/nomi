// Checks how onboarding answers turn into a profile.
import assert from "node:assert/strict";
import { test } from "node:test";

import { askAbout, startingDraft, toProfile } from "./onboarding.ts";
import { defaultProfile } from "../storage/profile.ts";

test("skipping every question gives the default profile", () => {
  assert.deepEqual(toProfile(startingDraft), defaultProfile);
});

test("pregnant or breastfeeding replaces the age group", () => {
  assert.equal(toProfile({ ...startingDraft, pregnancy: "pregnant" }).persona, "pregnant");
  assert.equal(
    toProfile({ ...startingDraft, age: "teen_12_17", pregnancy: "breastfeeding" }).persona,
    "breastfeeding",
  );
  // Everyone is asked, at any age.
  assert.equal(
    toProfile({ ...startingDraft, age: "adult_65_plus", pregnancy: "pregnant" }).persona,
    "pregnant",
  );
});

test("no and prefer not to say keep the age group", () => {
  assert.equal(toProfile({ ...startingDraft, pregnancy: "no" }).persona, "adult_18_64");
  assert.equal(toProfile({ ...startingDraft, pregnancy: "undisclosed" }).persona, "adult_18_64");
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

test("questions are worded for who the profile is for", () => {
  assert.equal(askAbout("self").are, "are you");
  assert.equal(askAbout("someone_else").do, "do they");
  assert.equal(askAbout("child").are, "is your child");
});
