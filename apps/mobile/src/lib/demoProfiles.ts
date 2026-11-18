/**
 * The three profiles the reference scores were worked out for (packages/schema/examples README),
 * and which one the result screen shows. Onboarding (NOMI-028) replaces this with the user's own
 * profile; until then the result screen lets you switch between these three.
 */

import { useSyncExternalStore } from "react";

export interface DemoProfile {
  id: "adult" | "older" | "child";
  /** Short, for the switcher. */
  label: string;
  /** Who it is, in words, under the switcher. */
  description: string;
  persona: string;
  conditions: string[];
  medicationTypes: string[];
}

export const DEMO_PROFILES: readonly DemoProfile[] = [
  {
    id: "adult",
    label: "Adult",
    description: "Adult, 18 to 64, no conditions",
    persona: "adult_18_64",
    conditions: [],
    medicationTypes: [],
  },
  {
    id: "older",
    label: "65+",
    description: "Adult 65 or older with high blood pressure",
    persona: "adult_65_plus",
    conditions: ["hypertension"],
    medicationTypes: [],
  },
  {
    id: "child",
    label: "Child",
    description: "Child, 6 to 11",
    persona: "child_6_11",
    conditions: [],
    medicationTypes: [],
  },
];

// The chosen profile lasts for the app session, so it stays the same from one scan to the next.
let current: DemoProfile = DEMO_PROFILES[0];
const listeners = new Set<() => void>();

export function setDemoProfile(profile: DemoProfile): void {
  current = profile;
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** The profile the result screen scores for. */
export function useDemoProfile(): DemoProfile {
  return useSyncExternalStore(subscribe, () => current);
}
