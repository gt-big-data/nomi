import { useState } from "react";
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import {
  riskSeverity,
  riskSeverityColors,
  riskSeverityText,
  useIconScale,
  useTheme,
} from "@/theme";

import { citationSourceText } from "./CitationChip";
import { Icon } from "./Icon";
import { ListGroup, ListRow } from "./ListGroup";
import type { RiskCitation } from "./RiskFactorRow";
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

/** The record's line is "<rating>. Source: "<quote>"". The sheet shows the two apart. */
function splitDetail(detail: string): { rating: string; quote?: string } {
  const at = detail.indexOf(' Source: "');
  if (at < 0) return { rating: detail };
  return { rating: detail.slice(0, at), quote: detail.slice(at + 9).replace(/^"|"$/g, "") };
}

function sources(item: RiskItem): string {
  return [...new Set(item.citations.map((c) => citationSourceText[c.source]))].join(", ");
}

/**
 * "Why this score" as a grouped list: one row per risk with its severity and sources, and the
 * points it took off. Tapping a row opens a sheet with the reason, the quote and the source.
 *
 * @example
 * ```tsx
 * <RiskList items={rows} />
 * ```
 */
export function RiskList({
  items,
  title = "Why this score",
}: {
  items: RiskItem[];
  /** The section header. */
  title?: string;
}) {
  const { colors, text } = useTheme();
  const [open, setOpen] = useState<RiskItem | null>(null);

  return (
    <>
      <ListGroup title={title}>
        {items.map((item) => {
          const severity = riskSeverity(item.points);
          const c = riskSeverityColors(colors, severity);
          return (
            <ListRow
              key={item.id}
              title={item.factor}
              subtitle={[riskSeverityText[severity], sources(item)].filter(Boolean).join(" · ")}
              trailing={
                <Text style={[text("headline"), styles.points, { color: c.text }]}>
                  −{item.points}
                </Text>
              }
              onPress={() => setOpen(item)}
              accessibilityLabel={spokenLabel([
                item.factor,
                riskSeverityText[severity],
                `minus ${item.points} points`,
              ])}
              accessibilityHint="Shows why, with the source"
            />
          );
        })}
      </ListGroup>
      <RiskSheet item={open} onClose={() => setOpen(null)} />
    </>
  );
}

function RiskSheet({ item, onClose }: { item: RiskItem | null; onClose: () => void }) {
  const { colors, space, text } = useTheme();
  const iconScale = useIconScale();
  const insets = useSafeAreaInsets();
  const severity = item ? riskSeverity(item.points) : "low";
  const c = riskSeverityColors(colors, severity);
  const { rating, quote } = item ? splitDetail(item.detail) : { rating: "", quote: undefined };

  return (
    <Modal visible={item !== null} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <Pressable
          style={StyleSheet.absoluteFill}
          onPress={onClose}
          accessibilityRole="button"
          accessibilityLabel="Close"
        />
        {item && (
          <View
            accessibilityViewIsModal
            style={[
              styles.sheet,
              {
                backgroundColor: colors.bg.surface,
                paddingTop: space[8],
                paddingHorizontal: space[20],
                paddingBottom: insets.bottom + space[24],
              },
            ]}
          >
            <View style={[styles.grabber, { backgroundColor: colors.border.separator }]} />
            <ScrollView contentContainerStyle={{ gap: space[16] }} bounces={false}>
              <View style={[styles.header, { gap: space[12] }]}>
                <View style={[styles.flex, { gap: space[4] }]}>
                  <Text
                    accessibilityRole="header"
                    style={[text("title"), { color: colors.text.primary }]}
                  >
                    {item.factor}
                  </Text>
                  <Text style={[text("subhead"), { color: c.text }]}>
                    <Text style={{ fontFamily: text("headline").fontFamily }}>
                      {riskSeverityText[severity]}
                    </Text>
                    {` · −${item.points} points`}
                  </Text>
                </View>
                <Tappable
                  onPress={onClose}
                  accessibilityLabel="Close"
                  style={[styles.close, { backgroundColor: colors.bg.fill }]}
                >
                  <Icon name="close" size="nav" scale={iconScale} color={colors.text.secondary} />
                </Tappable>
              </View>

              <Text style={[text("bodyLarge"), { color: colors.text.primary }]}>{rating}</Text>

              {quote ? (
                <View
                  style={[
                    styles.quote,
                    { borderLeftColor: colors.border.separator, paddingLeft: space[12] },
                  ]}
                >
                  <Text style={[text("bodyLarge"), { color: colors.text.secondary }]}>
                    “{quote}”
                  </Text>
                </View>
              ) : null}

              {item.citations.length > 0 && (
                <View style={{ gap: space[8] }}>
                  <Text style={[text("footnote"), { color: colors.text.tertiary }]}>
                    {item.citations.length === 1 ? "Source" : "Sources"}
                  </Text>
                  {item.citations.map((citation, index) => (
                    <Tappable
                      key={`${citation.source}-${index}`}
                      onPress={citation.onPress}
                      role="link"
                      accessibilityLabel={spokenLabel([
                        citationSourceText[citation.source],
                        citation.section,
                      ])}
                      accessibilityHint={citation.onPress ? "Opens the source" : undefined}
                      style={[
                        styles.source,
                        { backgroundColor: colors.bg.canvas, padding: space[12], gap: space[12] },
                      ]}
                    >
                      <View style={[styles.flex, { gap: space[2] }]}>
                        <Text style={[text("headline"), { color: colors.text.primary }]}>
                          {citationSourceText[citation.source]}
                        </Text>
                        {citation.section ? (
                          <Text style={[text("footnote"), { color: colors.text.secondary }]}>
                            {citation.section}
                          </Text>
                        ) : null}
                      </View>
                      {citation.onPress && (
                        <Icon
                          name="external"
                          size="nav"
                          scale={iconScale}
                          color={colors.brand.text}
                        />
                      )}
                    </Tappable>
                  ))}
                </View>
              )}
            </ScrollView>
          </View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  points: { fontVariant: ["tabular-nums"] },
  backdrop: { flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(23,19,31,0.32)" },
  sheet: { borderTopLeftRadius: 34, borderTopRightRadius: 34, maxHeight: "75%" },
  grabber: { alignSelf: "center", width: 36, height: 5, borderRadius: 3, marginBottom: 12 },
  header: { flexDirection: "row", alignItems: "flex-start" },
  flex: { flex: 1, minWidth: 0 },
  close: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  quote: { borderLeftWidth: 3 },
  source: { flexDirection: "row", alignItems: "center", borderRadius: 12, minHeight: 52 },
});
