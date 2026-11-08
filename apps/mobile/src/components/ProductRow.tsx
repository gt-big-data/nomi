import { Pressable, StyleSheet, Text, View } from "react-native";

import { tierText, type UiTier, useIconScale, useTheme } from "@/theme";

import { Icon } from "./Icon";
import { ScoreBadge } from "./ScoreBadge";

type ProductRowProps = {
  /** product.brand_name */
  title: string;
  /** Who it was for and when, or generic name and strength. */
  subtitle?: string;
  /** From `uiTier()`. Sets the score dot and what screen readers hear. */
  tier: UiTier;
  /** score-record.score. Not shown for Stop and None. */
  score?: number;
  /** Open the product's result. The chevron only shows when the row can be tapped. */
  onPress?: () => void;
};

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
  const k = useIconScale();

  const scoreText =
    tier === "stop"
      ? "Do not use"
      : tier === "none"
        ? "Not scored"
        : `Score ${score ?? 0}, ${tierText[tier]}`;
  const label = [title, scoreText, subtitle].filter(Boolean).join(". ");

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
  const content = (
    <>
      <ScoreBadge tier={tier} score={score} size="small" />
      <View style={[styles.stack, { gap: space[2] }]}>
        <Text style={[text("bodyStrong"), { color: colors.text.primary }]}>{title}</Text>
        {subtitle ? (
          <Text style={[text("footnote"), { color: colors.text.secondary }]}>{subtitle}</Text>
        ) : null}
      </View>
      {onPress && (
        <Icon name="chevron" size={18 * k} color={colors.text.secondary} strokeWidth={1.5 * k} />
      )}
    </>
  );

  if (!onPress) {
    return (
      <View accessible accessibilityRole="text" accessibilityLabel={label} style={row}>
        {content}
      </View>
    );
  }
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={label}
      style={({ pressed }) => [...row, pressed && styles.pressed]}
    >
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", borderWidth: 1, alignSelf: "stretch" },
  stack: { flex: 1 },
  pressed: { opacity: 0.85 },
});
