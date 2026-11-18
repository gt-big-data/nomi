/**
 * Bundles the v1 evidence table into the app. evidence.json is generated from
 * pipeline/knowledge/evidence and the FAERS signals; see engineV1.ts for how it is read.
 */

import evidence from "./evidence.json";

import { checkEvidence, type Evidence } from "./engineV1";

export const EVIDENCE = checkEvidence(evidence as Evidence);
