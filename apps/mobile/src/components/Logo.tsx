import { StyleSheet, Text, View } from "react-native";
import Svg, { Path } from "react-native-svg";

import { useIconScale, useTheme } from "@/theme";

/** Size of the cat in points, and how far the logo grows with large text (it's already big). */
const CAT_SIZE = 48;
const MAX_SCALE = 1.5;

/** The cat's paths from the Nomi Demo Prototype (icon/cat), on a 48×48 grid. */
const CAT = [
  "M12.75 18L12 6.75L19.5 12C22.5 10.875 25.5 10.875 28.5 12L36 6.75L35.25 18",
  "M24 28.5C30.6274 28.5 36 24.4706 36 19.5C36 14.5294 30.6274 10.5 24 10.5C17.3726 10.5 12 14.5294 12 19.5C12 24.4706 17.3726 28.5 24 28.5Z",
  "M18.75 19.5C19.75 18.25 20.75 18.25 21.75 19.5M26.25 19.5C27.25 18.25 28.25 18.25 29.25 19.5M15 27.75C21 30.25 27 30.25 33 27.75",
  "M24 33.375C25.0355 33.375 25.875 32.5355 25.875 31.5C25.875 30.4645 25.0355 29.625 24 29.625C22.9645 29.625 22.125 30.4645 22.125 31.5C22.125 32.5355 22.9645 33.375 24 33.375Z",
  "M15 28.5C12 32.5 11 37 12 42H36C37 37 36 32.5 33 28.5M34.5 23.25C36.5 18.75 38.5 16 40.5 15C42 16 42.5 17.5 42 19.5C41 22.5 39.5 24.75 37.5 26.25",
];

/**
 * The "nomi" wordmark with the cat, for the welcome screen. Screen readers hear "Nomi".
 *
 * @example
 * ```tsx
 * <Logo />
 * ```
 */
export function Logo() {
  const { colors, space, text } = useTheme();
  // The cat grows with the word next to it, like an icon beside text.
  const size = CAT_SIZE * useIconScale(MAX_SCALE);

  return (
    <View
      accessible
      accessibilityRole="header"
      accessibilityLabel="Nomi"
      style={[styles.row, { gap: space[8] }]}
    >
      {/* The wordmark is the one place the score number's size is used for words. */}
      <Text
        maxFontSizeMultiplier={MAX_SCALE}
        style={[text("scoreLarge", { maxScale: MAX_SCALE }), { color: colors.text.primary }]}
      >
        nomi
      </Text>
      <Svg width={size} height={size} viewBox="0 0 48 48" fill="none">
        {CAT.map((d) => (
          <Path
            key={d}
            d={d}
            stroke={colors.brand.text}
            strokeWidth={2.25}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", flexWrap: "wrap" },
});
