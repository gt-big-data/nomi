import assert from "node:assert/strict";
import { test } from "node:test";

import { ingredientName, productName } from "./displayName.ts";

test("title-cases all-caps and all-lowercase product names", () => {
  assert.equal(productName("equate allergy relief"), "Equate Allergy Relief");
  assert.equal(productName("ADVIL PM"), "Advil PM");
  assert.equal(productName("IBUPROFEN 200 MG"), "Ibuprofen 200 mg");
  assert.equal(productName("E-Z-GAS II"), "E-Z-Gas II");
});

test("leaves mixed-case product names alone", () => {
  assert.equal(productName("TYLENOL Extra Strength"), "TYLENOL Extra Strength");
  assert.equal(productName("ZzzQuil Nighttime Sleep-Aid"), "ZzzQuil Nighttime Sleep-Aid");
});

test("sentence-cases ingredient names", () => {
  assert.equal(ingredientName("DIPHENHYDRAMINE HYDROCHLORIDE"), "Diphenhydramine hydrochloride");
  assert.equal(ingredientName("PSEUDOEPHEDRINE HCL"), "Pseudoephedrine HCl");
  assert.equal(ingredientName("Naproxen Sodium"), "Naproxen Sodium");
});
