import { type RiskSeverity, severityColors, severityText, useTheme } from "@/theme";

import type { IconName } from "./Icon";
import { Pill } from "./Pill";

/** Same shapes as the matching tiers, so High always means the octagon. */
const icons: Record<RiskSeverity, IconName> = {
  high: "octagonAlert",
  moderate: "triangleAlert",
  low: "info",
};

type RiskSeverityLabelProps = {
  /** From `riskSeverity()`. */
  severity: RiskSeverity;
};

/**
 * How serious one risk is, in a pill: High, Moderate or Low. Used on risk rows; for the whole
 * product's result, use `TierLabel`.
 *
 * @example
 * ```tsx
 * <RiskSeverityLabel severity={riskSeverity(contribution.points)} />
 * ```
 */
export function RiskSeverityLabel({ severity }: RiskSeverityLabelProps) {
  const { colors } = useTheme();
  const c = severityColors(colors, severity);
  return (
    <Pill
      icon={icons[severity]}
      label={severityText[severity]}
      textStyle="label"
      background={c.tint}
      foreground={c.text}
    />
  );
}
