import type { ReactNode } from "react";
import { Pressable, type StyleProp, StyleSheet, View, type ViewStyle } from "react-native";

import { opacity } from "@/theme";

type TappableProps = {
  /** Runs when tapped. Leave it out and the area is plain, read-only content. */
  onPress?: () => void;
  /** Everything screen readers hear for the area. Build it with `spokenLabel()`. */
  accessibilityLabel: string;
  /** What tapping does, when the label doesn't make it obvious. Only used with `onPress`. */
  accessibilityHint?: string;
  /** What screen readers call it when it can be tapped. Defaults to `button`. */
  role?: "button" | "link";
  /** Extra space around the area that still counts as a tap, in points. */
  hitSlop?: number;
  /** Hide it from screen readers when the row it sits in already says it. Only without `onPress`. */
  decorative?: boolean;
  style: StyleProp<ViewStyle>;
  children: ReactNode;
};

/**
 * A card, row or chip that may or may not be tappable. With `onPress` it's a Pressable that dims
 * while pressed; without it, a View screen readers read as one piece of text.
 *
 * @example
 * ```tsx
 * <Tappable
 *   onPress={onPress}
 *   accessibilityLabel={spokenLabel([title, body])}
 *   style={[styles.box, { padding: space[16] }]}
 * >
 *   <Text>{title}</Text>
 * </Tappable>
 * ```
 */
export function Tappable({
  onPress,
  accessibilityLabel,
  accessibilityHint,
  role = "button",
  hitSlop,
  decorative = false,
  style,
  children,
}: TappableProps) {
  if (!onPress && decorative) {
    // Without this, Android TalkBack stops on it again after reading the row.
    return (
      <View aria-hidden style={style}>
        {children}
      </View>
    );
  }
  if (!onPress) {
    return (
      <View
        accessible
        accessibilityRole="text"
        accessibilityLabel={accessibilityLabel}
        style={style}
      >
        {children}
      </View>
    );
  }
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole={role}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      hitSlop={hitSlop}
      style={({ pressed }) => [style, pressed && styles.pressed]}
    >
      {children}
    </Pressable>
  );
}

/**
 * Joins the parts of a screen-reader label into sentences, skipping empty parts. A " · " inside a
 * part becomes a comma, so screen readers don't read the dot out loud.
 *
 * @example
 * ```ts
 * spokenLabel(["Benadryl Allergy", "Score 28, High risk", "For Mom · 2:14 PM"]);
 * // "Benadryl Allergy. Score 28, High risk. For Mom, 2:14 PM"
 * ```
 */
export function spokenLabel(parts: (string | null | undefined | false)[]): string {
  return parts
    .filter((part): part is string => Boolean(part))
    .map((part) => part.split(" · ").join(", "))
    .join(". ");
}

const styles = StyleSheet.create({
  pressed: { opacity: opacity.pressed },
});
