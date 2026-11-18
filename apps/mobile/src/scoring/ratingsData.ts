/**
 * Bundles the ingredient ratings into the app. ratings.json is generated from
 * pipeline/knowledge/ingredients; see engine.ts for how it is read.
 */

import ratings from "./ratings.json";

import type { Ratings } from "./engine";

export const RATINGS = ratings as Ratings;
