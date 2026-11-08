import { Pressable, StyleSheet, Text } from "react-native";

import { useTheme } from "@/theme";

type OptionChipProps = {
  /** The answer as shown, e.g. "65+" or "High blood pressure". */
  label: string;
  /** Whether it's picked. The chip doesn't remember this itself: keep it in state. */
  selected: boolean;
  /** Runs when tapped. Update `selected` here. */
  onPress: () => void;
  /** Defaults to `multi`. How each mode behaves is described on `OptionChip`. */
  mode?: "single" | "multi";
};

/**
 * An answer in onboarding (persona, conditions[], medication_types[]) or a filter. A picked chip
 * is filled in brand purple.
 *
 * The chip only shows whether it's picked. Your screen keeps track of the answers and decides
 * what a tap does:
 * - `mode="single"`: one answer from a group, like age group. Screen readers call it a radio
 *   button. In `onPress`, replace the answer, so picking one chip unpicks the others. Tapping the
 *   picked chip again leaves it picked. Wrap the group in a View with
 *   `accessibilityRole="radiogroup"` and an `accessibilityLabel`, so screen readers know which
 *   chips belong together.
 * - `mode="multi"` (default): any number of answers, like conditions. Screen readers call it a
 *   checkbox. In `onPress`, add the answer if it isn't picked, or remove it if it is.
 *
 * @example
 * ```tsx
 * // Single: one age group
 * const [age, setAge] = useState("65+");
 * <View accessibilityRole="radiogroup" accessibilityLabel="Age group">
 *   {["18–64", "65+"].map((a) => (
 *     <OptionChip key={a} mode="single" label={a} selected={age === a} onPress={() => setAge(a)} />
 *   ))}
 * </View>
 *
 * // Multi: any number of conditions
 * const [conditions, setConditions] = useState<string[]>([]);
 * const toggle = (c: string) =>
 *   setConditions((list) => (list.includes(c) ? list.filter((x) => x !== c) : [...list, c]));
 * <OptionChip
 *   label="Glaucoma"
 *   selected={conditions.includes("Glaucoma")}
 *   onPress={() => toggle("Glaucoma")}
 * />
 * ```
 */
export function OptionChip({ label, selected, onPress, mode = "multi" }: OptionChipProps) {
  const { colors, radius, space, text } = useTheme();
  const background = selected ? colors.brand.primary : colors.bg.surface;
  const border = selected ? colors.brand.primary : colors.border.subtle;
  const foreground = selected ? colors.brand.onPrimary : colors.text.primary;

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole={mode === "single" ? "radio" : "checkbox"}
      accessibilityState={{ checked: selected }}
      accessibilityLabel={label}
      style={({ pressed }) => [
        styles.chip,
        {
          backgroundColor: background,
          borderColor: border,
          // 20 = a full pill at the normal 40pt height, and a rounded box if large text wraps.
          borderRadius: radius.lg,
          paddingHorizontal: space[16],
          paddingVertical: space[8],
        },
        pressed && styles.pressed,
      ]}
    >
      <Text style={[text("calloutStrong"), { color: foreground }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  // Same 1.5 border on and off, so the chip doesn't change size when it's tapped.
  chip: {
    borderWidth: 1.5,
    alignSelf: "flex-start",
    maxWidth: "100%",
    minHeight: 40,
    justifyContent: "center",
  },
  pressed: { opacity: 0.8 },
});
