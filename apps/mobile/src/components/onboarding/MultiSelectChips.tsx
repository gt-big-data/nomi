import { StyleSheet, View } from "react-native";

import { useTheme } from "@/theme";

import { OptionChip } from "../OptionChip";

type MultiSelectChipsProps<T extends string> = {
  /** Every answer and its words, in the order they're shown. */
  options: Record<T, string>;
  /** The answers that are on. Pass some in to start with them picked. */
  picked: T[];
  /** Runs on every tap with the new list. */
  onChange: (picked: T[]) => void;
};

/**
 * Chips where any number can be picked. Tapping a chip turns it on or off.
 *
 * For "none of these", don't add a chip: change the main button's label when `picked` is empty
 * (see the conditions question).
 *
 * @example
 * ```tsx
 * const [conditions, setConditions] = useState<Condition[]>([]);
 * <MultiSelectChips options={conditionText} picked={conditions} onChange={setConditions} />
 * ```
 */
export function MultiSelectChips<T extends string>({
  options,
  picked,
  onChange,
}: MultiSelectChipsProps<T>) {
  const { space } = useTheme();
  const toggle = (value: T) =>
    onChange(picked.includes(value) ? picked.filter((p) => p !== value) : [...picked, value]);

  return (
    <View style={[styles.wrap, { gap: space[8] }]}>
      {(Object.keys(options) as T[]).map((value) => (
        <OptionChip
          key={value}
          label={options[value]}
          selected={picked.includes(value)}
          onPress={() => toggle(value)}
        />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", flexWrap: "wrap" },
});
