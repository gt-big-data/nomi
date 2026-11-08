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
  moderate: "Use with care",
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
      return c.tier.care;
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
 * Library rule: High is 15 points or more, Moderate 5–14, Low under 5.
 *
 * This is about one risk factor (one score-record.contributions[] item), not the whole product,
 * so it's separate from `uiTier()`: a high-risk product can have a low-severity factor. Low
 * severity is drawn in grey, not low-risk green, because a minor risk isn't a safe one.
 *
 * @param points - Points the risk took off the score (contributions[].points).
 *
 * @example
 * ```ts
 * riskSeverity(38); // "high"
 * riskSeverity(4); // "low"
 * ```
 */
export function riskSeverity(points: number): RiskSeverity {
  if (points >= 15) return "high";
  if (points >= 5) return "moderate";
  return "low";
}
