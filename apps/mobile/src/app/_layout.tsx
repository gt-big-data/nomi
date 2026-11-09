import { useEffect } from "react";
import { DarkTheme, DefaultTheme, Stack, ThemeProvider as NavThemeProvider } from "expo-router";
import * as SplashScreen from "expo-splash-screen";

import { ThemeProvider, useNomiFonts, useTheme } from "@/theme";

// Keep the splash screen up until the fonts are ready.
SplashScreen.preventAutoHideAsync();

export default function RootLayout() {
  const fontsReady = useNomiFonts();

  useEffect(() => {
    if (fontsReady) SplashScreen.hideAsync();
  }, [fontsReady]);

  if (!fontsReady) return null;

  return (
    <ThemeProvider>
      <Navigator />
    </ThemeProvider>
  );
}

/** A child of ThemeProvider, so useTheme() reads the provider instead of its fallback. */
function Navigator() {
  const { scheme, colors } = useTheme();
  const base = scheme === "dark" ? DarkTheme : DefaultTheme;
  const navTheme = {
    ...base,
    colors: {
      ...base.colors,
      background: colors.bg.canvas,
      card: colors.bg.surface,
      text: colors.text.primary,
      border: colors.border.subtle,
      primary: colors.brand.primary,
    },
  };

  return (
    <NavThemeProvider value={navTheme}>
      <Stack />
    </NavThemeProvider>
  );
}
