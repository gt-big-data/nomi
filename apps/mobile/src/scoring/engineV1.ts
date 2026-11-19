/**
 * The v1 on-device score (v1.6): the excess risk of serious harm from one course of the product
 * for this profile, on the fixed scale in docs/scoring/v1-method.md. Where a study passes the
 * evidence rules, the risk is the published relative risk times its baseline (evidence.json,
 * built by pipeline/src/nomi_pipeline/build/app_evidence.py). Every other v0 rating (ratings.json)
 * counts as the excess risk its severity stands for, fitted to the risks where both exist
 * (rules 31 to 36). One harm counts once. Nothing here is tuned to a product.
 *
 * Hard stops and the child-label rule are the label's, as in v0, so they come from engine.ts.
 */

import { DIMENSION_NAMES } from "../lib/referenceScores.ts";
import {
  capitalized,
  ratedSeverities,
  score as scoreV0,
  tier,
  words,
  type Citation,
  type EngineRecord,
  type Modifier,
  type RatedSeverity,
  type Profile,
  type Ratings,
  type ScorableProduct,
  type ScoreResult,
} from "./engine.ts";

interface Applies {
  persona: string;
  condition: string | null;
  medication_type: string | null;
}

type EvidenceCitation = Citation & { citation: string };

export interface RelativeRisk extends Applies {
  dimension: string;
  /** Rule 18: pairs the row with a baseline for the same outcome. */
  outcome: string | null;
  /** Rule 12: within_group rows need a baseline for the same group. */
  comparator: "non_use" | "within_group";
  measure: string;
  estimate: number;
  ci95: number[];
  /** Rule 27. */
  interval?: "confidence" | "credible";
  /** Rule 20: the source's own unexposed group's rate, used as the baseline when present. */
  unexposed_incidence?: {
    annual_incidence: number;
    /** Third review: the personas the source's population covers; used only for them. */
    personas: string[];
    as_reported: string;
    citation: EvidenceCitation;
  } | null;
  grade: string;
  citation: EvidenceCitation;
}

export interface Baseline extends Applies {
  dimension: string;
  outcome: string | null;
  annual_incidence: number;
  as_reported: string;
  citation: EvidenceCitation;
}

export interface Insufficient {
  dimension: string;
  /** Shown to profiles with any of these; to every profile when all three are empty. */
  personas: string[];
  conditions: string[];
  medication_types: string[];
  /** Rule 28: shown only to profiles with every listed attribute, not any. */
  require_all?: boolean;
  reason: string;
}

export interface FaersSignal {
  dimension: string;
  age_band: string;
  event_group: string;
  ic025: number;
  reports: number;
}

export interface Evidence {
  course_days: number;
  ingredients: Record<
    string,
    {
      name: string;
      relative_risks: RelativeRisk[];
      insufficient: Insufficient[];
      faers: FaersSignal[];
    }
  >;
  baselines: Baseline[];
}

/** What each dimension's outcome is called in a sentence (v1-method.md section 1). */
const OUTCOMES: Record<string, string> = {
  liver: "acute liver injury",
  gi_bleeding: "stomach bleeding",
  kidney: "acute kidney injury",
  cardiovascular_bp: "heart attack, stroke or heart failure",
  anticholinergic_cognitive: "delirium",
  sedation_falls: "a fall injury",
  serotonergic_interactions: "serotonin syndrome",
  anticoagulant_bleeding: "major bleeding",
  pregnancy_lactation: "the pregnancy harm studied",
};

/** Rule 18 and 24: the outcome a row measured, when it is narrower than its dimension's. */
const OUTCOME_IDS: Record<string, string> = {
  acute_liver_failure: "acute liver failure",
  mi: "heart attack",
  stroke: "stroke",
  mi_stroke: "heart attack or stroke",
  fracture: "a fracture",
  hip_fracture: "a hip fracture",
};

/**
 * Rule 7: dimensions whose outcome only exists for some profiles, so a gap in them is only news
 * to those profiles.
 */
