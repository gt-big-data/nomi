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
  /**
   * By SPL set id, so every package of one label gets the same answer: where a product's own
   * label differs from its ingredients' ratings, for the personas it was checked for.
   */
  labels: Record<
    string,
    {
      /** The personas this label was checked for. */
      personas: string[];
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
  /** The label (SPL set id) the package belongs to. */
  setId?: string | null;
  ingredients: { unii: string; name: string }[];
}

export interface EngineRecord extends ScoreRecord {
  contributions: (ScoreRecord["contributions"][number] & {
    ingredient_uniis: string[];
    citations: Citation[];
  })[];
}

/**
 * "unrated": missing names the active ingredients with no ratings. With reason "child_label", every
 * ingredient is rated but the profile is a child whose age this product's label wasn't checked
 * for: what a label allows by age differs between products with the same ingredient (a sleep aid
 * that says "do not use under 12" against an allergy tablet that doses from 6), so the ingredient
 * ratings alone can't be trusted to say it.
 */
export type ScoreResult =
  EngineRecord | { status: "unrated"; missing: string[]; reason?: "child_label" };

/** Personas whose label directions depend on age. */
export const CHILD_PERSONAS: readonly string[] = [
  "under_2",
  "child_2_5",
  "child_6_11",
  "teen_12_17",
];

/** Hard stops the engine makes from a rating, rather than taken from the product's label. */
export const RATED_STOP_PREFIX = "hs_rated_";

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

/** The dataset spells ingredient names in capitals ("DOXYLAMINE SUCCINATE"). */
const plain = (name: string) => name.toLowerCase();

/** "heavy_alcohol_use" as words. */
const words = (id: string) => id.replaceAll("_", " ");

/**
 * One line per risk: who is rated how high, what in the profile raised it, and the source's
 * words. A modifier's quote goes first, since it says why this profile is different.
 */
function explanationText(
  names: string[],
  severity: number,
  raisedBy: string[],
  citations: Citation[],
): string {
  const who = capitalized(names.map(plain).join(" and "));
  const because = raisedBy.length > 0 ? `, higher because of ${raisedBy.join(" and ")}` : "";
  const rated = `${who} ${names.length > 1 ? "are" : "is"} rated ${severity} of 3 for this profile${because}.`;
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
  const label = product.setId ? ratings.labels[product.setId] : undefined;
  const labelChecked = label?.personas.includes(profile.persona) ?? false;
  const names = new Map(product.ingredients.map((i) => [i.unii, i.name]));

  // dimension -> unii -> severity and citations
  const found = new Map<
    string,
    Map<string, { severity: number; raisedBy: string[]; citations: Citation[] }>
  >();
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
        // The modifiers' sources first: they say why this profile is different.
        const citations = [...used.flatMap((m) => m.citations), ...(rating?.citations ?? [])];
        const raisedBy = used
          .filter((m) => m.severity_change > 0)
          .map((m) => words(m.condition ?? m.medication_type!));
        if (!found.has(dimension)) found.set(dimension, new Map());
        found.get(dimension)!.set(unii, { severity, raisedBy, citations });
      }
    }
  }

  const contributions: EngineRecord["contributions"] = [];
  const explanation: ScoreRecord["explanation"] = [];
  for (const [dimension, byUnii] of found) {
    const top = Math.max(...[...byUnii.values()].map((entry) => entry.severity));
    const uniis = [...byUnii.keys()].filter((unii) => byUnii.get(unii)!.severity === top).sort();
    const citations: Citation[] = [];
    const raisedBy = [...new Set(uniis.flatMap((unii) => byUnii.get(unii)!.raisedBy))];
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
        raisedBy,
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
            id: `${RATED_STOP_PREFIX}${unii}_${profile.persona}`,
            message: `${capitalized(plain(names.get(unii)!))} is not considered safe at this age. Ask a pharmacist or doctor first.`,
          }));

  // A child whose age this label wasn't checked for: a hard stop from the ratings still shows
  // (it can only be more careful than the label), but a score that could be too kind does not.
  if (CHILD_PERSONAS.includes(profile.persona) && !labelChecked && hardStops.length === 0) {
    return { status: "unrated", missing: [], reason: "child_label" };
  }

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
