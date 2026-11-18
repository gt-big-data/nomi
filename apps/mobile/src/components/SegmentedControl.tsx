import { StyleSheet, Text, View } from "react-native";

import { useTheme } from "@/theme";

import { Tappable } from "./Tappable";

/** 44 pt tall, so every segment is easy to tap. */
const HEIGHT = 44;

/**
 * An iOS-style segmented control: a grey track with a white thumb on the selected segment.
 *
 * @example
 * ```tsx
 * <SegmentedControl
 *   label="Who will take it"
 *   options={[{ id: "a", label: "You" }, { id: "b", label: "Child" }]}
 *   selected="a"
 *   onSelect={setId}
 * />
 * ```
 */
export function SegmentedControl<T extends string>({
  label,
  options,
  selected,
  onSelect,
}: {
  /** What screen readers call the group. */
  label: string;
  options: { id: T; label: string }[];
  selected: T;
  onSelect: (id: T) => void;
}) {
  const { colors, text } = useTheme();
  return (
    <View
      accessibilityRole="radiogroup"
      accessibilityLabel={label}
      style={[styles.track, { backgroundColor: colors.bg.fill }]}
    >
      {options.map((option) => {
        const on = option.id === selected;
        return (
          <Tappable
            key={option.id}
            onPress={() => onSelect(option.id)}
            accessibilityLabel={option.label}
            role="radio"
            selected={on}
            style={[
              styles.segment,
              on && [
                styles.thumb,
                { backgroundColor: colors.bg.thumb, shadowColor: colors.text.primary },
              ],
            ]}
          >
            <Text
              numberOfLines={1}
              adjustsFontSizeToFit
              style={[
                text(on ? "bodyStrong" : "subhead"),
                { color: on ? colors.text.primary : colors.text.secondary },
              ]}
            >
              {option.label}
            </Text>
          </Tappable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  track: {
    flexDirection: "row",
    alignSelf: "stretch",
    minHeight: HEIGHT,
    borderRadius: HEIGHT / 2,
    padding: 3,
  },
  segment: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: (HEIGHT - 6) / 2,
    paddingHorizontal: 4,
  },
  thumb: {
    shadowOpacity: 0.1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
});
