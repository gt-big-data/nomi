/**
 * Design tokens from the Figma Nomi Library.
 *
 * Names follow the Figma variables: `color/tier/low/mark` in Figma is `colors.tier.low.mark` here.
 * If you change a value, change it in Figma too, so design and code stay the same.
 * Components should never use a color, size or font that isn't in this file.
 */

export type ColorScheme = "light" | "dark";

export type Colors = {
  bg: {
    /** Page background */
    canvas: string;
    /** Cards, sheets, nav and tab bars */
    surface: string;
    /** Scanner background (same in both modes) */
    camera: string;
  };
  border: {
    /** Card borders and dividers */
    subtle: string;
  };
  text: {
    /** Main text */
    primary: string;
    /** Supporting text, inactive tabs */
    secondary: string;
  };
  brand: {
    /** Primary buttons, selected chips, scan button */
    primary: string;
    /** Text and icons on brand.primary */
    onPrimary: string;
    /** Brand-tinted backgrounds (citation chips, person pill) */
    tint: string;
    /** Links and brand-colored text */
    text: string;
  };
  tier: {
    /** Low risk (score 75+) */
    low: { mark: string; text: string; tint: string; on: string };
    /** Use with care (score 50–74) */
    care: { mark: string; text: string; tint: string };
    /** High risk (score under 50) */
    high: { mark: string; text: string; tint: string };
    /** Hard stop: “Do not use” */
    stop: { fill: string; on: string };
    /** Not scored (homeopathic or out of scope) */
    none: { mark: string; text: string; tint: string };
  };
};

export const colors: Record<ColorScheme, Colors> = {
  light: {
    bg: { canvas: "#F6F5F9", surface: "#FFFFFF", camera: "#0F0C15" },
    border: { subtle: "#E7E4EE" },
    text: { primary: "#17131F", secondary: "#5E5869" },
    brand: { primary: "#5A21B5", onPrimary: "#FFFFFF", tint: "#EFE8FB", text: "#5A21B5" },
    tier: {
      low: { mark: "#005733", text: "#005733", tint: "#E3F5EC", on: "#FFFFFF" },
      care: { mark: "#C77A04", text: "#8A5300", tint: "#FEF5E6" },
      high: { mark: "#D41852", text: "#B5103F", tint: "#FCE9EB" },
      stop: { fill: "#B5103F", on: "#FFFFFF" },
      none: { mark: "#857F90", text: "#5E5869", tint: "#EEECF2" },
    },
  },
  dark: {
    bg: { canvas: "#121018", surface: "#1E1A26", camera: "#0F0C15" },
    border: { subtle: "#2E2838" },
    text: { primary: "#F4F1FA", secondary: "#A9A2B6" },
    brand: { primary: "#7B4CE0", onPrimary: "#FFFFFF", tint: "#2A2140", text: "#C9B3F5" },
    tier: {
      low: { mark: "#1EA987", text: "#3CC79C", tint: "#102C25", on: "#06231A" },
      care: { mark: "#FCD08D", text: "#FCD08D", tint: "#33260F" },
      high: { mark: "#D8152F", text: "#FF8A93", tint: "#2E1519" },
      stop: { fill: "#D8152F", on: "#FFFFFF" },
      none: { mark: "#6E6878", text: "#A9A2B6", tint: "#2A2633" },
    },
  },
};

/** Spacing scale in points (Figma: Spacing / space/*). */
export const space = {
  2: 2,
  4: 4,
  8: 8,
  12: 12,
  16: 16,
  20: 20,
  24: 24,
  32: 32,
  48: 48,
} as const;

/** Corner radii in points (Figma: Spacing / radius/*). */
export const radius = {
  sm: 10,
  md: 16,
  lg: 20,
  pill: 999,
} as const;

/** Inter, loaded by `useNomiFonts()` (fonts.ts). */
export const fontFamily = {
  regular: "Inter_400Regular",
  semiBold: "Inter_600SemiBold",
  bold: "Inter_700Bold",
  extraBold: "Inter_800ExtraBold",
} as const;

export type TextStyleToken = {
  fontFamily: string;
  fontSize: number;
  lineHeight: number;
  letterSpacing: number;
  textTransform?: "uppercase";
};

/** Figma letter spacing is a percent of the font size; React Native wants points. */
const tracking = (fontSize: number, percent: number) => +((fontSize * percent) / 100).toFixed(2);

/** Type scale (Figma text styles). Sizes and line heights in points. */
export const typography = {
  /** Score number in the large ring */
  scoreLarge: {
    fontFamily: fontFamily.extraBold,
    fontSize: 46,
    lineHeight: 48,
    letterSpacing: tracking(46, -3),
  },
  /** Score number in dots and list rows */
  scoreSmall: {
    fontFamily: fontFamily.extraBold,
    fontSize: 16,
    lineHeight: 20,
    letterSpacing: 0,
  },
  /** Tab titles */
  titleLarge: {
    fontFamily: fontFamily.extraBold,
    fontSize: 30,
    lineHeight: 36,
    letterSpacing: tracking(30, -2),
  },
  /** Product name, screen headings */
  titleMedium: {
    fontFamily: fontFamily.extraBold,
    fontSize: 24,
    lineHeight: 30,
    letterSpacing: tracking(24, -1),
  },
  /** Sheet titles */
  titleSmall: { fontFamily: fontFamily.extraBold, fontSize: 20, lineHeight: 26, letterSpacing: 0 },
  /** Hard-stop message, nav titles */
  headline: { fontFamily: fontFamily.bold, fontSize: 17, lineHeight: 24, letterSpacing: 0 },
  /** Paragraphs, the bottom line */
  body: { fontFamily: fontFamily.regular, fontSize: 15, lineHeight: 22, letterSpacing: 0 },
  /** Row titles, risk factor names */
  bodyStrong: { fontFamily: fontFamily.semiBold, fontSize: 15, lineHeight: 22, letterSpacing: 0 },
  /** Secondary paragraphs */
  callout: { fontFamily: fontFamily.regular, fontSize: 14, lineHeight: 20, letterSpacing: 0 },
  /** Chips, person pill */
  calloutStrong: {
    fontFamily: fontFamily.semiBold,
    fontSize: 14,
    lineHeight: 20,
    letterSpacing: 0,
  },
  /** Row subtitles, details */
  footnote: { fontFamily: fontFamily.regular, fontSize: 13, lineHeight: 18, letterSpacing: 0 },
  /** Citation chips, tab labels, review status */
  caption: { fontFamily: fontFamily.semiBold, fontSize: 12, lineHeight: 16, letterSpacing: 0 },
  /** Section labels and tier labels (all caps) */
  label: {
    fontFamily: fontFamily.extraBold,
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: tracking(11, 6),
    textTransform: "uppercase",
  },
  /** Button labels */
  button: { fontFamily: fontFamily.bold, fontSize: 16, lineHeight: 20, letterSpacing: 0 },
} satisfies Record<string, TextStyleToken>;

export type TypographyName = keyof typeof typography;
