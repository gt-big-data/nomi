import Svg, { G, Path } from "react-native-svg";

import { useIconScale, useTheme } from "@/theme";

import { CAT_PATH, LOGO_TRANSFORM, LOGO_VIEWBOX as BOX, WORDMARK_PATH } from "./logoPaths";

/** Height of the logo in points, and how far it grows with large text (it's already big). */
const HEIGHT = 64;
const MAX_SCALE = 1.5;

/**
 * Nomi's logo, the "nomi" wordmark with the waving cat, for the welcome screen. The wordmark
 * follows the text color and the cat the brand color, so it reads in light and dark mode.
 * Screen readers hear "Nomi".
 *
 * @example
 * ```tsx
 * <Logo />
 * ```
 */
export function Logo() {
  const { colors } = useTheme();
  const height = HEIGHT * useIconScale(MAX_SCALE);

  return (
    <Svg
      accessible
      accessibilityRole="header"
      accessibilityLabel="Nomi"
      width={(height * BOX.width) / BOX.height}
      height={height}
      viewBox={`${BOX.x} ${BOX.y} ${BOX.width} ${BOX.height}`}
    >
      <G transform={LOGO_TRANSFORM}>
        <Path d={WORDMARK_PATH} fill={colors.text.primary} />
        <Path d={CAT_PATH} fill={colors.brand.text} />
      </G>
    </Svg>
  );
}
