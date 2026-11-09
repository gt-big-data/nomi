import { tierColors, tierText, type UiTier, useTheme } from "@/theme";

import type { IconName } from "./Icon";
import { Pill } from "./Pill";

/** Each tier has its own icon shape, so tiers can be told apart without color. */
const icons: Record<UiTier, IconName> = {
  low: "checkCircle",
  moderate: "triangleAlert",
  high: "octagonAlert",
  stop: "stop",
  none: "dash",
};

type TierLabelProps = {
  /** From `uiTier()`. */
  tier: UiTier;
  /** `center` to sit under the score ring. This may be deprecated in the future,
   * depending on whether the score ring/dial is dropped.
   * Defaults to `start` (left, as in lists). */
  align?: "start" | "center";
};

/**
 * The whole product's result in a pill: Low risk, Use with caution, High risk, Do not use, Not
 * scored. For one risk inside a result, use `RiskSeverityLabel`.
 *
 * @example
 * ```tsx
 * <TierLabel tier="moderate" /> // shows "Use with caution"
 *
 * // Under the score ring
 * <ScoreBadge tier={tier} score={record.score} />
 * <TierLabel tier={tier} align="center" />
 * ```
 */
export function TierLabel({ tier, align }: TierLabelProps) {
  const { colors } = useTheme();
  const isStop = tier === "stop";
  const c = tierColors(colors, tier);
  return (
    <Pill
      icon={icons[tier]}
      label={tierText[tier]}
      textStyle="label"
      background={isStop ? colors.tier.stop.fill : c.tint}
      foreground={isStop ? colors.tier.stop.on : c.text}
      align={align}
    />
  );
}
