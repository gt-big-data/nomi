import { Pressable, StyleSheet, Text } from "react-native";

import { type Colors, minHeight, opacity, useIconScale, useTheme } from "@/theme";

import { Icon } from "./Icon";
export type ButtonType = "primary" | "secondary" | "ghost" | "destructive";

type ButtonProps = {
  /** What it does, verb first, e.g. "See safer alternative". */
  label: string;
  /** Runs when the button is tapped. */
  onPress: () => void;
  /** How much emphasis it has. Defaults to `primary`. The types are described on `Button`. */
  type?: ButtonType;
  /** Shows the gem: the action needs Premium (tapping it should open the Premium sheet). */
  gem?: boolean;
  /** Extra screen-reader hint, e.g. "Opens the comparison". */
  accessibilityHint?: string;
};

function typeColors(c: Colors, type: ButtonType) {
  switch (type) {
    case "primary":
      return { background: c.brand.primary, foreground: c.brand.onPrimary };
    case "secondary":
      return { background: c.brand.tint, foreground: c.brand.text };
    case "ghost":
      return { background: undefined, foreground: c.brand.text };
    case "destructive":
      return { background: c.destructive.fill, foreground: c.destructive.on };
  }
}

/**
 * Full-width action, at least `minHeight.button` (52) points tall. Grows taller with large text
 * instead of clipping.
 *
 * Types, from most to least emphasis:
 * - `primary` (default): the one main action on a screen. Brand purple. Use one per screen.
 * - `secondary`: the next most likely action. Purple text on a light purple tint.
 * - `ghost`: text only, for skipping or dismissing, e.g. "Not now".
 * - `destructive`: deletes or can't be undone, e.g. "Delete all my data". Red. Confirm first.
 *
 * Green and red stay for risk, so there's no green button: use `primary` or `secondary` for
 * adding a safer pick.
 *
 * Screen readers hear the label as a button. Add `accessibilityHint` when the result of tapping
 * isn't obvious from the label. With `gem`, they also hear "Premium" and, unless you pass your
 * own hint, "Needs Nomi Premium".
 *
 * @example
 * ```tsx
 * <Button
 *   label="See safer alternative"
 *   onPress={openAlternative}
 *   accessibilityHint="Opens the side-by-side comparison"
 * />
 * <Button type="secondary" label="Add to Mom’s cabinet" onPress={addToCabinet} />
 * <Button type="ghost" label="Not now" onPress={dismiss} />
 * <Button
 *   type="destructive"
 *   label="Delete all my data"
 *   onPress={confirmDelete}
 *   accessibilityHint="Asks you to confirm first"
 * />
 * <Button gem label="See Premium" onPress={openPremium} />
 * ```
 */
export function Button({
  label,
  onPress,
  type = "primary",
  gem = false,
  accessibilityHint,
}: ButtonProps) {
  const { colors, radius, space, text } = useTheme();
  const c = typeColors(colors, type);
  const iconScale = useIconScale();

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={gem ? `${label}, Premium` : label}
      accessibilityHint={accessibilityHint ?? (gem ? "Needs Nomi Premium" : undefined)}
      style={({ pressed }) => [
        styles.button,
        {
          backgroundColor: c.background,
          borderRadius: radius.md,
          gap: space[8],
          paddingHorizontal: space[20],
          paddingVertical: space[16],
        },
        pressed && styles.pressed,
      ]}
    >
      {gem && (
        <Icon name="gem" size={18 * iconScale} color={c.foreground} strokeWidth={2 * iconScale} />
      )}
      <Text style={[text("button"), styles.label, { color: c.foreground }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    minHeight: minHeight.button,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    alignSelf: "stretch",
  },
  label: { flexShrink: 1, textAlign: "center" },
  pressed: { opacity: opacity.pressed },
});
