/**
 * The three profiles the reference scores were worked out for (packages/schema/examples README),
 * and which profile the result screen scores for: the saved one, or one of these three so the
 * presenter can show the score change with who takes it.
 */

import { useSyncExternalStore } from "react";

import type { Profile } from "../storage/profile.ts";

export interface DemoProfile extends Profile {
  id: "adult" | "older" | "child";
  /** Short, for the switcher. */
  label: string;
  /** Who it is, in words, under the switcher. */
  description: string;
}

export const DEMO_PROFILES: readonly DemoProfile[] = [
  {
    id: "adult",
    label: "Adult",
    description: "Adult, 18 to 64, no conditions",
    relation: "self",
    persona: "adult_18_64",
    conditions: [],
    medication_types: [],
  },
  {
    id: "older",
    label: "65+",
    description: "Adult 65 or older with high blood pressure",
    relation: "someone_else",
    persona: "adult_65_plus",
    conditions: ["hypertension"],
    medication_types: [],
  },
  {
    id: "child",
    label: "Child",
    description: "Child, 6 to 11",
    relation: "child",
    persona: "child_6_11",
    conditions: [],
    medication_types: [],
  },
];

/** "saved" for the saved profile, or a demo profile's id. */
export type ScoredFor = "saved" | DemoProfile["id"];

// Lasts for the app session, so it stays the same from one scan to the next.
let current: ScoredFor = "saved";
const listeners = new Set<() => void>();

export function setScoredFor(id: ScoredFor): void {
  current = id;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Which profile the result screen scores for. */
export function useScoredFor(): ScoredFor {
  return useSyncExternalStore(subscribe, () => current);
}
