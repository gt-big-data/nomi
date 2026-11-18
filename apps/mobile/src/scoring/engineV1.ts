/**
 * The v1 on-device score: the published excess risk of serious harm from one course of the
 * product for this profile, on the fixed scale in docs/scoring/v1-method.md. Every number comes
 * from evidence.json (built by pipeline/src/nomi_pipeline/build/app_evidence.py from the cited
 * tables in pipeline/knowledge/evidence/). Nothing here is tuned to a product.
 *
 * Hard stops and the child-label rule are the label's, as in v0, so they come from engine.ts.
 */

import {
  capitalized,
  score as scoreV0,
  tier,
  words,
  type Citation,
  type EngineRecord,
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

  interface Term {
    dimension: string;
    outcome: string | null;
    ear: number;
    used: { unii: string; row: RelativeRisk }[];
    baseline: Pick<Baseline, "annual_incidence" | "citation">;
  }
  const terms: Term[] = [];
  const gaps: string[] = [];
  for (const dimension of Object.keys(OUTCOMES)) {
    const used = uniis.flatMap((unii) => {
      const rows = evidence.ingredients[unii].relative_risks.filter(
        (r) => r.dimension === dimension,
      );
      const row = pick(rows, profile.persona, profile, (r) => r.estimate);
      return row ? [{ unii, row }] : [];
    });
    // Rule 18: one term per outcome; the dimension counts the largest.
    const outcomes = [...new Set(used.map(({ row }) => row.outcome))].sort();
    let best: Term | undefined;
    let missingBaseline = false;
    for (const outcome of outcomes) {
      const same = used.filter(({ row }) => row.outcome === outcome);
      // Rule 4: ingredients without a row are a factor of 1.
      const rr = same.reduce((product, { row }) => product * row.estimate, 1);
      if (rr <= 1) continue;
      const groups = [
        ...new Set(
          same
            .filter(({ row }) => row.comparator === "within_group")
            .map(({ row }) => `${row.condition}|${row.medication_type}`),
        ),
      ];
      if (groups.length > 1) {
        missingBaseline = true;
        continue;
      }
      const group = same.find(({ row }) => row.comparator === "within_group")?.row;
      // Rule 20: a source's own unexposed rate first (the largest relative risk's, if several).
      const adult = ["pregnant", "breastfeeding"].includes(profile.persona)
        ? "adult_18_64"
        : profile.persona;
      const own = same
        .filter(({ row }) => row.unexposed_incidence?.personas.includes(adult))
        .sort((a, b) => b.row.estimate - a.row.estimate)[0]?.row.unexposed_incidence;
      const baseline = own ?? baselineFor(evidence, dimension, outcome, group, profile);
      if (!baseline) {
        missingBaseline = true;
        continue;
      }
      const ear = (baseline.annual_incidence * (rr - 1) * evidence.course_days) / 365;
      if (!best || ear > best.ear) best = { dimension, outcome, ear, used: same, baseline };
    }
    if (best) terms.push(best);
    else if (missingBaseline) {
      // Rules 6 and 12.
      gaps.push(`${OUTCOMES[dimension]} (no published baseline rate for this profile)`);
    }
  }
  // Rule 16: the anticoagulant major-bleeding rate already includes stomach bleeding.
  if (terms.some((t) => t.dimension === "anticoagulant_bleeding")) {
    const gi = terms.findIndex((t) => t.dimension === "gi_bleeding");
    if (gi >= 0) terms.splice(gi, 1);
  }

  for (const unii of uniis) {
    for (const gap of evidence.ingredients[unii].insufficient) {
      if (!gapApplies(gap, profile)) continue;
      const scoped = [...gap.personas, ...gap.conditions, ...gap.medication_types];
      const covered = terms.some(
        (t) => t.dimension === gap.dimension && t.used.some((u) => u.unii === unii),
      );
      // Rule 28: say when the general estimate still covers this profile.
      gaps.push(
        covered && scoped.length > 0
          ? `${OUTCOMES[gap.dimension]} with ${name(unii)} specific to ${scoped.map(words).join(" and ")} (the general estimate is used)`
          : `${OUTCOMES[gap.dimension]} with ${name(unii)}`,
      );
    }
  }

  const excess = terms.reduce((sum, t) => sum + t.ear, 0);
  const total = Math.round(scaleScore(excess));
  const points = apportion(
    100 - total,
    terms.map((t) => t.ear),
  );

  const signalFor = (unii: string, dimension: string) => {
    const signals = evidence.ingredients[unii].faers.filter((s) => s.dimension === dimension);
    return signals.find((s) => s.age_band === band) ?? signals.find((s) => s.age_band === "all");
  };

  const contributions: EngineRecord["contributions"] = [];
  const explanation: EngineRecord["explanation"] = [];
  const small: string[] = [];
  terms.forEach((term, i) => {
    const sentence = `${capitalized((term.outcome && OUTCOME_IDS[term.outcome]) || OUTCOMES[term.dimension])}: ${term.used
      .map(({ unii, row }) => {
        const short = row.citation.section?.split(",")[0] ?? "";
        const measure = MEASURES[row.measure] ?? row.measure;
        const grade = GRADES[row.grade] ?? row.grade;
        return `${name(unii)} ${row.estimate} times as likely (${measure}, 95% ${row.interval === "credible" ? "credible interval" : "CI"} ${row.ci95[0]} to ${row.ci95[1]}; ${grade}, ${short})`;
      })
      .join("; ")}. Baseline ${oneIn(term.baseline.annual_incidence)} a year, so one ${
      evidence.course_days
    }-day course adds about ${oneIn(term.ear)}.`;
    if (points[i] === 0) {
      // Too small to take a whole point, but it still counts toward the score.
      small.push(sentence);
      return;
    }
    const citations: Citation[] = [];
    for (const { unii, row } of term.used) {
      citations.push(row.citation);
      const signal = signalFor(unii, term.dimension);
      if (signal) {
        citations.push({
          source: "faers",
          section: `${name(unii)}: ${signal.reports.toLocaleString("en-US")} reports, IC025 ${signal.ic025.toFixed(2)} (${words(signal.event_group)}, ages ${signal.age_band})`,
        });
      }
    }
    citations.push(term.baseline.citation);
    contributions.push({
      dimension: term.dimension,
      points: points[i],
      ingredient_uniis: term.used.map((u) => u.unii),
      citations,
    });
    explanation.push({ template_id: `engine_v1_${term.dimension}`, text: sentence });
  });
  contributions.sort((a, b) => b.points - a.points || (a.dimension < b.dimension ? -1 : 1));

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
