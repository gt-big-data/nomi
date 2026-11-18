/**
 * Design tokens from the Figma Nomi Library.
 *
 * Names follow the Figma variables: `color/tier/low/mark` in Figma is `colors.tier.low.mark` here.
 * If you change a value, change it in Figma too, so design and code stay the same.
 * Components should never use a color, size or font that isn't in this file. `borderWidth`,
 * `minHeight` and `opacity` aren't Figma variables yet.
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
    /** Segmented control track, score ring track */
    fill: string;
    /** The selected segment's thumb, lighter than the track in both modes */
    thumb: string;
  };
  border: {
    /** Card borders and dividers */
    subtle: string;
    /** Hairlines between rows inside a grouped list */
    separator: string;
  };
  text: {
    /** Main text */
    primary: string;
    /** Supporting text, inactive tabs */
    secondary: string;
    /** Footnotes and disclaimers; still 4.5:1 on the canvas */
    tertiary: string;
    /** Chevrons and quiet glyphs */
    glyph: string;
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
    low: { mark: string; text: string; tint: string };
    /** Use with caution (score 50–74) */
    moderate: { mark: string; text: string; tint: string };
    /** High risk (score under 50) */
    high: { mark: string; text: string; tint: string };
    /** Hard stop: “Do not use” */
    stop: { fill: string; on: string };
    /** Not scored (homeopathic or out of scope) */
    none: { mark: string; text: string; tint: string };
  };
  /**
   * Destructive buttons, like "Delete all my data". Its own token so tier colors stay for risk
   * only, even though it's red.
   */
  destructive: { fill: string; on: string };
};

