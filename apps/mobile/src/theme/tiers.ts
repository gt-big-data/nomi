import type { Colors } from "./tokens";

/**
 * The five ways a result can look. The schema only has three tiers (score-record.tier:
 * green / yellow / red); the UI adds Stop (a hard stop fired) and None (not scored).
 */
export type UiTier = "low" | "moderate" | "high" | "stop" | "none";

/** Same values as `Tier` in @nomi/schema. Import it from there once apps/mobile depends on it. */
export type SchemaTier = "green" | "yellow" | "red";

/**
 * Turns score-record data into the UI tier.
 *
 * @param input - From the score record:
 *   - `tier`: score-record.tier
 *   - `hardStop`: true when hard_stops_triggered[] isn't empty
 *   - `scored`: false when product.scope isn't in_scope (homeopathic, out of scope)
 *
 * @example
 * ```ts
 * uiTier({ tier: "yellow" }); // "moderate"
 * uiTier({ tier: "yellow", hardStop: true }); // "stop"
 * uiTier({ tier: "green", scored: false }); // "none"
 * ```
 */
export function uiTier(input: { tier?: SchemaTier; hardStop?: boolean; scored?: boolean }): UiTier {
  if (input.scored === false || input.tier === undefined) return "none";
  if (input.hardStop) return "stop";
  if (input.tier === "green") return "low";
  if (input.tier === "yellow") return "moderate";
  return "high";
}

/** The tier word shown in the app. Never show a tier by color alone. */
export const tierText: Record<UiTier, string> = {
  low: "Low risk",
  moderate: "Use with caution",
  high: "High risk",
  stop: "Do not use",
  none: "Not scored",
};

/**
 * Ring, text and tint colors for a tier. Stop uses the high-risk colors except on the Tier label.
 *
 * @param c - The current colors, from `useTheme().colors`.
 * @param tier - From `uiTier()`.
 *
 * @example
 * ```tsx
 * const { colors } = useTheme();
 * const { mark, text, tint } = tierColors(colors, "moderate");
 * ```
 */
export function tierColors(c: Colors, tier: UiTier): { mark: string; text: string; tint: string } {
  switch (tier) {
    case "low":
      return c.tier.low;
    case "moderate":
      return c.tier.moderate;
    case "high":
    case "stop":
      return c.tier.high;
    case "none":
      return c.tier.none;
  }
}

/** How serious one risk factor is. */
export type RiskSeverity = "high" | "moderate" | "low";

/**
 * High is 51 points or more, Moderate 15–50, Low under 15. These match the reference
 * products' severity 3/2/1 (51/15/5 points). Swap to contributions[].severity once the schema has it.
 *
 * This is about one risk factor (one score-record.contributions[] item), not the whole product,
 * so it's separate from `uiTier()`: a high-risk product can have a low-severity factor. Low
 * severity is drawn in grey, not low-risk green, because a minor risk isn't a safe one.
 *
 * @param points - Points the risk took off the score (contributions[].points).
 *
 * @example
 * ```ts
 * riskSeverity(51); // "high"
 * riskSeverity(5); // "low"
 * ```
 */
export function riskSeverity(points: number): RiskSeverity {
  if (points >= 51) return "high";
  if (points >= 15) return "moderate";
  return "low";
}

/** The severity word on a risk row. Never show a severity by color alone. */
export const severityText: Record<RiskSeverity, string> = {
  high: "High",
  moderate: "Moderate",
  low: "Low",
};

/**
 * Text and tint colors for a risk's severity. High and Moderate share the tier colors; Low is
 * grey, not low-risk green, because a minor risk isn't a safe one.
 *
 * @param c - The current colors, from `useTheme().colors`.
 * @param severity - From `riskSeverity()`.
 */
export function severityColors(
  c: Colors,
  severity: RiskSeverity,
): { mark: string; text: string; tint: string } {
  switch (severity) {
    case "high":
      return c.tier.high;
    case "moderate":
      return c.tier.moderate;
    case "low":
      return c.tier.none;
  }
}
