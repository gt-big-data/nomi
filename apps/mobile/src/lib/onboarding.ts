// Plain logic for onboarding, kept out of the screens so it can be tested with node --test.
import {
  type AgeGroup,
  type Condition,
  defaultProfile,
  type MedicationType,
  type Profile,
  type Relation,
} from "../storage/profile.ts";

/** The answer to "Are you pregnant or breastfeeding?". */
export type Pregnancy = "no" | "pregnant" | "breastfeeding" | "undisclosed";

/** The answers so far. Every field starts at the default, so any question can be skipped. */
export type Draft = {
  relation: Relation;
  /** Null until answered, which counts as the default adult 18-64. */
  age: AgeGroup | null;
  pregnancy: Pregnancy;
  conditions: Condition[];
  medicationTypes: MedicationType[];
};

export const startingDraft: Draft = {
  relation: defaultProfile.relation,
  age: null,
  pregnancy: "no",
  conditions: [],
  medicationTypes: [],
};

const childAges: readonly AgeGroup[] = ["under_2", "child_2_5", "child_6_11"];

/**
 * The age picked when the age question opens. Nothing for a child, so a child is never scored
 * as an adult by tapping Next.
 */
export function startingAge(draft: Draft): AgeGroup | null {
  return draft.age ?? (draft.relation === "child" ? null : "adult_18_64");
}

/**
 * Whether to ask "Are you pregnant or breastfeeding?". Not for a child: a parent answering
 * "Breastfeeding" for a nursing baby would hide the baby's own warnings.
 */
export function asksPregnancy(draft: Draft): boolean {
  return draft.relation !== "child" && !(draft.age && childAges.includes(draft.age));
}

/**
 * Turns the answers into a profile. Pregnant or breastfeeding replaces the age group, but only
 * when `asksPregnancy()` is true.
 *
 * @example
 * ```ts
 * toProfile({ ...draft, age: "adult_18_64", pregnancy: "pregnant" }).persona; // "pregnant"
 * ```
 */
export function toProfile(draft: Draft): Profile {
  const pregnancy =
    asksPregnancy(draft) && (draft.pregnancy === "pregnant" || draft.pregnancy === "breastfeeding")
      ? draft.pregnancy
      : null;
  return {
    relation: draft.relation,
    persona: pregnancy ?? draft.age ?? defaultProfile.persona,
    conditions: draft.conditions,
    medication_types: draft.medicationTypes,
  };
}

/** Capitalizes the first letter, for questions that start with `askAbout()`. */
export function capitalize(words: string): string {
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/**
 * Words for asking about the person the profile is for: "you", "they" or "your child".
 *
 * @example
 * ```ts
 * askAbout("child").are; // "is your child"
 * ```
 */
export function askAbout(relation: Relation) {
  switch (relation) {
    case "self":
      return { are: "are you", do: "do you" };
    case "someone_else":
      return { are: "are they", do: "do they" };
    case "child":
      return { are: "is your child", do: "does your child" };
  }
}
