import { useEffect, useRef, useState } from "react";
import {
  AccessibilityInfo,
  Animated,
  Easing,
  Modal,
  PanResponder,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
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

/** How far below its resting place the sheet starts, in points: past the bottom of any phone. */
const OFFSCREEN = 900;
/** Dragging the sheet down this far, or flicking it, closes it. */
const DISMISS_DISTANCE = 120;
const DISMISS_VELOCITY = 0.8;

/**
 * The risk detail as a bottom sheet. The dim backdrop fades in on its own while the sheet springs
 * up from the bottom; closing reverses both. Drag the sheet down, tap the backdrop or tap Close to
 * dismiss. With Reduce Motion on, it fades instead of moving.
 */
function RiskSheet({ item, onClose }: { item: RiskItem | null; onClose: () => void }) {
  const { colors, space, text } = useTheme();
  const iconScale = useIconScale();
  const insets = useSafeAreaInsets();
  // Kept while the sheet animates out, after the parent has already cleared `item`.
  const [shown, setShown] = useState<RiskItem | null>(null);
  const progress = useRef(new Animated.Value(0)).current;
  const drag = useRef(new Animated.Value(0)).current;
  const reduceMotion = useRef(false);
  const closing = useRef(false);

  useEffect(() => {
    AccessibilityInfo.isReduceMotionEnabled().then((on) => (reduceMotion.current = on));
  }, []);

  useEffect(() => {
    if (!item) return;
    closing.current = false;
    setShown(item);
    drag.setValue(0);
    progress.setValue(0);
    const open = reduceMotion.current
      ? Animated.timing(progress, { toValue: 1, duration: 200, useNativeDriver: true })
      : Animated.spring(progress, {
          toValue: 1,
          damping: 30,
          stiffness: 300,
          mass: 1,
          useNativeDriver: true,
        });
    open.start();
  }, [item, drag, progress]);

  const close = () => {
    if (closing.current) return;
    closing.current = true;
    Animated.timing(progress, {
      toValue: 0,
      duration: 220,
      easing: Easing.in(Easing.cubic),
      useNativeDriver: true,
    }).start(() => {
      setShown(null);
      onClose();
    });
  };

  const pan = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => g.dy > 6 && Math.abs(g.dy) > Math.abs(g.dx),
      onPanResponderMove: (_, g) => drag.setValue(Math.max(0, g.dy)),
      onPanResponderRelease: (_, g) => {
        if (g.dy > DISMISS_DISTANCE || g.vy > DISMISS_VELOCITY) closeRef.current();
        else
          Animated.spring(drag, {
            toValue: 0,
            damping: 30,
            stiffness: 300,
            useNativeDriver: true,
          }).start();
      },
    }),
  ).current;
  const closeRef = useRef(close);
  closeRef.current = close;

  const sheetMotion = reduceMotion.current
    ? { opacity: progress }
    : {
        transform: [
          {
            translateY: Animated.add(
              progress.interpolate({ inputRange: [0, 1], outputRange: [OFFSCREEN, 0] }),
              drag,
            ),
          },
        ],
      };

  const severity = shown ? riskSeverity(shown.points) : "low";
  const c = riskSeverityColors(colors, severity);
  const { rating, quote } = shown ? splitDetail(shown.detail) : { rating: "", quote: undefined };
  const item_ = shown;

  return (
    <Modal visible={shown !== null} transparent animationType="none" onRequestClose={close}>
      <View style={styles.backdrop}>
        <Animated.View style={[StyleSheet.absoluteFill, styles.scrim, { opacity: progress }]}>
          <Pressable
            style={StyleSheet.absoluteFill}
            onPress={close}
            accessibilityRole="button"
            accessibilityLabel="Close"
          />
        </Animated.View>
        {item_ && (
          <Animated.View
            accessibilityViewIsModal
            {...pan.panHandlers}
            style={[
              sheetMotion,
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
                    {item_.factor}
                  </Text>
                  <Text style={[text("subhead"), { color: c.text }]}>
                    <Text style={{ fontFamily: text("headline").fontFamily }}>
                      {riskSeverityText[severity]}
                    </Text>
                    {` · −${item_.points} points`}
                  </Text>
                </View>
                <Tappable
                  onPress={close}
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

              {item_.citations.length > 0 && (
                <View style={{ gap: space[8] }}>
                  <Text style={[text("footnote"), { color: colors.text.tertiary }]}>
                    {item_.citations.length === 1 ? "Source" : "Sources"}
                  </Text>
                  {item_.citations.map((citation, index) => (
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
          </Animated.View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  points: { fontVariant: ["tabular-nums"] },
  backdrop: { flex: 1, justifyContent: "flex-end" },
  scrim: { backgroundColor: "rgba(23,19,31,0.32)" },
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
