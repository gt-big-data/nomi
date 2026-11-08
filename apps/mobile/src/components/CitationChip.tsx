import { Pressable, StyleSheet, Text, View } from "react-native";

import { useIconScale, useTheme } from "@/theme";

import { Icon } from "./Icon";

/** Same values as `CitationSource` in @nomi/schema (citation.source). */
export type CitationSource =
  | "fda_label"
  | "otc_monograph"
  | "stopp_start"
  | "acb"
  | "faers"
  | "publication"
  | "pharmacist_review";

/** UI text conversion from schema citationSource type. */
export const citationSourceText: Record<CitationSource, string> = {
  fda_label: "FDA label",
  otc_monograph: "OTC monograph",
  stopp_start: "STOPP/START",
  acb: "ACB scale",
  faers: "FDA reports",
  publication: "Research",
  pharmacist_review: "Pharmacist",
};

type CitationChipProps = {
  source: CitationSource;
  /** Open the source (citation.url or its quote). Leave out for a chip that only labels. */
  onPress?: () => void;
};

/**
 * Where a value comes from. One chip per citation.
 *
 * @example
 * ```tsx
 * // citation.url is optional, so only make the chip tappable when there is one
 * <CitationChip
 *   source={citation.source}
 *   onPress={citation.url ? () => Linking.openURL(citation.url!) : undefined}
 * />
 * <CitationChip source="acb" />
 * ```
 */
export function CitationChip({ source, onPress }: CitationChipProps) {
  const { colors, radius, space, text } = useTheme();
  const k = useIconScale();
  const displayText = citationSourceText[source];
  const pill = [
    styles.pill,
    {
      backgroundColor: colors.brand.tint,
      borderRadius: radius.pill,
      gap: space[4],
      paddingVertical: space[4],
      paddingLeft: space[8],
      paddingRight: 10,
    },
  ];
  const content = (
    <>
      <Icon name="doc" size={14 * k} color={colors.brand.text} strokeWidth={1.17 * k} />
      <Text style={[text("caption"), styles.shrink, { color: colors.brand.text }]}>
        {displayText}
      </Text>
    </>
  );

  if (!onPress) {
    return (
      <View
        accessible
        accessibilityRole="text"
        accessibilityLabel={`Source: ${displayText}`}
        style={pill}
      >
        {content}
      </View>
    );
  }
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="link"
      accessibilityLabel={`Source: ${displayText}`}
      accessibilityHint="Opens the source"
      hitSlop={10}
      style={({ pressed }) => [...pill, pressed && styles.pressed]}
    >
      {content}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pill: { flexDirection: "row", alignItems: "center", alignSelf: "flex-start", maxWidth: "100%" },
  shrink: { flexShrink: 1 },
  pressed: { opacity: 0.7 },
});
