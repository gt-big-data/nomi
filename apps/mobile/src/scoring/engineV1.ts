/**
 * The v1 on-device score: the published excess risk of serious harm from one course of the
 * product for this profile, on the fixed scale in docs/scoring/v1-method.md. Every number comes
 * from evidence.json (built by pipeline/src/nomi_pipeline/build/app_evidence.py from the cited
 * tables in pipeline/knowledge/evidence/). Nothing here is tuned to a product.
 *
 * Hard stops and the child-label rule are the label's, as in v0, so they come from engine.ts.
 */

import { score as scoreV0, type Citation, type EngineRecord, type Profile, type Ratings, type ScorableProduct, type ScoreResult } from "./engine.ts";

interface Applies {
  persona: string;
  condition: string | null;
  medication_type: string | null;
}

export interface RelativeRisk extends Applies {
  dimension: string;
  measure: string;
  estimate: number;
  ci95: [number, number];
  grade: string;
  citation: Citation & { citation: string };
}

export interface Baseline extends Applies {
  dimension: string;
  annual_incidence: number;
  as_reported: string;
  citation: Citation & { citation: string };
}

export interface Evidence {
  course_days: number;
  ingredients: Record<
    string,
    {
      name: string;
      relative_risks: RelativeRisk[];
      insufficient: { dimension: string; reason: string; persona?: string; condition?: string; medication_type?: string }[];
      faers: { dimension: string; age_band: string; event_group: string; ic025: number; reports: number }[];
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

/** Rule 5: personas whose baseline age band is another persona's when no row names them. */
const BASELINE_AGE: Record<string, string> = { pregnant: "adult_18_64", breastfeeding: "adult_18_64" };

const words = (id: string) => id.replaceAll("_", " ");
const capitalized = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);

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
function pick<T extends Applies>(rows: T[], persona: string, profile: Profile, value: (row: T) => number): T | undefined {
  const applying = rows.filter((row) => matches(row, persona, profile));
  const pool = applying.some(specific) ? applying.filter(specific) : applying;
  return pool.reduce<T | undefined>((best, row) => (best && value(best) >= value(row) ? best : row), undefined);
}

/** Rule 5: the profile's own persona first, then its age band. */
function baselineFor(evidence: Evidence, dimension: string, profile: Profile): Baseline | undefined {
  const rows = evidence.baselines.filter((row) => row.dimension === dimension);
  const own = pick(rows, profile.persona, profile, (row) => row.annual_incidence);
  if (own || !(profile.persona in BASELINE_AGE)) return own;
  return pick(rows, BASELINE_AGE[profile.persona], profile, (row) => row.annual_incidence);
}

/** "1 in 25,000" */
function oneIn(probability: number): string {
  const n = 1 / probability;
  const rounded = n >= 100 ? Number(n.toPrecision(2)) : Math.round(n);
  return `1 in ${rounded.toLocaleString("en-US")}`;
}

/** Score on the CIOMS-anchored scale (section 3): 1e-5 is 100, 1e-4 is 75, 1e-3 is 50. */
export function scaleScore(excessRisk: number): number {
  if (excessRisk <= 0) return 100;
  return Math.min(100, Math.max(0, 100 - 25 * (Math.log10(excessRisk) + 5)));
}

/** Rule 8: whole points that add up to total, by largest remainder. */
function apportion(total: number, weights: number[]): number[] {
  const sum = weights.reduce((a, b) => a + b, 0);
  if (sum === 0 || total === 0) return weights.map(() => 0);
  const exact = weights.map((w) => (total * w) / sum);
  const out = exact.map(Math.floor);
  const order = exact.map((x, i) => [x - Math.floor(x), i] as const).sort((a, b) => b[0] - a[0] || a[1] - b[1]);
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
  const missing = product.ingredients.filter((i) => !(i.unii in evidence.ingredients)).map((i) => i.name);
  if (product.ingredients.length === 0 || missing.length > 0) return { status: "unrated", missing };

  // Hard stops and the child-label rule come from the label, exactly as in v0.
  const v0 = scoreV0(product, profile, ratings);
  if ("status" in v0) return v0;

  const uniis = [...new Set(product.ingredients.map((i) => i.unii))].sort();
  const name = (unii: string) => evidence.ingredients[unii].name.replaceAll("_", " ");
  const band = AGE_BANDS[profile.persona];

  interface Term {
    dimension: string;
    ear: number;
    used: { unii: string; row: RelativeRisk }[];
    baseline: Baseline;
    rr: number;
  }
  const terms: Term[] = [];
  const gaps: string[] = [];
  for (const dimension of Object.keys(OUTCOMES)) {
    const used = uniis.flatMap((unii) => {
      const rows = evidence.ingredients[unii].relative_risks.filter((r) => r.dimension === dimension);
      const row = pick(rows, profile.persona, profile, (r) => r.estimate);
      return row ? [{ unii, row }] : [];
    });
    // Rule 4: ingredients without a row are a factor of 1.
    const rr = used.reduce((product, { row }) => product * row.estimate, 1);
    if (rr <= 1) continue;
    const baseline = baselineFor(evidence, dimension, profile);
    if (!baseline) {
      // Rule 6.
      gaps.push(`${OUTCOMES[dimension]}: no published baseline rate for this profile`);
      continue;
    }
    const ear = (baseline.annual_incidence * (rr - 1) * evidence.course_days) / 365;
    terms.push({ dimension, ear, used, baseline, rr });
  }

  // Rule 7: insufficient-evidence pairs that apply to this profile.
  for (const unii of uniis) {
    for (const gap of evidence.ingredients[unii].insufficient) {
      if (gap.persona && gap.persona !== profile.persona) continue;
      if (gap.condition && !profile.conditions.includes(gap.condition)) continue;
      if (gap.medication_type && !profile.medicationTypes.includes(gap.medication_type)) continue;
      const who = gap.condition ?? gap.medication_type ?? gap.persona;
      gaps.push(`${OUTCOMES[gap.dimension] ?? words(gap.dimension)} with ${name(unii)}${who ? ` (${words(who)})` : ""}`);
    }
  }

  const excess = terms.reduce((sum, t) => sum + t.ear, 0);
  const total = Math.round(scaleScore(excess));
  const points = apportion(100 - total, terms.map((t) => t.ear));

  const contributions: EngineRecord["contributions"] = [];
  const explanation: EngineRecord["explanation"] = [];
  terms.forEach((term, i) => {
    if (points[i] === 0) return;
    const citations: Citation[] = [];
    for (const { unii, row } of term.used) {
      citations.push(row.citation);
      const signal = evidence.ingredients[unii].faers
        .filter((s) => s.dimension === term.dimension && s.age_band === band)
        .sort((a, b) => b.ic025 - a.ic025)[0];
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
    const factors = term.used
      .map(({ unii, row }) => {
        const short = row.citation.section?.split(",")[0] ?? "";
        return `${name(unii)} ${row.estimate} times as likely (${MEASURES[row.measure] ?? row.measure}, 95% CI ${row.ci95[0]} to ${row.ci95[1]}; ${GRADES[row.grade] ?? row.grade}, ${short})`;
      })
      .join("; ");
    explanation.push({
      template_id: `engine_v1_${term.dimension}`,
      text:
        `${capitalized(OUTCOMES[term.dimension])}: ${factors}. ` +
        `Baseline ${oneIn(term.baseline.annual_incidence)} a year, so one ${evidence.course_days}-day course adds about ${oneIn(term.ear)}.`,
    });
  });
  contributions.sort((a, b) => b.points - a.points || (a.dimension < b.dimension ? -1 : 1));

  if (gaps.length > 0) {
    explanation.push({
      template_id: "engine_v1_insufficient",
      text: `Not enough published evidence to rate: ${[...new Set(gaps)].join("; ")}.`,
    });
  }

  return {
    ...v0,
    score: total,
    tier: v0.hard_stops_triggered.length > 0 ? "red" : total >= 75 ? "green" : total >= 50 ? "yellow" : "red",
    contributions,
    explanation,
  };
}
