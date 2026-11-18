import { createContext, type ReactNode, useContext, useMemo, useState } from "react";

import { type Draft, startingDraft } from "@/lib/onboarding";

type DraftContext = { draft: Draft; update: (changes: Partial<Draft>) => void };

const Context = createContext<DraftContext | null>(null);

/** Holds the answers while someone moves between the onboarding screens. */
export function DraftProvider({ children }: { children: ReactNode }) {
  const [draft, setDraft] = useState(startingDraft);
  const value = useMemo(
    () => ({ draft, update: (changes: Partial<Draft>) => setDraft((d) => ({ ...d, ...changes })) }),
    [draft],
  );
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

/**
 * The answers so far and a way to change them. Only works inside the onboarding screens.
 *
 * @example
 * ```tsx
 * const { draft, update } = useDraft();
 * const pickOlder = () => update({ age: "adult_65_plus" });
 * ```
 */
export function useDraft(): DraftContext {
  const value = useContext(Context);
  if (!value) throw new Error("useDraft() must be used inside the onboarding screens.");
  return value;
}
