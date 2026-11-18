/**
 * Score records (packages/schema score-record) and how the result screen reads them: the risk rows,
 * the notes no row shows, and the tier. The v0 engine (src/scoring/engine.ts) produces these
 * records; the hand-computed ones in packages/schema/examples/<product>/expected-scores.json are
 * its golden checks.
 */

import { productTier, type ProductTier, type SchemaTier } from "../theme/tiers.ts";

/** The fields of a score-record (packages/schema) that the result screen shows. */
export interface ScoreRecord {
  ndc11: string;
  profile: { persona: string; conditions: string[]; medication_types: string[] };
  score: number;
  tier: SchemaTier;
  contributions: {
    dimension: string;
    points: number;
    citations: Citation[];
  }[];
  hard_stops_triggered: { id: string; message: string }[];
  explanation: { template_id: string; text: string }[];
}

export interface Citation {
  /** checkRecords rejects any other value, so every citation has a chip. */
  source: (typeof CITATION_SOURCES)[number];
  section?: string;
  url?: string;
}

/** One risk on the result screen, largest first. */
export interface RiskRow {
  dimension: string;
  /** What the app calls the risk, e.g. "Stomach bleeding". */
  name: string;
  /** The record's sentence on why. */
  detail: string;
  points: number;
  /** One chip per source document: sections of the same label or guideline share a chip. */
  citations: Citation[];
}

/** What the app calls each risk dimension (packages/schema common.schema.json). */
export const DIMENSION_NAMES: Record<string, string> = {
  liver: "Liver",
  gi_bleeding: "Stomach bleeding",
  cardiovascular_bp: "Heart and blood pressure",
  kidney: "Kidneys",
  anticholinergic_cognitive: "Memory and thinking",
  sedation_falls: "Drowsiness and falls",
  serotonergic_interactions: "Serotonin interactions",
  anticoagulant_bleeding: "Bleeding with blood thinners",
  pediatric: "Use in children",
  rebound_overuse: "Overuse",
  pregnancy_lactation: "Pregnancy and breastfeeding",
  duplicate_dosing: "Double dosing",
  excipients: "Inactive ingredients",
  local_skin: "Skin",
  efficacy_evidence: "Evidence it works",
};

const TIERS: readonly string[] = ["green", "yellow", "red"];

/** The line every draft record carries to say it is a draft. The screen says so in its own words. */
const DRAFT_LINE = /_fixture_draft$/;
/** What the label's directions say for the profile's age. */
const CHILD_DIRECTIONS_LINE = /_child_directions$/;
/** A hard stop because the label forbids this age ("hs_zzzquil_under_12"). */
const AGE_STOP = /^hs_(?!rated_).*_under_\d+$/;

/** The dimension an explanation line is about, from its template id ("NOMI-015_gi_bleeding"). */
function lineDimension(templateId: string): string | undefined {
  return Object.keys(DIMENSION_NAMES).find((dimension) => templateId.endsWith(`_${dimension}`));
}

/** citation.source values (packages/schema common.schema.json). The app has a chip for each. */
export const CITATION_SOURCES = [
  "fda_label",
  "otc_monograph",
  "stopp_start",
  "acb",
  "faers",
  "publication",
  "pharmacist_review",
] as const;

const isStrings = (value: unknown) =>
  Array.isArray(value) && value.every((item) => typeof item === "string");

function checkCitations(citations: unknown, where: string): void {
  if (!Array.isArray(citations)) throw new Error(`${where}: citations missing`);
  for (const citation of citations as Citation[]) {
    if (!(CITATION_SOURCES as readonly string[]).includes(citation?.source)) {
      throw new Error(`${where}: unknown citation source ${citation?.source}`);
    }
  }
}

/**
 * Throws unless every record has every field the result screen reads, with values it can show.
 * Also requires a sentence for each risk that took points off, so no row shows without a reason.
 */
