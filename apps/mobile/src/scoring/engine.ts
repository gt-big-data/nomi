/**
 * The v0 on-device score: one product, one profile, from the bundled ingredient ratings
 * (ratings.json, built by pipeline/src/nomi_pipeline/build/app_ratings.py).
 *
 * It follows the draft convention in packages/schema/examples/README.md exactly, as
 * packages/schema/tests/test_examples.py states it: each ingredient's severity on a dimension is
 * its rating plus the modifiers that match the profile, capped at 3; each dimension costs the
 * points of its highest severity across ingredients; the score is 100 minus those points, clamped
 * to 0. A pediatric rating of 3 at the profile's age is a hard stop. duplicate_dosing is left to
 * the Medicine Cabinet, so ratings.json leaves it out.
 *
 * ratingsData.ts bundles the ratings; this module only reads them, so the tests run it in Node.
 */

import type { Citation as RecordCitation, ScoreRecord } from "../lib/referenceScores.ts";

export interface Citation extends RecordCitation {
  /** The source's own words, where the knowledge base quotes them. */
  quote?: string;
}

export interface Rating {
  dimension: string;
  persona: string;
  severity: number;
  citations: Citation[];
}

export interface Modifier {
  dimension: string;
  condition?: string;
  medication_type?: string;
  severity_change: number;
  /** The personas it applies to; every persona when absent. */
  personas?: string[];
  citations: Citation[];
}

export interface Ratings {
  /** By UNII. Only ratings above 0 are listed. */
  ingredients: Record<string, { name: string; ratings: Rating[]; modifiers: Modifier[] }>;
  /** By NDC11: where a product's own label differs from its ingredients' ratings. */
  labels: Record<
    string,
    {
      /** These replace the ingredient's rating for that dimension and persona; 0 removes it. */
      ratings: (Rating & { unii: string })[];
      hard_stops: { persona: string; id: string; message: string }[];
    }
  >;
}

export interface Profile {
  persona: string;
  conditions: string[];
  medicationTypes: string[];
}

export interface ScorableProduct {
  ndc11: string;
  ingredients: { unii: string; name: string }[];
}

export interface EngineRecord extends ScoreRecord {
  contributions: (ScoreRecord["contributions"][number] & {
    ingredient_uniis: string[];
    citations: Citation[];
  })[];
}

export type ScoreResult = EngineRecord | { status: "unrated"; missing: string[] };

/** Points for severity 1, 2 and 3 under the draft convention (tests/test_examples.py POINTS). */
export const POINTS: Record<number, number> = { 1: 5, 2: 15, 3: 51 };

export function tier(score: number, hardStops: unknown[]): ScoreRecord["tier"] {
  if (hardStops.length > 0) return "red";
  return score >= 75 ? "green" : score >= 50 ? "yellow" : "red";
}

function applies(modifier: Modifier, profile: Profile): boolean {
  const matches =
    (modifier.condition !== undefined && profile.conditions.includes(modifier.condition)) ||
    (modifier.medication_type !== undefined &&
      profile.medicationTypes.includes(modifier.medication_type));
  return matches && (modifier.personas?.includes(profile.persona) ?? true);
}

const sameCitation = (a: Citation, b: Citation) => JSON.stringify(a) === JSON.stringify(b);

const capitalized = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

/** One line per risk, from the ratings alone: who is rated how high, and the source's words. */
function explanationText(names: string[], severity: number, citations: Citation[]): string {
  const who = capitalized(names.join(" and "));
  const rated = `${who} ${names.length > 1 ? "are" : "is"} rated ${severity} of 3 for this profile.`;
  const quote = citations.find((citation) => citation.quote)?.quote;
  return quote ? `${rated} Source: "${quote}"` : rated;
}

/**
 * The product's score for this profile, or "unrated" with the names of the active ingredients
 * that have no ratings: a product is only scored when every active ingredient is rated.
 */
export function score(product: ScorableProduct, profile: Profile, ratings: Ratings): ScoreResult {
  const missing = product.ingredients
    .filter((ingredient) => !(ingredient.unii in ratings.ingredients))
    .map((ingredient) => ingredient.name);
  if (product.ingredients.length === 0 || missing.length > 0) {
    return { status: "unrated", missing };
  }
  const label = ratings.labels[product.ndc11];
  const names = new Map(product.ingredients.map((i) => [i.unii, i.name]));

  // dimension -> unii -> severity and citations
  const found = new Map<string, Map<string, { severity: number; citations: Citation[] }>>();
  const pediatricStops: string[] = [];
  for (const unii of [...new Set(names.keys())]) {
    const own = new Map<string, Rating>();
    for (const rating of ratings.ingredients[unii].ratings) {
      if (rating.persona === profile.persona) own.set(rating.dimension, rating);
    }
    for (const rating of label?.ratings ?? []) {
      if (rating.unii === unii && rating.persona === profile.persona) {
        own.set(rating.dimension, rating);
      }
    }
    if (own.get("pediatric")?.severity === 3) pediatricStops.push(unii);

    const modifiers = ratings.ingredients[unii].modifiers.filter((m) => applies(m, profile));
    const dimensions = new Set([...own.keys(), ...modifiers.map((m) => m.dimension)]);
    for (const dimension of dimensions) {
      const rating = own.get(dimension);
      const used = modifiers.filter((m) => m.dimension === dimension);
      const severity = Math.min(
        3,
        (rating?.severity ?? 0) + used.reduce((sum, m) => sum + m.severity_change, 0),
      );
      if (severity > 0) {
        const citations = [...(rating?.citations ?? []), ...used.flatMap((m) => m.citations)];
        if (!found.has(dimension)) found.set(dimension, new Map());
        found.get(dimension)!.set(unii, { severity, citations });
      }
    }
  }

  const contributions: EngineRecord["contributions"] = [];
  const explanation: ScoreRecord["explanation"] = [];
  for (const [dimension, byUnii] of found) {
    const top = Math.max(...[...byUnii.values()].map((entry) => entry.severity));
    const uniis = [...byUnii.keys()].filter((unii) => byUnii.get(unii)!.severity === top).sort();
    const citations: Citation[] = [];
    for (const unii of uniis) {
      for (const citation of byUnii.get(unii)!.citations) {
        if (!citations.some((seen) => sameCitation(seen, citation))) citations.push(citation);
      }
    }
    contributions.push({ dimension, points: POINTS[top], ingredient_uniis: uniis, citations });
    explanation.push({
      template_id: `engine_v0_${dimension}`,
      text: explanationText(
        uniis.map((unii) => names.get(unii)!),
        top,
        citations,
      ),
    });
  }
  contributions.sort((a, b) => b.points - a.points || (a.dimension < b.dimension ? -1 : 1));

  const labelStops = (label?.hard_stops ?? [])
    .filter((stop) => stop.persona === profile.persona)
    .map(({ id, message }) => ({ id, message }));
  const hardStops =
    pediatricStops.length === 0
      ? []
      : labelStops.length > 0
        ? labelStops
        : pediatricStops.map((unii) => ({
            id: `hs_${unii}_${profile.persona}`,
            message: `${capitalized(names.get(unii)!)} is rated 3 of 3 for use at this age.`,
          }));

  const total = Math.max(0, 100 - contributions.reduce((sum, c) => sum + c.points, 0));
  return {
    ndc11: product.ndc11,
    profile: {
      persona: profile.persona,
      conditions: profile.conditions,
      medication_types: profile.medicationTypes,
    },
    score: total,
    tier: tier(total, hardStops),
    contributions,
    hard_stops_triggered: hardStops,
    explanation,
  };
}
