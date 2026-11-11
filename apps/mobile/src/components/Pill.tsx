import { StyleSheet, Text } from "react-native";

import { useIconScale, useTheme } from "@/theme";

import { Icon, type IconName } from "./Icon";
import { Tappable } from "./Tappable";

type PillProps = {
  icon: IconName;
  /** The word shown in the pill. */
  label: string;
  /** `label` for status words (all caps), `caption` for chips. */
  textStyle: "label" | "caption";
  background: string;
  /** Icon and text color. */
  foreground: string;
  /** What screen readers hear. Defaults to `label`. */
  accessibilityLabel?: string;
  /** Makes the pill tappable. See `Tappable` for the rest of these props. */
  onPress?: () => void;
  role?: "button" | "link";
  accessibilityHint?: string;
  /** Where the pill sits in its column. `center` also centers wrapped text. Defaults to `start`. */
  align?: "start" | "center";
  /** Hide it from screen readers when the row it sits in already says it. Ignored with `onPress`. */
  decorative?: boolean;
};

/**
 * The shared rounded shape behind TierLabel, RiskSeverityLabel and CitationChip: a small icon and
 * a short word. Not exported; screens use those components instead.
 *
 * @example
 * ```tsx
 * <Pill icon="info" label="Low" textStyle="label" background={c.tint} foreground={c.text} />
 * ```
 */
export function Pill({
  icon,
  label,
  textStyle,
  background,
  foreground,
  accessibilityLabel = label,
  onPress,
  role,
  accessibilityHint,
  align = "start",
  decorative = false,
}: PillProps) {
  const { radius, space, text } = useTheme();
  // Grows with the text, up to 3x, so the icon keeps up with the word next to it.
  const iconScale = useIconScale(3);

  return (
    <Tappable
      onPress={onPress}
      role={role}
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      // A pill is small, so when it's tappable the tap area reaches past it to about 48 points.
      hitSlop={onPress ? space[12] : undefined}
      decorative={decorative}
      style={[
        styles.pill,
        align === "center" && styles.center,
        {
          backgroundColor: background,
          borderRadius: radius.pill,
          gap: space[4],
          paddingVertical: space[4],
          paddingLeft: space[8],
          paddingRight: space[12],
        },
      ]}
    >
      <Icon name={icon} size="pill" scale={iconScale} color={foreground} />
      <Text
        style={[
          text(textStyle),
          styles.shrink,
          align === "center" && styles.centerText,
          { color: foreground },
        ]}
      >
        {label}
      </Text>
    </Tappable>
  );
}

const styles = StyleSheet.create({
  pill: { flexDirection: "row", alignItems: "center", alignSelf: "flex-start", maxWidth: "100%" },
  center: { alignSelf: "center" },
  shrink: { flexShrink: 1 },
  centerText: { textAlign: "center" },
});