const DIMENSION_SCOPE: Record<string, (profile: Profile) => boolean> = {
  pregnancy_lactation: (p) => p.persona === "pregnant" || p.persona === "breastfeeding",
  anticoagulant_bleeding: (p) =>
    p.medicationTypes.includes("anticoagulants") || p.medicationTypes.includes("antiplatelets"),
};

const MEASURES: Record<string, string> = {
  RR: "relative risk",
  OR: "odds ratio",
  HR: "hazard ratio",
  IRR: "rate ratio",
};

const GRADES: Record<string, string> = {
  meta_analysis: "meta-analysis",
  cohort: "cohort study",
  case_control: "case-control study",
  regulatory: "regulatory review",
};

/** FAERS age bands (signal.schema.json) by persona. */
const AGE_BANDS: Record<string, string> = {
  adult_18_64: "18-64",
  pregnant: "18-64",
  breastfeeding: "18-64",
  adult_65_plus: "65+",
  teen_12_17: "12-17",
  child_6_11: "0-11",
  child_2_5: "0-11",
  under_2: "0-11",
};

/** Rule 5: personas whose baseline is their age band's when no row names them. */
const BASELINE_AGE: Record<string, string> = {
  pregnant: "adult_18_64",
  breastfeeding: "adult_18_64",
};

/** Throws unless every number the formula reads is a finite number in range. */
export function checkEvidence(evidence: Evidence): Evidence {
  const finite = (value: unknown, where: string, low = 0) => {
    if (typeof value !== "number" || !Number.isFinite(value) || value <= low) {
      throw new Error(`evidence ${where}: ${String(value)} is not a number above ${low}`);
    }
  };
  finite(evidence.course_days, "course_days");
  for (const [unii, entry] of Object.entries(evidence.ingredients)) {
    for (const row of entry.relative_risks) {
      finite(row.estimate, `${unii} ${row.dimension} estimate`);
      if (!(row.dimension in OUTCOMES)) throw new Error(`evidence ${unii}: ${row.dimension}`);
    }
    for (const gap of entry.insufficient) {
      if (![gap.personas, gap.conditions, gap.medication_types].every(Array.isArray)) {
        throw new Error(`evidence ${unii} ${gap.dimension}: insufficient scope missing`);
      }
    }
  }
  for (const row of evidence.baselines) {
    finite(row.annual_incidence, `baseline ${row.dimension} ${row.persona}`);
    if (row.annual_incidence >= 1)
      throw new Error(`evidence baseline ${row.dimension}: not a rate`);
  }
  return evidence;
}

function matches(row: Applies, persona: string, profile: Profile): boolean {
  return (
    (row.persona === "all" || row.persona === persona) &&
    (row.condition == null || profile.conditions.includes(row.condition)) &&
    (row.medication_type == null || profile.medicationTypes.includes(row.medication_type))
  );
}

const specific = (row: Applies) =>
  row.persona !== "all" || row.condition != null || row.medication_type != null;

/** Rule 3: the largest applying specific row, else the largest applying general row. */
function pick<T extends Applies>(
  rows: T[],
  persona: string,
  profile: Profile,
  value: (row: T) => number,
): T | undefined {
  const applying = rows.filter((row) => matches(row, persona, profile));
  const pool = applying.some(specific) ? applying.filter(specific) : applying;
  return pool.reduce<T | undefined>(
    (best, row) => (best && value(best) >= value(row) ? best : row),
    undefined,
  );
}

/**
 * Rule 5: a pregnant or breastfeeding profile uses its age band's rows (adult_18_64 over "all")
 * unless some row names its own persona.
 */
function baselineFor(
  evidence: Evidence,
  dimension: string,
  outcome: string | null,
  group: Applies | undefined,
  profile: Profile,
): Baseline | undefined {
  let rows = evidence.baselines.filter(
    (row) => row.dimension === dimension && row.outcome === outcome,
  );
  // Rule 12: a risk measured inside a group needs that group's own rate.
  if (group) {
    rows = rows.filter(
      (row) => row.condition === group.condition && row.medication_type === group.medication_type,
    );
  }
  const named = rows.some((row) => row.persona === profile.persona);
  const persona = named ? profile.persona : (BASELINE_AGE[profile.persona] ?? profile.persona);
  return pick(rows, persona, profile, (row) => row.annual_incidence);
}

