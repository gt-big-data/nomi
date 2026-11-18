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
  /** Hide it from screen readers when the row it sits in already says the score. */
  decorative?: boolean;
};

const LARGE = 136;
const SMALL = 40;
/** Ring line widths. */
const RING = 12;
const DOT_RING = 4;
/** Numbers sit inside a fixed circle, so they grow with large text only up to these limits. */
const MAX_SCALE = { number: 1.2, dot: 1.15 };

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
export function ScoreBadge({
  tier,
  score = 0,
  size = "large",
  decorative = false,
}: ScoreBadgeProps) {
  const { colors, text } = useTheme();
  const c = productTierColors(colors, tier);
  const value = Math.round(Math.min(100, Math.max(0, score)));
  const label =
    tier === "stop"
      ? "No score, do not use"
      : tier === "none"
        ? "Not scored"
        : `Score ${value} out of 100`;
  const a11y = decorative
    ? { "aria-hidden": true }
    : { accessible: true, accessibilityRole: "text" as const, accessibilityLabel: label };

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
      <View {...a11y} style={styles.dot}>
        <Arc
          size={SMALL}
          width={DOT_RING}
          fill={isNone ? 0 : value}
          track={colors.bg.fill}
          mark={c.mark}
        />
        <Text
          maxFontSizeMultiplier={MAX_SCALE.dot}
          style={[text("scoreSmall", { maxScale: MAX_SCALE.dot }), { color: c.text }]}
        >
          {isNone ? "—" : value}
        </Text>
      </View>
    );
  }

  // Large: Stop is a solid disc with a stop sign and no number; otherwise a ring that fills to
  // the score, with the number and "of 100" inside. None shows only the track.
  if (tier === "stop") {
    return (
      <View {...a11y} style={[styles.ring, { backgroundColor: colors.tier.stop.fill }]}>
        <Icon name="stop" size="ring" color={colors.tier.stop.on} />
      </View>
    );
  }
  const isNone = tier === "none";
  return (
    <View {...a11y} style={styles.ring}>
      <Arc
        size={LARGE}
        width={RING}
        fill={isNone ? 0 : value}
        track={colors.bg.fill}
        mark={c.mark}
      />
      <Text
        maxFontSizeMultiplier={MAX_SCALE.number}
        style={[
          text("scoreHero", { maxScale: MAX_SCALE.number }),
          { color: isNone ? colors.text.secondary : colors.text.primary },
        ]}
      >
        {isNone ? "—" : value}
      </Text>
      {!isNone && (
        <Text
          maxFontSizeMultiplier={MAX_SCALE.number}
          style={[text("footnote"), { color: colors.text.tertiary }]}
        >
          of 100
        </Text>
      )}
    </View>
  );
}

/** A track circle with an arc from 12 o'clock, clockwise, to `fill` percent. */
function Arc({
  size,
  width,
  fill,
  track,
  mark,
}: {
  size: number;
  width: number;
  fill: number;
  track: string;
  mark: string;
}) {
  const r = size / 2 - width / 2;
  const circumference = 2 * Math.PI * r;
  return (
    <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
      <Circle cx={size / 2} cy={size / 2} r={r} stroke={track} strokeWidth={width} fill="none" />
      {fill > 0 && (
        <Circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke={mark}
          strokeWidth={width}
          strokeLinecap={fill < 100 ? "round" : "butt"}
          fill="none"
          strokeDasharray={[(circumference * fill) / 100, circumference]}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
      )}
    </Svg>
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
