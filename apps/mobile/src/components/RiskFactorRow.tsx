import { Pressable, StyleSheet, Text, View } from "react-native";

import { type Colors, type RiskSeverity, riskSeverity, useTheme } from "@/theme";

type RiskFactorRowProps = {
  /** The dimension's display name, e.g. "Memory & thinking" (from contributions[].dimension). */
  factor: string;
  /** One short line on why, e.g. "Strong anticholinergic (ACB score 3)". */
  detail: string;
  /** contributions[].points: points this risk took off the score. */
  points: number;
  /** The largest points value on the screen, so bars are drawn relative to it. */
  maxPoints: number;
  /** Open the risk factor detail screen. */
  onPress?: () => void;
};

function severityColors(c: Colors, severity: RiskSeverity) {
  switch (severity) {
    case "high":
      return { text: c.tier.high.text, bar: c.tier.high.mark };
    case "moderate":
      return { text: c.tier.care.text, bar: c.tier.care.mark };
    case "low":
      return { text: c.text.secondary, bar: c.tier.none.mark };
  }
}

/**
 * One item from score-record.contributions[]. Show them largest first.
 *
 * @example
 * ```tsx
 * <RiskFactorRow
 *   factor="Memory & thinking"
 *   detail="Strong anticholinergic (ACB score 3)"
 *   points={38}
 *   maxPoints={38}
 *   onPress={openFactor}
 * />
 * ```
 */
export function RiskFactorRow({ factor, detail, points, maxPoints, onPress }: RiskFactorRowProps) {
  const { colors, radius, space, text } = useTheme();
  const s = severityColors(colors, riskSeverity(points));
  const share = maxPoints > 0 ? Math.min(1, points / maxPoints) : 0;
  const card = [
    styles.card,
    {
      backgroundColor: colors.bg.surface,
      borderColor: colors.border.subtle,
      borderRadius: radius.md,
      gap: space[8],
      padding: space[16],
    },
  ];
  const content = (
    <>
      <View style={[styles.top, { gap: space[8] }]}>
        <Text style={[text("bodyStrong"), styles.factor, { color: colors.text.primary }]}>
          {factor}
        </Text>
        <Text style={[text("calloutStrong"), { color: s.text }]}>−{points} pts</Text>
      </View>
      <Text style={[text("footnote"), { color: colors.text.secondary }]}>{detail}</Text>
      <View style={[styles.track, { backgroundColor: colors.bg.canvas }]}>
        <View style={[styles.fill, { backgroundColor: s.bar, width: `${share * 100}%` }]} />
      </View>
    </>
  );
  const accessibilityLabel = `${factor}, minus ${points} points. ${detail}`;

  if (!onPress) {
    return (
      <View
        accessible
        accessibilityRole="text"
        accessibilityLabel={accessibilityLabel}
        style={card}
      >
        {content}
      </View>
    );
  }
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint="Shows why, and the sources"
      style={({ pressed }) => [...card, pressed && styles.pressed]}
    >
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { borderWidth: 1, alignSelf: "stretch" },
  top: { flexDirection: "row", alignItems: "center" },
  factor: { flex: 1 },
  track: { height: 8, borderRadius: 4, overflow: "hidden" },
  fill: { height: 8, borderRadius: 4, minWidth: 8 },
  pressed: { opacity: 0.85 },
});
