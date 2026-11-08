import { StyleSheet, Text, View } from "react-native";

import { tierColors, tierText, type UiTier, useIconScale, useTheme } from "@/theme";

import { Icon, type IconName } from "./Icon";

/** Each tier has its own icon shape, so tiers can be told apart without color. */
const icons: Record<UiTier, IconName> = {
  low: "checkCircle",
  moderate: "alert",
  high: "octagon",
  stop: "stop",
  none: "dash",
};

type TierLabelProps = {
  /** From `uiTier()`. */
  tier: UiTier;
};

/**
 * The tier word in a pill: Low risk, Use with care, High risk, Do not use, Not scored.
 *
 * @example
 * ```tsx
 * <TierLabel tier="moderate" /> // shows "Use with care"
 * ```
 */
export function TierLabel({ tier }: TierLabelProps) {
  const { colors, radius, space, text } = useTheme();
  const k = useIconScale();
  const isStop = tier === "stop";
  const c = tierColors(colors, tier);
  const background = isStop ? colors.tier.stop.fill : c.tint;
  const foreground = isStop ? colors.tier.stop.on : c.text;

  return (
    <View
      accessible
      accessibilityRole="text"
      accessibilityLabel={tierText[tier]}
      style={[
        styles.pill,
        {
          backgroundColor: background,
          borderRadius: radius.pill,
          gap: space[4],
          paddingVertical: space[4],
          paddingLeft: space[8],
          paddingRight: space[12],
        },
      ]}
    >
      <Icon name={icons[tier]} size={14 * k} color={foreground} strokeWidth={1.4 * k} />
      <Text style={[text("label"), styles.shrink, { color: foreground }]}>{tierText[tier]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: { flexDirection: "row", alignItems: "center", alignSelf: "flex-start", maxWidth: "100%" },
  shrink: { flexShrink: 1 },
});
