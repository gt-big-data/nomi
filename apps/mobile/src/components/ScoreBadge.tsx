import { StyleSheet, Text, View } from "react-native";
import Svg, { Circle } from "react-native-svg";

import { productTierColors, type ProductTier, useTheme } from "@/theme";

import { Icon } from "./Icon";

type ScoreBadgeProps = {
  /** From `productTier()`: score-record.tier, plus Stop (hard stop) and None (not scored). */
  tier: ProductTier;
  /** score-record.score, 0–100. Ignored for Stop and None, which never show a number. */
  score?: number;
  /** Large = the ring on the result screen. Small = the dot in lists. */
  size?: "large" | "small";
};

const LARGE = 150;
const SMALL = 44;
/** The ring is 18% of the radius thick. */
const RING = (LARGE / 2) * 0.18;
/** Numbers sit inside a fixed circle, so they grow with large text only up to these limits. */
const MAX_SCALE = { number: 1.2, outOf: 1.5, dot: 1.15 };

/**
 * The 0–100 score. Always pair it with a TierLabel nearby (or say the tier in the row's label),
 * so the tier is never shown by color alone.
 *
 * @example
 * ```tsx
 * const tier = productTier({ tier: record.tier, hardStop: record.hard_stops_triggered.length > 0 });
 * <ScoreBadge tier={tier} score={record.score} />
 * <TierLabel tier={tier} />
 *
 * // The small dot, for lists
 * <ScoreBadge tier="moderate" score={52} size="small" />
 * ```
 */
export function ScoreBadge({ tier, score = 0, size = "large" }: ScoreBadgeProps) {
  const { colors, text } = useTheme();
  const c = productTierColors(colors, tier);
  const value = Math.round(Math.min(100, Math.max(0, score)));
  const label =
    tier === "stop"
      ? "No score, do not use"
      : tier === "none"
        ? "Not scored"
        : `Score ${value} out of 100`;
  const a11y = { accessible: true, accessibilityRole: "text" as const, accessibilityLabel: label };

  if (size === "small") {
    if (tier === "stop") {
      return (
        <View {...a11y} style={[styles.dot, { backgroundColor: c.tint }]}>
          <Icon name="stop" size="dot" color={c.text} />
        </View>
      );
    }
    const isNone = tier === "none";
    return (
      <View
        {...a11y}
        style={[
          styles.dot,
          {
            backgroundColor: colors.bg.surface,
            borderColor: c.mark,
            borderWidth: isNone ? 2 : 3,
          },
        ]}
      >
        <Text
          maxFontSizeMultiplier={MAX_SCALE.dot}
          style={[text("scoreSmall", { maxScale: MAX_SCALE.dot }), { color: c.text }]}
        >
          {isNone ? "—" : value}
        </Text>
      </View>
    );
  }

  if (tier === "stop") {
    return (
      <View {...a11y} style={[styles.ring, { backgroundColor: c.tint }]}>
        <Icon name="stop" size="ring" color={c.text} />
      </View>
    );
  }

  if (tier === "none") {
    return (
      <View
        {...a11y}
        style={[
          styles.ring,
          {
            backgroundColor: colors.bg.surface,
            borderColor: c.mark,
            borderWidth: 4,
          },
        ]}
      >
        <Text
          maxFontSizeMultiplier={MAX_SCALE.number}
          style={[text("scoreLarge", { maxScale: MAX_SCALE.number }), { color: c.text }]}
        >
          —
        </Text>
      </View>
    );
  }

  const r = LARGE / 2 - RING / 2;
  const circumference = 2 * Math.PI * r;
  return (
    <View {...a11y} style={styles.ring}>
      <Svg width={LARGE} height={LARGE} style={StyleSheet.absoluteFill}>
        <Circle
          cx={LARGE / 2}
          cy={LARGE / 2}
          r={r}
          stroke={c.tint}
          strokeWidth={RING}
          fill="none"
        />
        {value > 0 && (
          <Circle
            cx={LARGE / 2}
            cy={LARGE / 2}
            r={r}
            stroke={c.mark}
            strokeWidth={RING}
            fill="none"
            strokeDasharray={[(circumference * value) / 100, circumference]}
            transform={`rotate(-90 ${LARGE / 2} ${LARGE / 2})`}
          />
        )}
      </Svg>
      <Text
        maxFontSizeMultiplier={MAX_SCALE.number}
        style={[text("scoreLarge", { maxScale: MAX_SCALE.number }), { color: c.text }]}
      >
        {value}
      </Text>
      <Text
        maxFontSizeMultiplier={MAX_SCALE.outOf}
        style={[text("caption", { maxScale: MAX_SCALE.outOf }), { color: colors.text.secondary }]}
      >
        /100
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  ring: {
    width: LARGE,
    height: LARGE,
    borderRadius: LARGE / 2,
    alignItems: "center",
    justifyContent: "center",
  },
  dot: {
    width: SMALL,
    height: SMALL,
    borderRadius: SMALL / 2,
    alignItems: "center",
    justifyContent: "center",
  },
});
