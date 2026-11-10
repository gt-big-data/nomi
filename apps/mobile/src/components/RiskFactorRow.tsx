import { StyleSheet, Text, View } from "react-native";

import { borderWidth, riskSeverity, riskSeverityText, useTheme } from "@/theme";

import { CitationChip, type CitationSource } from "./CitationChip";
import { spokenLabel, Tappable } from "./Tappable";
import { RiskSeverityLabel } from "./RiskSeverityLabel";

/** One of the contribution's citations[]. Leave out `onPress` when there's nothing to open. */
export type RiskCitation = { source: CitationSource; onPress?: () => void };

type RiskFactorRowProps = {
  /** The dimension's display name, e.g. "Memory & thinking" (from contributions[].dimension). */
  factor: string;
  /** One plain-language sentence on why, e.g. "Can cause confusion and memory problems." */
  detail: string;
  /** contributions[].points: points this risk took off the score. Sets the High/Moderate/Low label. */
  points: number;
  /** contributions[].citations, shown as chips so the source is visible without tapping. */
  citations: RiskCitation[];
  /**
   * Also show "−38 pts", for people who want the numbers. Off by default: the design doc picked
   * the Plain list, where the words come first.
   */
  showPoints?: boolean;
  /** Open the risk factor detail screen. */
  onPress?: () => void;
};

/**
 * One item from score-record.contributions[], as a Plain list row (docs/design/score-visualization.md):
 * a High/Moderate/Low label, one plain-language sentence, and its sources. Show them largest first.
 *
 * @example
 * ```tsx
 * <RiskFactorRow
 *   factor="Memory & thinking"
 *   detail="Can cause confusion and memory problems, especially after 65."
 *   points={38}
 *   citations={[{ source: "acb" }, { source: "fda_label", onPress: openLabel }]}
 *   onPress={openFactor}
 * />
 * ```
 */
export function RiskFactorRow({
  factor,
  detail,
  points,
  citations,
  showPoints = false,
  onPress,
}: RiskFactorRowProps) {
  const { colors, radius, space, text } = useTheme();
  const severity = riskSeverity(points);
  const accessibilityLabel = spokenLabel([
    `${riskSeverityText[severity]} risk: ${factor}`,
    detail,
    showPoints && `Minus ${points} points`,
  ]);

  const body = (
    <>
      {/* Wraps the points under the label when text is large, instead of running off the card. */}
      <View style={[styles.labelRow, { gap: space[8] }]}>
        <RiskSeverityLabel severity={severity} />
        {showPoints && (
          <Text style={[text("footnote"), styles.points, { color: colors.text.secondary }]}>
            −{points} pts
          </Text>
        )}
      </View>
      <Text style={[text("bodyStrong"), styles.title, { color: colors.text.primary }]}>
        {factor}
      </Text>
      <Text style={[text("body"), { color: colors.text.primary }]}>{detail}</Text>
    </>
  );

  return (
    <View
      style={[
        styles.card,
        {
          backgroundColor: colors.bg.surface,
          borderColor: colors.border.subtle,
          borderRadius: radius.md,
          gap: space[12],
          padding: space[16],
        },
      ]}
    >
      <Tappable
        onPress={onPress}
        accessibilityLabel={accessibilityLabel}
        accessibilityHint="Shows more about this risk"
        style={{ gap: space[8] }}
      >
        {body}
      </Tappable>
      {citations.length > 0 && (
        <View style={[styles.chips, { gap: space[8] }]}>
          {citations.map((c, i) => (
            <CitationChip key={`${c.source}-${i}`} source={c.source} onPress={c.onPress} />
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderWidth: borderWidth.card, alignSelf: "stretch" },
  labelRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    justifyContent: "space-between",
  },
  points: { flexShrink: 0 },
  title: { minWidth: 0 },
  chips: { flexDirection: "row", flexWrap: "wrap" },
});
