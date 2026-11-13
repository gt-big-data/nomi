import { productTierColors, productTierText, type ProductTier, useTheme } from "@/theme";

import type { IconName } from "./Icon";
import { Pill } from "./Pill";

/** Each tier has its own icon shape, so tiers can be told apart without color. */
const icons: Record<ProductTier, IconName> = {
  low: "checkCircle",
  moderate: "triangleAlert",
  high: "octagonAlert",
  stop: "stop",
  none: "dash",
};

type TierLabelProps = {
  /** From `productTier()`. */
  tier: ProductTier;
  /**
   * `center` to sit under the score ring. Defaults to `start` (left, as in lists). May go away if
   * the score ring is dropped.
   */
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
  const c = productTierColors(colors, tier);
  return (
    <Pill
      icon={icons[tier]}
      label={productTierText[tier]}
      textStyle="label"
      background={isStop ? colors.tier.stop.fill : c.tint}
      foreground={isStop ? colors.tier.stop.on : c.text}
      align={align}
    />
  );
}
