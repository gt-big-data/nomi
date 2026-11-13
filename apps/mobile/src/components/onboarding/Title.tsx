import { Text } from "react-native";

import { useTheme } from "@/theme";

/**
 * How far onboarding titles grow with large text. They start at 28, so 2× (56) is already huge,
 * and at 3× words like "conditions" no longer fit across the screen and break mid-word.
 */
const MAX_SCALE = 2;

/**
 * The big title at the top of an onboarding screen. Screen readers treat it as a heading.
 *
 * @example
 * ```tsx
 * <Title>Who are you scanning for?</Title>
 * ```
 */
export function Title({ children }: { children: string }) {
  const { colors, text } = useTheme();
  return (
    <Text
      accessibilityRole="header"
      maxFontSizeMultiplier={MAX_SCALE}
      style={[text("titleLarge", { maxScale: MAX_SCALE }), { color: colors.text.primary }]}
    >
      {children}
    </Text>
  );
}