/** Rule 7. */
function gapApplies(gap: Insufficient, profile: Profile): boolean {
  if (DIMENSION_SCOPE[gap.dimension] && !DIMENSION_SCOPE[gap.dimension](profile)) return false;
  const scoped = gap.personas.length + gap.conditions.length + gap.medication_types.length > 0;
  if (gap.require_all) {
    return (
      gap.personas.every((p) => p === profile.persona) &&
      gap.conditions.every((c) => profile.conditions.includes(c)) &&
      gap.medication_types.every((m) => profile.medicationTypes.includes(m))
    );
  }
  return (
    !scoped ||
    gap.personas.includes(profile.persona) ||
    gap.conditions.some((c) => profile.conditions.includes(c)) ||
    gap.medication_types.some((m) => profile.medicationTypes.includes(m))
  );
}

/** "1 in 25,000" */
function oneIn(probability: number): string {
  const n = 1 / probability;
  const rounded = n >= 100 ? Number(n.toPrecision(2)) : Math.round(n);
  return `1 in ${rounded.toLocaleString("en-US")}`;
}

/** Score on the CIOMS-anchored scale (section 3): 1e-5 is 100, 1e-4 is 75, 1e-3 is 50. */
export function scaleScore(excessRisk: number): number {
  if (!Number.isFinite(excessRisk) || excessRisk < 0) {
    throw new Error(`excess risk ${excessRisk} is not a probability`);
  }
  if (excessRisk === 0) return 100;
  return Math.min(100, Math.max(0, 100 - 25 * (Math.log10(excessRisk) + 5)));
}

/** Rule 8: whole points that add up to total, by largest remainder. */
export function apportion(total: number, weights: number[]): number[] {
  const sum = weights.reduce((a, b) => a + b, 0);
  if (sum === 0 || total === 0) return weights.map(() => 0);
  const exact = weights.map((w) => (total * w) / sum);
  const out = exact.map(Math.floor);
  const order = exact
    .map((x, i) => [x - Math.floor(x), i] as const)
    .sort((a, b) => b[0] - a[0] || a[1] - b[1]);
  const remaining = total - out.reduce((a, b) => a + b, 0);
  for (let k = 0; k < remaining; k++) out[order[k][1]] += 1;
  return out;
}

interface Term {
  dimension: string;
  outcome: string | null;
  ear: number;
  used: { unii: string; row: RelativeRisk }[];
  baseline: Pick<Baseline, "annual_incidence" | "citation">;
}

/**
 * Rules 1 to 30 for one profile: the study term each outcome dimension counts, and, per
 * dimension, the ingredients a study covers (rule 32): a row applies to them and their outcome
 * has a baseline, or the relative risks multiply to 1 or less.
 */
