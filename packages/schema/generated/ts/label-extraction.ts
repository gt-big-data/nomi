// Generated from packages/schema/schemas by scripts/codegen-ts.mjs. Do not edit.

/**
 * Exact text copied from the label that supports a fact.
 *
 * This interface was referenced by `LabelExtraction`'s JSON-Schema
 * via the `definition` "evidence".
 */
export type Evidence = string;

/**
 * Structured facts an LLM pulled from one OTC Drug Facts label (NOMI-032). Every fact quotes the label text it came from, so it can be checked against the rule extractor (NOMI-031) and shown as evidence.
 */
export interface LabelExtraction {
  /**
   * DailyMed SPL set id of the label.
   */
  set_id: string;
  /**
   * Exact model id that produced the facts, e.g. 'claude-haiku-4-5'.
   */
  model_id: string;
  /**
   * SHA-256 of the system prompt and output schema sent to the model, so results from different prompts are never mixed.
   */
  prompt_hash: string;
  /**
   * When the extraction ran (ISO 8601).
   */
  extracted_at: string;
  facts: LabelFacts;
}
/**
 * The nine extracted fields. An empty list means the label has nothing for that field.
 *
 * This interface was referenced by `LabelExtraction`'s JSON-Schema
 * via the `definition` "label_facts".
 */
export interface LabelFacts {
  active_ingredients: LabelActiveIngredient[];
  uses: QuotedStatement[];
  mandated_warnings: MandatedWarning[];
  do_not_use: QuotedStatement[];
  /**
   * Conditions that mean asking a doctor before use.
   */
  ask_doctor: QuotedStatement[];
  /**
   * Medicines that mean asking a doctor or pharmacist before use.
   */
  drug_interactions: QuotedStatement[];
  age_limits: LabelAgeLimit[];
  max_daily_doses: LabelMaxDailyDose[];
  allergens: QuotedStatement[];
}
/**
 * This interface was referenced by `LabelExtraction`'s JSON-Schema
 * via the `definition` "active_ingredient".
 */
export interface LabelActiveIngredient {
  name: string;
  /**
   * Strength per unit as printed, e.g. '325 mg'. Null if the label doesn't state one.
   */
  strength: string | null;
  evidence: Evidence;
}
/**
 * One condition, situation or medicine the label names, in plain words, with its quote.
 *
 * This interface was referenced by `LabelExtraction`'s JSON-Schema
 * via the `definition` "quoted".
 */
export interface QuotedStatement {
  text: string;
  evidence: Evidence;
}
/**
 * This interface was referenced by `LabelExtraction`'s JSON-Schema
 * via the `definition` "mandated_warning".
 */
export interface MandatedWarning {
  /**
   * Warning id from pipeline/knowledge/mandated_warnings.yaml and the rule extractor.
   */
  warning_id: string;
  evidence: Evidence;
}
/**
 * This interface was referenced by `LabelExtraction`'s JSON-Schema
 * via the `definition` "age_limit".
 */
export interface LabelAgeLimit {
  action: "do_not_use" | "ask_doctor";
  min_years: number | null;
  under_years: number;
  evidence: Evidence;
}
/**
 * This interface was referenced by `LabelExtraction`'s JSON-Schema
 * via the `definition` "max_daily_dose".
 */
export interface LabelMaxDailyDose {
  amount: number;
  unit: string;
  evidence: Evidence;
}
