import { createContext, type ReactNode, useContext, useMemo } from "react";
import { useColorScheme, useWindowDimensions } from "react-native";

import {
  type Colors,
  colors,
  type ColorScheme,
  radius,
  space,
  type TextStyleToken,
  typography,
  type TypographyName,
} from "./tokens";

export type Theme = {
  scheme: ColorScheme;
  colors: Colors;
  space: typeof space;
  radius: typeof radius;
  /**
   * Extra text scale on top of the phone's own text size setting. Always 1 in the app; the
   * gallery raises it to preview large text on the web, where there is no system setting.
   */
  textScale: number;
  /**
   * A type-scale style, ready to spread into a Text style.
   *
   * @param name - Which style from the type scale, e.g. "body" or "caption".
   * @param options - `maxScale` caps growth for text that sits inside a fixed shape (the score
   *   ring). Pass the same number to the Text's `maxFontSizeMultiplier` so the phone setting is
   *   capped too.
   *
   * @example
   * ```tsx
   * <Text style={[text("body"), { color: colors.text.primary }]}>Plain paragraph</Text>
   * <Text maxFontSizeMultiplier={1.2} style={text("scoreLarge", { maxScale: 1.2 })}>84</Text>
   * ```
   */
  text: (name: TypographyName, options?: { maxScale?: number }) => TextStyleToken;
};

function makeTheme(scheme: ColorScheme, textScale: number): Theme {
  return {
    scheme,
    colors: colors[scheme],
    space,
    radius,
    textScale,
    text: (name, options) => {
      const style: TextStyleToken = typography[name];
      const k = Math.min(textScale, options?.maxScale ?? Infinity);
      if (k === 1) return style;
      return {
        ...style,
        fontSize: style.fontSize * k,
        lineHeight: style.lineHeight * k,
        letterSpacing: style.letterSpacing * k,
      };
    },
  };
}

const ThemeContext = createContext<Theme | null>(null);

type ThemeProviderProps = {
  /** Force light or dark. Leave it out to follow the phone's setting. */
  scheme?: ColorScheme;
  /** See `Theme.textScale`. Leave at 1 outside the gallery. */
  textScale?: number;
  children: ReactNode;
};

/**
 * Wrap the app (root layout) in this. Nested providers can override the scheme for one area.
 *
 * @example
 * ```tsx
 * // Root layout: follow the phone's light/dark setting
 * <ThemeProvider>
 *   <Stack />
 * </ThemeProvider>
 *
 * // One area always dark
 * <ThemeProvider scheme="dark">
 *   <ScoreBadge tier="low" score={84} />
 * </ThemeProvider>
 * ```
 */
export function ThemeProvider({ scheme, textScale = 1, children }: ThemeProviderProps) {
  const system = useColorScheme();
  const resolved: ColorScheme = scheme ?? (system === "dark" ? "dark" : "light");
  const theme = useMemo(() => makeTheme(resolved, textScale), [resolved, textScale]);
  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
}

/**
 * The current theme. Works without a provider too (follows the phone's light/dark setting).
 *
 * @example
 * ```tsx
 * function Card({ title }: { title: string }) {
 *   const { colors, space, radius, text } = useTheme();
 *   return (
 *     <View
 *       style={{ backgroundColor: colors.bg.surface, padding: space[16], borderRadius: radius.md }}
 *     >
 *       <Text style={[text("bodyStrong"), { color: colors.text.primary }]}>{title}</Text>
 *     </View>
 *   );
 * }
 * ```
 */
export function useTheme(): Theme {
  const fromProvider = useContext(ThemeContext);
  const system = useColorScheme();
  const fallback = useMemo(() => makeTheme(system === "dark" ? "dark" : "light", 1), [system]);
  return fromProvider ?? fallback;
}

/**
 * How much to grow an icon that sits next to text, so it keeps up with large text settings
 * (the phone's text size times the gallery preview), up to `max`.
 *
 * @param max - The largest multiplier it will return. Defaults to 1.5.
 *
 * @example
 * ```tsx
 * const k = useIconScale();
 * <Icon name="info" size={22 * k} color={colors.brand.text} strokeWidth={1.83 * k} />
 * ```
 */
export function useIconScale(max = 1.5): number {
  const { fontScale } = useWindowDimensions();
  const { textScale } = useTheme();
  return Math.min(max, Math.max(1, fontScale * textScale));
}
