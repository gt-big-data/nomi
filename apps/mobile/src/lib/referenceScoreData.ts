/**
 * Bundles the reference products' draft score records into the app. The files are the single
 * source; see referenceScores.ts for what they are and why the app calls them drafts.
 * referenceScores.test.ts checks this list matches the example folders.
 */

import aleve from "../../../../packages/schema/examples/aleve/expected-scores.json";
import nyquil from "../../../../packages/schema/examples/nyquil/expected-scores.json";
import diphenhydramine from "../../../../packages/schema/examples/store-brand-diphenhydramine/expected-scores.json";
import tylenol from "../../../../packages/schema/examples/tylenol/expected-scores.json";
import zzzquil from "../../../../packages/schema/examples/zzzquil/expected-scores.json";

import { checkRecords } from "./referenceScores";

// Checked at load, so a bad record fails the app's first launch instead of showing a wrong tier.
export const REFERENCE_SCORES = checkRecords([
  ...aleve,
  ...nyquil,
  ...diphenhydramine,
  ...tylenol,
  ...zzzquil,
]);
