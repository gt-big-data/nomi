import { Pressable, StyleSheet, Text, View } from "react-native";

import { borderWidth, minHeight, opacity, useIconScale, useTheme } from "@/theme";

/** Radio button size from the design, in points: the ring and the dot inside it. */
const RADIO = { ring: 22, dot: 12 };

type OptionCardProps = {
  /** The answer, e.g. "Myself". */
  label: string;
  /** One short line under the label, e.g. "Scores for your age, health and medicines". */
  description?: string;
  /** Whether it's picked. Keep this in state; only one card in a group should be picked. */
  selected: boolean;
  /** Runs when tapped. Set this card as the answer here. */
  onPress: () => void;
};

/**
 * One answer in a pick-one question, as a full-width card with a radio button. Use it when the
 * answers need a line of explanation or read as sentences; for short answers like age groups,
 * use `OptionChip` with `mode="single"`.
 *
 * Wrap the group in a View with `accessibilityRole="radiogroup"` and an `accessibilityLabel`,
 * so screen readers know which cards belong together.
 *
 * @example
 * ```tsx
 * const [who, setWho] = useState("self");
 * <View accessibilityRole="radiogroup" accessibilityLabel="Who are you scanning for?">
 *   <OptionCard
 *     label="Myself"
 *     description="Scores for your age, health and medicines"
 *     selected={who === "self"}
 *     onPress={() => setWho("self")}
 *   />
 * </View>
 * ```
 */
export function OptionCard({ label, description, selected, onPress }: OptionCardProps) {
  const { colors, radius, space, text } = useTheme();
  const iconScale = useIconScale();
  const accent = selected ? colors.brand.primary : colors.border.subtle;
  const ring = RADIO.ring * iconScale;
  const dot = RADIO.dot * iconScale;

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="radio"
      accessibilityState={{ checked: selected }}
      accessibilityLabel={description ? `${label}. ${description}` : label}
      style={({ pressed }) => [
        styles.card,
        {
          backgroundColor: selected ? colors.brand.tint : colors.bg.surface,
          borderColor: accent,
          borderRadius: radius.md,
          gap: space[12],
          paddingHorizontal: space[16],
          paddingVertical: space[12],
        },
        pressed && styles.pressed,
      ]}
    >
      <View
        style={[
          styles.radio,
          { width: ring, height: ring, borderRadius: ring / 2, borderColor: accent },
        ]}
      >
        {selected && (
          <View
            style={{
              width: dot,
              height: dot,
              borderRadius: dot / 2,
              backgroundColor: colors.brand.primary,
            }}
          />
        )}
      </View>
      <View style={[styles.words, { gap: space[2] }]}>
        <Text style={[text("bodyStrong"), { color: colors.text.primary }]}>{label}</Text>
        {description ? (
          <Text style={[text("footnote"), { color: colors.text.secondary }]}>{description}</Text>
        ) : null}
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  // Same border on and off, so the card doesn't change size when it's tapped.
  card: {
    borderWidth: borderWidth.control,
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "stretch",
    minHeight: minHeight.chip,
  },
  radio: { borderWidth: borderWidth.control, alignItems: "center", justifyContent: "center" },
  words: { flex: 1, minWidth: 0 },
  pressed: { opacity: opacity.pressed },
});
