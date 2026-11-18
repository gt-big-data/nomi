import { useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";

import { borderWidth, riskSeverity, riskSeverityColors, useIconScale, useTheme } from "@/theme";

import { Button } from "./Button";
import { CitationChip } from "./CitationChip";
import { Icon } from "./Icon";
import type { RiskCitation } from "./RiskFactorRow";
import { RiskSeverityLabel } from "./RiskSeverityLabel";
import { spokenLabel, Tappable } from "./Tappable";

/** One risk that took points off the score. */
export type RiskItem = {
  /** Stable key, e.g. the contribution's dimension. */
  id: string;
  /** Display name, e.g. "Stomach bleeding". */
  factor: string;
  /** Why, in plain language, shown when the row is opened. */
  detail: string;
  /** Points this risk took off the score. */
  points: number;
  citations: RiskCitation[];
};

/**
 * "Why this score" as one line per risk: the name, the points it took off and a chevron.
 * Tapping a line opens a sheet with the reason and its sources.
 *
 * @example
 * ```tsx
 * <RiskList items={rows} />
 * ```
 */
export function RiskList({ items }: { items: RiskItem[] }) {
  const { colors, radius, space, text } = useTheme();
  const iconScale = useIconScale();
  const [open, setOpen] = useState<RiskItem | null>(null);

  return (
    <>
      <View
        style={[
          styles.card,
          {
            backgroundColor: colors.bg.surface,
            borderColor: colors.border.subtle,
            borderRadius: radius.md,
            paddingHorizontal: space[16],
          },
        ]}
      >
        {items.map((item, index) => {
          const c = riskSeverityColors(colors, riskSeverity(item.points));
          return (
            <Tappable
              key={item.id}
              onPress={() => setOpen(item)}
              accessibilityLabel={spokenLabel([item.factor, `Minus ${item.points} points`])}
              accessibilityHint="Shows why"
              style={[
                styles.row,
                { gap: space[8] },
                index > 0 && {
                  borderTopWidth: StyleSheet.hairlineWidth,
                  borderTopColor: colors.border.subtle,
                },
              ]}
            >
              <Text style={[text("bodyStrong"), styles.factor, { color: colors.text.primary }]}>
                {item.factor}
              </Text>
              <Text style={[text("bodyStrong"), { color: c.text }]}>−{item.points}</Text>
              <Icon name="chevron" size="chevron" scale={iconScale} color={colors.text.secondary} />
            </Tappable>
          );
        })}
      </View>
      <RiskSheet item={open} onClose={() => setOpen(null)} />
    </>
  );
}

function RiskSheet({ item, onClose }: { item: RiskItem | null; onClose: () => void }) {
  const { colors, space, text } = useTheme();
  return (
    <Modal visible={item !== null} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <Pressable
          style={StyleSheet.absoluteFill}
          onPress={onClose}
          accessibilityRole="button"
          accessibilityLabel="Close"
        />
        {item && (
          <View
            style={[
              styles.sheet,
              { backgroundColor: colors.bg.surface, padding: space[24], gap: space[12] },
            ]}
          >
            <View style={[styles.grabber, { backgroundColor: colors.border.subtle }]} />
            <ScrollView contentContainerStyle={{ gap: space[12] }} bounces={false}>
              <Text
                accessibilityRole="header"
                style={[text("titleSmall"), { color: colors.text.primary }]}
              >
                {item.factor}
              </Text>
              <View style={[styles.labelRow, { gap: space[8] }]}>
                <RiskSeverityLabel severity={riskSeverity(item.points)} />
                <Text style={[text("footnote"), { color: colors.text.secondary }]}>
                  −{item.points} pts
                </Text>
              </View>
              <Text style={[text("body"), { color: colors.text.primary }]}>{item.detail}</Text>
              {item.citations.length > 0 && (
                <View style={[styles.chips, { gap: space[8] }]}>
                  {item.citations.map((c, i) => (
                    <CitationChip key={`${c.source}-${i}`} source={c.source} onPress={c.onPress} />
                  ))}
                </View>
              )}
            </ScrollView>
            <Button label="Done" type="secondary" onPress={onClose} />
          </View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  card: { borderWidth: borderWidth.card, alignSelf: "stretch" },
  row: { flexDirection: "row", alignItems: "center", minHeight: 56 },
  factor: { flex: 1, minWidth: 0 },
  backdrop: { flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(23,19,31,0.4)" },
  sheet: {
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    paddingBottom: 40,
    maxHeight: "80%",
  },
  grabber: { alignSelf: "center", width: 40, height: 5, borderRadius: 3 },
  labelRow: { flexDirection: "row", flexWrap: "wrap", alignItems: "center" },
  chips: { flexDirection: "row", flexWrap: "wrap" },
});