export function checkRecords(records: unknown[]): ScoreRecord[] {
  for (const record of records as ScoreRecord[]) {
    const where = `score record ${record?.ndc11} ${record?.profile?.persona}`;
    if (typeof record?.ndc11 !== "string") throw new Error(`${where}: no ndc11`);
    if (
      typeof record.profile?.persona !== "string" ||
      !isStrings(record.profile.conditions) ||
      !isStrings(record.profile.medication_types)
    ) {
      throw new Error(`${where}: incomplete profile`);
    }
    if (!TIERS.includes(record.tier)) throw new Error(`${where}: unknown tier ${record.tier}`);
    if (!Number.isFinite(record.score)) throw new Error(`${where}: no score`);
    if (!Array.isArray(record.hard_stops_triggered)) throw new Error(`${where}: no hard stops`);
    const stopIds = new Set<string>();
    for (const stop of record.hard_stops_triggered) {
      if (typeof stop?.id !== "string" || typeof stop.message !== "string" || !stop.message) {
        throw new Error(`${where}: hard stop without id or message`);
      }
      if (stopIds.has(stop.id)) throw new Error(`${where}: hard stop ${stop.id} twice`);
      stopIds.add(stop.id);
    }
    if (!Array.isArray(record.contributions) || !Array.isArray(record.explanation)) {
      throw new Error(`${where}: missing contributions or explanation`);
    }
    for (const line of record.explanation) {
      if (typeof line?.template_id !== "string" || typeof line.text !== "string") {
        throw new Error(`${where}: explanation line without template_id or text`);
      }
    }
    for (const contribution of record.contributions) {
      const at = `${where} ${contribution?.dimension}`;
      if (!Number.isFinite(contribution?.points)) throw new Error(`${at}: no points`);
      if (!(contribution.dimension in DIMENSION_NAMES)) throw new Error(`${at}: unknown dimension`);
      checkCitations(contribution.citations, at);
      const explained = record.explanation.some(
        (line) => lineDimension(line.template_id) === contribution.dimension,
      );
      if (contribution.points > 0 && !explained) throw new Error(`${at}: no explanation line`);
    }
  }
  return records as ScoreRecord[];
}

function sameSet(a: readonly string[], b: readonly string[]): boolean {
  const sorted = (list: readonly string[]) => [...list].sort().join("\n");
  return a.length === b.length && sorted(a) === sorted(b);
}

/** The tier the screen shows: a hard stop beats the record's own tier. */
export function recordTier(record: ScoreRecord): ProductTier {
  return productTier({ tier: record.tier, hardStop: record.hard_stops_triggered.length > 0 });
}

/**
 * The record for this product and profile, or undefined. Matches the whole profile (persona,
 * conditions and medicines), never just the persona, so a record is only shown for the exact
 * profile it was worked out for.
 */
export function findScore(
  records: readonly ScoreRecord[],
  ndc11: string,
  profile: { persona: string; conditions: readonly string[]; medication_types: readonly string[] },
): ScoreRecord | undefined {
  return records.find(
    (record) =>
      record.ndc11 === ndc11 &&
      record.profile.persona === profile.persona &&
      sameSet(record.profile.conditions, profile.conditions) &&
      sameSet(record.profile.medication_types, profile.medication_types),
  );
}

function uniqueCitations(citations: Citation[]): Citation[] {
  const seen = new Set<string>();
  return citations.filter((citation) => {
    const key = `${citation.source}\n${citation.url ?? citation.section ?? ""}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/** The explanation line each risk row shows: the first one about that risk. */
function rowLine(record: ScoreRecord, dimension: string) {
  return record.explanation.find((e) => lineDimension(e.template_id) === dimension);
}

/** The record's contributions as rows, largest first, each with its own explanation line. */
export function riskRows(record: ScoreRecord): RiskRow[] {
  return record.contributions
    .filter((contribution) => contribution.points > 0)
    .map((contribution) => ({
      dimension: contribution.dimension,
      name: DIMENSION_NAMES[contribution.dimension],
      // checkRecords guarantees the line exists.
      detail: rowLine(record, contribution.dimension)!.text,
      points: contribution.points,
      citations: uniqueCitations(contribution.citations),
    }))
    .sort((a, b) => b.points - a.points);
}

/**
 * Every explanation line no risk row shows, except the draft note: what the label's directions
 * say for this age ("Children younger than 12 must not use this ZzzQuil presentation"), and any
 * line about a risk that took no points. The screen shows these as banners, so no line is lost.
 */
export function profileNotes(record: ScoreRecord): string[] {
  const shown = new Set(riskRows(record).map((row) => rowLine(record, row.dimension)));
  // An age hard stop's banner already says the label forbids this age, more strongly. Any other
  // hard stop leaves the age directions to say.
  const stopped = record.hard_stops_triggered.some((stop) => AGE_STOP.test(stop.id));
  return record.explanation
    .filter(
      (e) =>
        !DRAFT_LINE.test(e.template_id) &&
        !shown.has(e) &&
        !(stopped && CHILD_DIRECTIONS_LINE.test(e.template_id)),
    )
    .map((e) => e.text);
}
