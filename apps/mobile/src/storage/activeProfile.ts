import * as SecureStore from "expo-secure-store";
import { useSyncExternalStore } from "react";

import { setScoredFor } from "@/lib/demoProfiles";

import type { Profile } from "./profile";

// In the iOS Keychain / Android Keystore (docs/system-design.md 8.4). Nothing is sent anywhere.
const KEY = "profile";

// undefined until it's read at launch; null when onboarding hasn't been finished or skipped.
let saved: Profile | null | undefined;
const listeners = new Set<() => void>();

function set(profile: Profile | null): void {
  saved = profile;
  for (const listener of listeners) listener();
}

/** Reads the saved profile, once at launch. Never logs the answers. */
export function loadProfile(): Promise<void> {
  return SecureStore.getItemAsync(KEY)
    .then((json) => set(json ? (JSON.parse(json) as Profile) : null))
    .catch(() => {
      console.error("Couldn't read the saved profile.");
      set(null);
    });
}

/** The saved profile, or null before onboarding. */
export function getSavedProfile(): Profile | null | undefined {
  return saved;
}

/** Makes this the active profile, saves it on the phone and scores the next result for it. */
export function saveProfile(profile: Profile): void {
  set(profile);
  setScoredFor("saved");
  SecureStore.setItemAsync(KEY, JSON.stringify(profile)).catch(() =>
    console.error("Couldn't save the profile."),
  );
}

/** The saved profile, kept up to date: undefined while loading, null before onboarding. */
export function useSavedProfile(): Profile | null | undefined {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    getSavedProfile,
    getSavedProfile,
  );
}
