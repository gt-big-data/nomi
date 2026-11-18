/**
 * Same values as `Persona` in @nomi/schema.
 */
export type Persona =
  | "adult_18_64"
  | "adult_65_plus"
  | "teen_12_17"
  | "child_6_11"
  | "child_2_5"
  | "under_2"
  | "pregnant"
  | "breastfeeding";

/** Same values as `Condition` in @nomi/schema (docs/scoring/dimensions.md). */
export type Condition =
  | "hypertension"
  | "heart_disease"
  | "kidney_disease"
  | "liver_disease"
  | "stomach_ulcer_or_bleeding"
  | "glaucoma"
  | "enlarged_prostate"
  | "asthma"
  | "diabetes"
  | "thyroid_disease"
  | "phenylketonuria"
  | "heavy_alcohol_use";

/** Same values as `MedicationType` in @nomi/schema (docs/scoring/dimensions.md). */
export type MedicationType =
  | "anticoagulants"
  | "antiplatelets"
  | "maoi"
  | "ssri_snri"
  | "sedatives"
  | "diuretics"
  | "blood_pressure_medications"
  | "corticosteroids";

/** Who the profile is for, from the first onboarding question. */
export type Relation = "self" | "someone_else" | "child";

/** The personas that are ages, without pregnant and breastfeeding (which replace an age). */
export type AgeGroup = Exclude<Persona, "pregnant" | "breastfeeding">;

/**
 * Who Nomi scores for. `persona`, `conditions` and `medication_types` match `Profile` in
 * @nomi/schema; `toScoringProfile()` drops the rest for the scoring engine. Never leaves the phone.
 */
export type Profile = {
  relation: Relation;
  persona: Persona;
  conditions: Condition[];
  medication_types: MedicationType[];
};

/** The fields the scoring engine takes, as `Profile` in @nomi/schema allows no others. */
export function toScoringProfile({ relation: _relation, ...scoring }: Profile) {
  return scoring;
}

/** Used when someone skips onboarding: an adult 18–64 with no conditions or medicines. */
export const defaultProfile: Profile = {
  relation: "self",
  persona: "adult_18_64",
  conditions: [],
  medication_types: [],
};

/** Who the profile is for, as the answers read. */
export const relationText: Record<Relation, string> = {
  self: "Myself",
  someone_else: "A parent or someone else",
  child: "My child",
};

/** Each persona in a few words, e.g. on the done screen. */
export const personaText: Record<Persona, string> = {
  under_2: "Under 2",
  child_2_5: "Child 2–5",
  child_6_11: "Child 6–11",
  teen_12_17: "Teen 12–17",
  adult_18_64: "Adult 18–64",
  adult_65_plus: "Adult 65+",
  pregnant: "Pregnant",
  breastfeeding: "Breastfeeding",
};

/** Age groups in the order they're shown, with the words on each chip. */
export const ageGroupText: Record<AgeGroup, string> = {
  under_2: "Under 2",
  child_2_5: "2–5",
  child_6_11: "6–11",
  teen_12_17: "12–17",
  adult_18_64: "18–64",
  adult_65_plus: "65+",
};

/** Plain names for each condition, in the order they're shown. */
export const conditionText: Record<Condition, string> = {
  hypertension: "High blood pressure",
  heart_disease: "Heart disease",
  kidney_disease: "Kidney disease",
  liver_disease: "Liver disease",
  stomach_ulcer_or_bleeding: "Stomach ulcer or bleeding",
  glaucoma: "Glaucoma",
  enlarged_prostate: "Enlarged prostate",
  asthma: "Asthma",
  diabetes: "Diabetes",
  thyroid_disease: "Thyroid disease",
  phenylketonuria: "PKU",
  // Less judgy and less ambiguous than "heavy alcohol use".
  heavy_alcohol_use: "3+ drinks a day",
};

/** Plain names for each medicine type, in the order they're shown. */
export const medicationTypeText: Record<MedicationType, string> = {
  anticoagulants: "Blood thinners",
  antiplatelets: "Clopidogrel or daily aspirin",
  maoi: "MAOI antidepressants",
  ssri_snri: "SSRI or SNRI antidepressants",
  sedatives: "Sleep or anxiety medicine",
  diuretics: "Water pills",
  blood_pressure_medications: "Blood pressure medicine",
  corticosteroids: "Steroid pills",
};

/**
 * The profile in plain words, one row per answer, e.g. on the done and profile screens.
 *
 * @example
 * ```ts
 * profileSummary(defaultProfile)[1]; // { label: "Scored as", value: "Adult 18–64" }
 * ```
 */
export function profileSummary(profile: Profile): { label: string; value: string }[] {
  return [
    { label: "For", value: relationText[profile.relation] },
    { label: "Scored as", value: personaText[profile.persona] },
    {
      label: "Health conditions",
      value: profile.conditions.map((c) => conditionText[c]).join(", ") || "None",
    },
    {
      label: "Medicines",
      value: profile.medication_types.map((m) => medicationTypeText[m]).join(", ") || "None",
    },
  ];
}