export const colors: Record<ColorScheme, Colors> = {
  light: {
    bg: {
      canvas: "#F6F5F9",
      surface: "#FFFFFF",
      camera: "#0F0C15",
      fill: "#EEECF2",
      thumb: "#FFFFFF",
    },
    border: { subtle: "#D6D1E0", separator: "#E7E4EE" },
    text: { primary: "#17131F", secondary: "#5E5869", tertiary: "#6E6878", glyph: "#8F8999" },
    brand: { primary: "#5A21B5", onPrimary: "#FFFFFF", tint: "#EFE8FB", text: "#5A21B5" },
    tier: {
      low: { mark: "#005733", text: "#005733", tint: "#E3F5EC" },
      moderate: { mark: "#C77A04", text: "#8A5300", tint: "#FEF5E6" },
      high: { mark: "#D41852", text: "#B5103F", tint: "#FCE9EB" },
      stop: { fill: "#B5103F", on: "#FFFFFF" },
      none: { mark: "#857F90", text: "#5E5869", tint: "#EEECF2" },
    },
    destructive: { fill: "#B5103F", on: "#FFFFFF" },
  },
  dark: {
    bg: {
      canvas: "#121018",
      surface: "#1E1A26",
      camera: "#0F0C15",
      fill: "#2A2633",
      thumb: "#3A3446",
    },
    border: { subtle: "#3A3346", separator: "#2E2938" },
    text: { primary: "#F4F1FA", secondary: "#A9A2B6", tertiary: "#9890A6", glyph: "#6E6878" },
    brand: { primary: "#7B4CE0", onPrimary: "#FFFFFF", tint: "#2A2140", text: "#C9B3F5" },
    tier: {
      low: { mark: "#1EA987", text: "#3CC79C", tint: "#102C25" },
      moderate: { mark: "#FCD08D", text: "#FCD08D", tint: "#33260F" },
      high: { mark: "#D8152F", text: "#FF8A93", tint: "#2E1519" },
      stop: { fill: "#D8152F", on: "#FFFFFF" },
      none: { mark: "#6E6878", text: "#A9A2B6", tint: "#2A2633" },
    },
    destructive: { fill: "#D8152F", on: "#FFFFFF" },
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

/** Border widths in points. Cards and rows use `card`; option chips and cards use `control`. */
export const borderWidth = {
  card: 1,
  control: 1.5,
  /** The scan frame on the camera. */
  scanFrame: 3,
} as const;

/** Minimum heights in points, so controls stay easy to tap. */
export const minHeight = {
  /** 48 is the Android minimum tap size (iOS asks for 44). */
  chip: 48,
  button: 52,
} as const;

/** Opacity for anything being pressed. */
export const opacity = {
  pressed: 0.7,
  /** The dimmed camera picture around the scan frame. */
  scrim: 0.6,
} as const;

/**
 * Every icon size the Nomi Library uses, each with its line thickness (Figma's stroke weight), in
 * points. If a design needs a new size, add it to Figma first, then here.
 */
export const iconSize = {
  /** Tier, risk severity and citation pills */
  pill: { size: 14, strokeWidth: 1.4 },
  /** Chevron on tappable rows and banners */
  chevron: { size: 18, strokeWidth: 1.5 },
  /** Premium gem on buttons */
  button: { size: 18, strokeWidth: 2 },
  /** Alert banner icon */
  banner: { size: 22, strokeWidth: 1.83 },
  /** "Do not use" icon in the small score dot */
  dot: { size: 22, strokeWidth: 2 },
  /** "Do not use" icon in the large score ring */
  ring: { size: 72, strokeWidth: 6 },
  /** Back arrow in the onboarding top bar */
  back: { size: 20, strokeWidth: 1.67 },
  /** Icons in the circles on the welcome screen */
  feature: { size: 20, strokeWidth: 1.5 },
  /** Glass circle buttons: close, home, profile */
  nav: { size: 20, strokeWidth: 2 },
  /** Stop sign in the "Do not use" disc */
  stop: { size: 30, strokeWidth: 2.5 },
  /** The one icon on an empty or error screen */
  empty: { size: 40, strokeWidth: 1.75 },
} as const;

export type IconSize = keyof typeof iconSize;

/** Figtree, loaded by `useNomiFonts()` (fonts.ts). Three weights: regular, semibold and bold. */
export const fontFamily = {
  regular: "Figtree_400Regular",
  semiBold: "Figtree_600SemiBold",
  bold: "Figtree_700Bold",
} as const;

export type TextStyleToken = {
  fontFamily: string;
  fontSize: number;
  lineHeight: number;
  letterSpacing: number;
  textTransform?: "uppercase";
  /** Same-width digits, so a score doesn't shift when it changes. */
  fontVariant?: "tabular-nums"[];
};

/** Figma letter spacing is a percent of the font size; React Native wants points. */
const tracking = (fontSize: number, percent: number) => +((fontSize * percent) / 100).toFixed(2);

/**
 * Type scale (Figma text styles). Sizes and line heights in points.
 *
 * Six sizes (46, 28, 20, 15, 13, 11) and three weights, so screens don't get busy.
 */
export const typography = {
  /** Score number in the large ring */
  scoreLarge: {
    fontFamily: fontFamily.bold,
    fontSize: 46,
    lineHeight: 48,
    letterSpacing: tracking(46, -3),
    fontVariant: ["tabular-nums"],
  },
  /** Score number in the result's verdict ring */
  scoreHero: {
    fontFamily: fontFamily.bold,
    fontSize: 56,
    lineHeight: 60,
    letterSpacing: -2,
    fontVariant: ["tabular-nums"],
  },
  /** The verdict word next to the ring, e.g. "Use with caution" */
  verdict: { fontFamily: fontFamily.bold, fontSize: 26, lineHeight: 30, letterSpacing: -0.4 },
  /** Page titles: Home, Profile, Type a barcode */
  largeTitle: { fontFamily: fontFamily.bold, fontSize: 34, lineHeight: 40, letterSpacing: -0.8 },
  /** Product name on the result, sheet titles */
  title: { fontFamily: fontFamily.bold, fontSize: 28, lineHeight: 34, letterSpacing: -0.6 },
  /** Row titles and buttons in grouped lists */
  headline: { fontFamily: fontFamily.semiBold, fontSize: 17, lineHeight: 22, letterSpacing: 0 },
  /** Reading text: reasons, quotes */
  bodyLarge: { fontFamily: fontFamily.regular, fontSize: 17, lineHeight: 23, letterSpacing: 0 },
  /** Subtitles under titles, captions under controls */
  subhead: { fontFamily: fontFamily.regular, fontSize: 15, lineHeight: 20, letterSpacing: 0 },
  /** Score number in dots and list rows */
  scoreSmall: {
    fontFamily: fontFamily.bold,
    fontSize: 16,
    lineHeight: 20,
    letterSpacing: 0,
    fontVariant: ["tabular-nums"],
  },
  /** Tab titles, product name on the result */
  titleLarge: {
    fontFamily: fontFamily.bold,
    fontSize: 28,
    lineHeight: 34,
    letterSpacing: tracking(28, -2),
  },
  /** Screen headings, sheet titles, section headings */
  titleSmall: { fontFamily: fontFamily.bold, fontSize: 20, lineHeight: 26, letterSpacing: 0 },
  /** Paragraphs, the bottom line, risk sentences */
  body: { fontFamily: fontFamily.regular, fontSize: 15, lineHeight: 22, letterSpacing: 0 },
  /** Row titles, risk factor names, chips */
  bodyStrong: { fontFamily: fontFamily.semiBold, fontSize: 15, lineHeight: 22, letterSpacing: 0 },
  /** Button labels */
  button: { fontFamily: fontFamily.bold, fontSize: 15, lineHeight: 20, letterSpacing: 0 },
  /** Row subtitles, details */
  footnote: { fontFamily: fontFamily.regular, fontSize: 13, lineHeight: 18, letterSpacing: 0 },
  /** Citation chips, tab labels, review status */
  caption: { fontFamily: fontFamily.semiBold, fontSize: 13, lineHeight: 18, letterSpacing: 0 },
  /** Section labels and tier labels (all caps) */
  label: {
    fontFamily: fontFamily.semiBold,
    fontSize: 11,
    lineHeight: 14,
    letterSpacing: tracking(11, 6),
    textTransform: "uppercase",
  },
} satisfies Record<string, TextStyleToken>;

export type TypographyName = keyof typeof typography;