function studyTerms(
  uniis: string[],
  profile: Profile,
  evidence: Evidence,
): {
  terms: Term[];
  covered: Map<string, Set<string>>;
  /** Rule 39: the ingredients whose outcome has a baseline for this profile, by dimension. */
  baselined: Map<string, Set<string>>;
  /** By dimension: each ingredient's own row. */
  rowsUsed: Map<string, Map<string, RelativeRisk>>;
  noBaseline: Set<string>;
} {
  const terms: Term[] = [];
  const covered = new Map<string, Set<string>>();
  const baselined = new Map<string, Set<string>>();
  const rowsUsed = new Map<string, Map<string, RelativeRisk>>();
  const noBaseline = new Set<string>();
  for (const dimension of Object.keys(OUTCOMES)) {
    const used = uniis.flatMap((unii) => {
      const rows = evidence.ingredients[unii].relative_risks.filter(
        (r) => r.dimension === dimension,
      );
      const row = pick(rows, profile.persona, profile, (r) => r.estimate);
      return row ? [{ unii, row }] : [];
    });
    rowsUsed.set(dimension, new Map(used.map(({ unii, row }) => [unii, row])));
    // Rule 18: one term per outcome; the dimension counts the largest.
    const outcomes = [...new Set(used.map(({ row }) => row.outcome))].sort();
    // Rule 42: an ingredient is covered only when its outcome has a baseline.
    const cover = new Set<string>();
    const withBaseline = new Set<string>();
    let best: Term | undefined;
    for (const outcome of outcomes) {
      const same = used.filter(({ row }) => row.outcome === outcome);
      // Rules 4 and 38: no row is a factor of 1, and so is an estimate at or below 1.
      const rr = same.reduce((product, { row }) => product * Math.max(1, row.estimate), 1);
      const groups = [
        ...new Set(
          same
            .filter(({ row }) => row.comparator === "within_group")
            .map(({ row }) => `${row.condition}|${row.medication_type}`),
        ),
      ];
      let baseline: Pick<Baseline, "annual_incidence" | "citation"> | undefined;
      if (groups.length <= 1) {
        const group = same.find(({ row }) => row.comparator === "within_group")?.row;
        // Rule 20: a source's own unexposed rate first (the largest relative risk's, if several).
        const adult = ["pregnant", "breastfeeding"].includes(profile.persona)
          ? "adult_18_64"
          : profile.persona;
        const own = same
          .filter(({ row }) => row.unexposed_incidence?.personas.includes(adult))
          .sort((a, b) => b.row.estimate - a.row.estimate)[0]?.row.unexposed_incidence;
        baseline = own ?? baselineFor(evidence, dimension, outcome, group, profile);
      }
      if (!baseline) {
        if (rr > 1) noBaseline.add(dimension);
        continue;
      }
      for (const { unii } of same) {
        cover.add(unii);
        withBaseline.add(unii);
      }
      if (rr <= 1) continue;
      const ear = (baseline.annual_incidence * (rr - 1) * evidence.course_days) / 365;
      const raising = same.filter(({ row }) => row.estimate > 1);
      if (!best || ear > best.ear) best = { dimension, outcome, ear, used: raising, baseline };
    }
    if (best) terms.push(best);
    covered.set(dimension, cover);
    baselined.set(dimension, withBaseline);
  }
  return { terms, covered, baselined, rowsUsed, noBaseline };
}

/** One calibration pair (rule 33): a v0 severity and the excess risk a study gives the same risk. */
export interface CalibrationPair {
  unii: string;
  dimension: string;
  persona: string;
  severity: number;
  ear: number;
}

export interface Calibration {
  pairs: CalibrationPair[];
  /** Excess risk per course for severity 1, 2 and 3 (rule 34). */
  levels: Record<number, number>;
}

