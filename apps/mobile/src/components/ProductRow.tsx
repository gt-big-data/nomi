import { StyleSheet, Text, View } from "react-native";

import {
  borderWidth,
  productTierText,
  type ProductTier,
  useIconScale,
  useTextScale,
  useTheme,
} from "@/theme";

import { Icon } from "./Icon";
import { ScoreBadge } from "./ScoreBadge";
import { spokenLabel, Tappable } from "./Tappable";

type ProductRowProps = {
  /** product.brand_name */
  title: string;
  /** Who it was for and when, or generic name and strength. */
  subtitle?: string;
  /** From `productTier()`. Sets the score dot and what screen readers hear. */
  tier: ProductTier;
  /** score-record.score. Not shown for Stop and None. */
  score?: number;
  /** Open the product's result. The chevron only shows when the row can be tapped. */
  onPress?: () => void;
};

/** From this text size up, the score dot moves above the title so long names don't break mid-word. */
const STACK_AT = 1.5;

/**
 * A product in History, Cabinet, Search and Compare.
 *
 * @example
 * ```tsx
 * <ProductRow
 *   title="Benadryl Allergy"
 *   subtitle="For Mom · 2:14 PM"
 *   tier="high"
 *   score={28}
 *   onPress={openResult}
 * />
 * ```
 */
export function ProductRow({ title, subtitle, tier, score, onPress }: ProductRowProps) {
  const { colors, radius, space, text } = useTheme();
  const iconScale = useIconScale();
  const stacked = useTextScale() >= STACK_AT;

  const scoreText =
    tier === "stop"
      ? "Do not use"
      : tier === "none"
        ? "Not scored"
        : `Score ${score ?? 0}, ${productTierText[tier]}`;
  const label = spokenLabel([title, scoreText, subtitle]);

  const row = [
    styles.row,
    {
      backgroundColor: colors.bg.surface,
      borderColor: colors.border.subtle,
      borderRadius: radius.md,
      gap: space[12],
      paddingHorizontal: space[16],
      paddingVertical: space[12],
    },
  ];
  const badge = <ScoreBadge tier={tier} score={score} size="small" />;
  const chevron = onPress ? (
    <Icon name="chevron" size="chevron" scale={iconScale} color={colors.text.secondary} />
  ) : null;
  const words = (
    <View style={[styles.stack, { gap: space[2] }]}>
      <Text style={[text("bodyStrong"), { color: colors.text.primary }]}>{title}</Text>
      {subtitle ? (
        <Text style={[text("footnote"), { color: colors.text.secondary }]}>{subtitle}</Text>
      ) : null}
    </View>
  );
  // Large text: the dot and chevron share the top line, so the name gets the full width.
  const content = stacked ? (
    <View style={[styles.stack, { gap: space[8] }]}>
      <View style={styles.topLine}>
        {badge}
        {chevron}
      </View>
      {words}
    </View>
  ) : (
    <>
      {badge}
      {words}
      {chevron}
    </>
  );

  return (
    <Tappable onPress={onPress} accessibilityLabel={label} style={row}>
      {content}
    </Tappable>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: borderWidth.card,
    alignSelf: "stretch",
  },
  stack: { flex: 1 },
  topLine: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
});