const median = (values: number[]) => {
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 1 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

/**
 * Rule 33: every ingredient-dimension-persona that v0 rates above 0 and a study covers, for a
 * profile with that persona and no condition or medication, scored as that one ingredient.
 * Pairs that repeat the same severity, study rows and excess risk (salts of one ingredient, or
 * personas sharing a row and a baseline) count once.
 */
export function calibrationPairs(ratings: Ratings, evidence: Evidence): CalibrationPair[] {
  const pairs: CalibrationPair[] = [];
  const seen = new Set<string>();
  for (const unii of Object.keys(evidence.ingredients).sort()) {
    const rated = ratings.ingredients[unii];
    if (!rated) continue;
    for (const rating of rated.ratings) {
      if (rating.severity <= 0 || !(rating.dimension in OUTCOMES)) continue;
      const profile = { persona: rating.persona, conditions: [], medicationTypes: [] };
      const { terms, baselined, rowsUsed } = studyTerms([unii], profile, evidence);
      // Rule 39: every pair needs a baseline, whatever its estimate.
      if (!baselined.get(rating.dimension)?.has(unii)) continue;
      const term = terms.find((t) => t.dimension === rating.dimension);
      const ear = term?.ear ?? 0;
      const own = rowsUsed.get(rating.dimension)!.get(unii)!;
      const key = [
        rating.dimension,
        rating.severity,
        ear,
        own.citation.citation,
        own.estimate,
        own.outcome,
      ].join("|");
      if (seen.has(key)) continue;
      seen.add(key);
      pairs.push({
        unii,
        dimension: rating.dimension,
        persona: rating.persona,
        severity: rating.severity,
        ear,
      });
    }
  }
  return pairs;
}

const calibrations = new WeakMap<Evidence, WeakMap<Ratings, Calibration>>();

/** Rule 34: what each v0 severity means in excess risk per course, from the pairs. */
export function calibrate(ratings: Ratings, evidence: Evidence): Calibration {
  const cached = calibrations.get(evidence)?.get(ratings);
  if (cached) return cached;
  const pairs = calibrationPairs(ratings, evidence);
  const levels = calibrationLevels(pairs);
  const result = { pairs, levels };
  if (!calibrations.has(evidence)) calibrations.set(evidence, new WeakMap());
  calibrations.get(evidence)!.set(ratings, result);
  return result;
}

/**
 * Rule 34: the mean excess risk of the pairs at severity 2 and 3, made non-decreasing by pool
 * adjacent violators (weighted by pair count); an empty severity takes the other's fitted value.
 * No pairs at all gives 0. Rule 43: severity 1 is 0 by definition and is not fitted.
 */
/** Rule 43: the severities fitted to the pairs; severity 1 is not a serious harm. */
const FITTED = [2, 3];

export function calibrationLevels(pairs: CalibrationPair[]): Record<number, number> {
  const blocks: { severities: number[]; n: number; mean: number }[] = [];
  for (const severity of FITTED) {
    const at = pairs.filter((p) => p.severity === severity).map((p) => p.ear);
    if (at.length === 0) continue;
    blocks.push({
      severities: [severity],
      n: at.length,
      mean: at.reduce((a, b) => a + b, 0) / at.length,
    });
    // Pool adjacent violators.
    while (blocks.length > 1 && blocks[blocks.length - 2].mean > blocks[blocks.length - 1].mean) {
      const last = blocks.pop()!;
      const prev = blocks.pop()!;
      const n = prev.n + last.n;
      blocks.push({
        severities: [...prev.severities, ...last.severities],
        n,
        mean: (prev.mean * prev.n + last.mean * last.n) / n,
      });
    }
  }
  const fitted: Record<number, number> = {};
  for (const block of blocks)
    for (const severity of block.severities) fitted[severity] = block.mean;
  const levels: Record<number, number> = { 1: 0 };
  for (const severity of FITTED) {
    if (severity in fitted) {
      levels[severity] = fitted[severity];
      continue;
    }
    const below = FITTED.filter((s) => s < severity && s in fitted).pop();
    const above = FITTED.find((s) => s > severity && s in fitted);
    const near = [below, above].filter((s): s is number => s !== undefined).map((s) => fitted[s]);
    levels[severity] = near.length === 0 ? 0 : near.reduce((a, b) => a + b, 0) / near.length;
  }
  return levels;
}

/** The quote a v0 rating cites, for the rating row's sentence. */
const quoteOf = (citations: Citation[]) => citations.find((c) => c.quote)?.quote;
/** The label's own words, when a citation quotes the product label or the OTC monograph. */
const LABEL_SOURCES = new Set(["fda_label", "otc_monograph"]);
/** A note's closing quote: "Label:" for the label's words, which the result screen shows. */
const noteQuote = (citations: Citation[]) => {
  const cited = citations.find((c) => c.quote && LABEL_SOURCES.has(c.source));
  if (cited?.quote) {
    // A label section can hold the whole sentence the quote ends ("50570-1: Do not use to make a
    // child sleepy" for "to make a child sleepy"): use that, so the quote isn't read alone.
    const heading = (cited.section ?? "").replace(/^[\d-]+:\s*/, "");
    const whole = heading.toLowerCase().endsWith(cited.quote.toLowerCase()) ? heading : cited.quote;
    return ` Label: "${whole}"`;
  }
  const quote = quoteOf(citations);
  return quote ? ` Source: "${quote}"` : "";
};

export function scoreV1(
  product: ScorableProduct,
  profile: Profile,
  ratings: Ratings,
  evidence: Evidence,
): ScoreResult {
  // Rule 9: every active ingredient must have been through the evidence review.
  const missing = product.ingredients
    .filter((i) => !(i.unii in evidence.ingredients))
    .map((i) => i.name);
  if (product.ingredients.length === 0 || missing.length > 0) {
    return { status: "unrated", missing };
  }

  // Hard stops and the child-label rule come from the label, exactly as in v0.
  const v0 = scoreV0(product, profile, ratings);
  if ("status" in v0) return v0;

  const uniis = [...new Set(product.ingredients.map((i) => i.unii))].sort();
  const name = (unii: string) => words(evidence.ingredients[unii].name);
  const band = AGE_BANDS[profile.persona];
  const { levels, pairs } = calibrate(ratings, evidence);
  const { found } = ratedSeverities(product, profile, ratings);
  const { terms: studies, covered, noBaseline } = studyTerms(uniis, profile, evidence);

  // Rule 35: per dimension, the larger of the study term and the rating terms.
  interface Row {
    dimension: string;
    ear: number;
    study?: Term;
    rated?: { uniis: string[]; severity: number; raisedBy: string[]; citations: Citation[] };
  }
  const rows: Row[] = [];
  const notes: { template_id: string; text: string }[] = [];
  const stopRatings: [string, RatedSeverity][] = [];
  const noteFor = (dimension: string, unii: string, entry: RatedSeverity) => {
    const because =
      entry.raisedBy.length > 0 ? `, higher because of ${entry.raisedBy.join(" and ")}` : "";
    return {
      template_id: `engine_v1_note_${dimension}`,
      text: `${DIMENSION_NAMES[dimension] ?? capitalized(words(dimension))}: ${capitalized(name(unii))} is rated ${entry.severity} of 3 for this profile${because}. Not scored separately.${noteQuote(entry.citations)}`,
    };
  };
  const dimensions = [...new Set([...Object.keys(OUTCOMES), ...found.keys()])];
  for (const dimension of dimensions) {
    if (!(dimension in OUTCOMES)) {
      // Rules 40 and 44: a note with no points and no excess risk.
      for (const [unii, entry] of found.get(dimension) ?? new Map<string, RatedSeverity>()) {
        if (dimension === "pediatric" && entry.severity === 3) {
          // Rule 45: the hard stop, a row or a note after the totals.
          stopRatings.push([unii, entry]);
          continue;
        }
        notes.push(noteFor(dimension, unii, entry));
      }
      continue;
    }
    const study = studies.find((t) => t.dimension === dimension);
    const uncovered = [...(found.get(dimension) ?? new Map()).entries()].filter(
      ([unii, entry]) =>
        !(
          covered.get(dimension)?.has(unii) &&
          // Rule 32: the row must be the study of the condition or medication that raised it.
          entryMatchesStudy(entry.raisers, unii, dimension, studies, evidence, profile)
        ),
    );
    let rated: Row["rated"];
    const severe = uncovered.filter(([, e]) => e.severity >= 2);
    if (!study && severe.length === 0) {
      // Rule 43: a severity-1 rating with no study is a note.
      for (const [unii, entry] of uncovered) notes.push(noteFor(dimension, unii, entry));
      continue;
    }
    if (severe.length > 0) {
      const severity = Math.max(...severe.map(([, e]) => e.severity));
      const top = severe.filter(([, e]) => e.severity === severity);
      const citations: Citation[] = [];
      for (const [, e] of top) {
        for (const c of e.citations) {
          if (!citations.some((seen) => JSON.stringify(seen) === JSON.stringify(c))) {
            citations.push(c);
          }
        }
      }
      rated = {
        uniis: top.map(([unii]) => unii),
        severity,
        raisedBy: [...new Set(top.flatMap(([, e]) => e.raisedBy))],
        citations,
      };
    }
    const ratedEar = rated ? levels[rated.severity] : 0;
    const studyEar = study?.ear ?? 0;
    if (!study && !rated) continue;
    rows.push(
      study && studyEar >= ratedEar
        ? { dimension, ear: studyEar, study }
        : { dimension, ear: ratedEar, rated },
    );
  }
  const filled = new Set(rows.filter((r) => r.rated).map((r) => r.dimension));
  // Rule 37: on a blood thinner, stomach bleeding and blood-thinner bleeding are one row, the
  // larger of the two.
  const thinned = ["anticoagulants", "antiplatelets"].some((m) =>
    profile.medicationTypes.includes(m),
  );
  const gi = rows.findIndex((r) => r.dimension === "gi_bleeding");
  const ac = rows.findIndex((r) => r.dimension === "anticoagulant_bleeding");
  if (thinned && gi >= 0 && ac >= 0) rows.splice(rows[gi].ear > rows[ac].ear ? ac : gi, 1);

  const gaps: string[] = [];
  for (const dimension of noBaseline) {
    if (rows.some((r) => r.dimension === dimension)) continue;
    // Rules 6 and 12.
    gaps.push(`${OUTCOMES[dimension]} (no published baseline rate for this profile)`);
  }
  for (const unii of uniis) {
    for (const gap of evidence.ingredients[unii].insufficient) {
      if (!gapApplies(gap, profile) || filled.has(gap.dimension)) continue;
      const scoped = [...gap.personas, ...gap.conditions, ...gap.medication_types];
      const isCovered = rows.some(
        (r) => r.dimension === gap.dimension && r.study?.used.some((u) => u.unii === unii),
      );
      // Rule 28: say when the general estimate still covers this profile.
      gaps.push(
        isCovered && scoped.length > 0
          ? `${OUTCOMES[gap.dimension]} with ${name(unii)} specific to ${scoped.map(words).join(" and ")} (the general estimate is used)`
          : `${OUTCOMES[gap.dimension]} with ${name(unii)}`,
      );
    }
  }

  const excess = rows.reduce((sum, r) => sum + r.ear, 0);
  // Rules 41 and 45: rows share the computed score's points; a hard stop holds the score at 49
  // and the difference is its own row.
  const computed = Math.round(scaleScore(excess));
  const stopped = v0.hard_stops_triggered.length > 0;
  const total = stopped ? Math.min(computed, 49) : computed;
  const points = apportion(
    100 - computed,
    rows.map((r) => r.ear),
  );

  const signalFor = (unii: string, dimension: string) => {
    const signals = evidence.ingredients[unii].faers.filter((s) => s.dimension === dimension);
    return signals.find((s) => s.age_band === band) ?? signals.find((s) => s.age_band === "all");
  };

  const contributions: EngineRecord["contributions"] = [];
  const explanation: EngineRecord["explanation"] = [];
  const small: string[] = [];
  rows.forEach((row, i) => {
    let sentence: string;
    const citations: Citation[] = [];
    let ingredientUniis: string[];
    if (row.study) {
      const term = row.study;
      sentence = `${capitalized((term.outcome && OUTCOME_IDS[term.outcome]) || OUTCOMES[term.dimension])}: ${term.used
        .map(({ unii, row: rr }) => {
          const short = rr.citation.section?.split(",")[0] ?? "";
          const measure = MEASURES[rr.measure] ?? rr.measure;
          const grade = GRADES[rr.grade] ?? rr.grade;
          return `${name(unii)} ${rr.estimate} times as likely (${measure}, 95% ${rr.interval === "credible" ? "credible interval" : "CI"} ${rr.ci95[0]} to ${rr.ci95[1]}; ${grade}, ${short})`;
        })
        .join("; ")}. Baseline ${oneIn(term.baseline.annual_incidence)} a year, so one ${
        evidence.course_days
      }-day course adds about ${oneIn(term.ear)}.`;
      for (const { unii, row: rr } of term.used) {
        citations.push(rr.citation);
        const signal = signalFor(unii, term.dimension);
        if (signal) {
          citations.push({
            source: "faers",
            section: `${name(unii)}: ${signal.reports.toLocaleString("en-US")} reports, IC025 ${signal.ic025.toFixed(2)} (${words(signal.event_group)}, ages ${signal.age_band})`,
          });
        }
      }
      citations.push(term.baseline.citation);
      ingredientUniis = term.used.map((u) => u.unii);
    } else {
      // Rule 36.
      const rated = row.rated!;
      const who = capitalized(rated.uniis.map(name).join(" and "));
      const because =
        rated.raisedBy.length > 0 ? `, higher because of ${rated.raisedBy.join(" and ")}` : "";
      const meaning =
        pairs.length === 0
          ? "This rating is not yet calibrated."
          : row.ear > 0
            ? `Where studies measured risks rated ${rated.severity}, one course added about ${oneIn(row.ear)} on average.`
            : `Where studies measured risks rated ${rated.severity}, they found no added risk on average.`;
      const quote = quoteOf(rated.citations);
      sentence = `${capitalized(DIMENSION_NAMES[row.dimension] ?? words(row.dimension))}: ${who} ${
        rated.uniis.length > 1 ? "are" : "is"
      } rated ${rated.severity} of 3 for this profile${because}; no study passed the evidence rules for it. ${meaning}${
        quote ? ` Source: "${quote}"` : ""
      }`;
      citations.push(...rated.citations);
      ingredientUniis = rated.uniis;
    }
    if (points[i] === 0) {
      // Too small to take a whole point, but it still counts toward the score.
      small.push(sentence);
      return;
    }
    contributions.push({
      dimension: row.dimension,
      points: points[i],
      ingredient_uniis: ingredientUniis,
      citations,
    });
    explanation.push({ template_id: `engine_v1_${row.dimension}`, text: sentence });
  });
  if (stopped && computed > total) {
    const citations: Citation[] = stopRatings.flatMap(([, e]) => e.citations);
    const stopQuote = quoteOf(citations);
    contributions.push({
      dimension: "pediatric",
      points: computed - total,
      ingredient_uniis: stopRatings.map(([unii]) => unii),
      citations,
    });
    explanation.push({
      template_id: "engine_v1_hard_stop_pediatric",
      text: `Hard stop: ${v0.hard_stops_triggered.map((h) => h.message).join(" ")} A product the label rules out for this profile is held at 49, in the red band.${stopQuote ? ` Source: "${stopQuote}"` : ""}`,
    });
  } else {
    for (const [unii, entry] of stopRatings) {
      notes.push({
        template_id: "engine_v1_note_pediatric",
        text: `${DIMENSION_NAMES.pediatric}: ${capitalized(name(unii))} is rated 3 of 3 for this age. This is the hard stop.${noteQuote(entry.citations)}`,
      });
    }
  }
  contributions.sort((a, b) => b.points - a.points || (a.dimension < b.dimension ? -1 : 1));

  explanation.push(...notes);
  if (small.length > 0) {
    explanation.push({
      template_id: "engine_v1_under_one_point",
      text: `Under one point each: ${small.join(" ")}`,
    });
  }
  if (gaps.length > 0) {
    explanation.push({
      template_id: "engine_v1_insufficient",
      text: `Not enough published evidence to rate: ${[...new Set(gaps)].join("; ")}.`,
    });
  }

  return {
    ...v0,
    score: total,
    tier: tier(total, v0.hard_stops_triggered),
    contributions,
    explanation,
  };
}

/**
 * Rule 32's last clause: every modifier that raised the ingredient's v0 severity is the condition
 * or co-medication of the row the study used for it.
 */
function entryMatchesStudy(
  raisers: Modifier[],
  unii: string,
  dimension: string,
  studies: Term[],
  evidence: Evidence,
  profile: Profile,
): boolean {
  if (raisers.length === 0) return true;
  const rows = evidence.ingredients[unii].relative_risks.filter((r) => r.dimension === dimension);
  const row =
    studies.find((t) => t.dimension === dimension)?.used.find((u) => u.unii === unii)?.row ??
    pick(rows, profile.persona, profile, (r) => r.estimate);
  if (!row) return false;
  return raisers.every(
    (m) =>
      (m.condition !== undefined && row.condition === m.condition) ||
      (m.medication_type !== undefined && row.medication_type === m.medication_type),
  );
}
