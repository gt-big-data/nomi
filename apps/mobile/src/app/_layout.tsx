import { useEffect } from "react";
import { DarkTheme, DefaultTheme, Stack, ThemeProvider as NavThemeProvider } from "expo-router";
import * as SplashScreen from "expo-splash-screen";

import { loadProfile, useSavedProfile } from "@/storage/activeProfile";
import { loadCabinet } from "@/storage/cabinet";
import { ThemeProvider, useNomiFonts, useTheme } from "@/theme";

// A deep link to /result still gets the camera underneath it, so Back has somewhere to go.
export const unstable_settings = { initialRouteName: "index" };

// Keep the splash screen up until the fonts and the saved profile are ready.
SplashScreen.preventAutoHideAsync();
loadProfile();
loadCabinet();

export default function RootLayout() {
  const fontsReady = useNomiFonts();
  const profileLoaded = useSavedProfile() !== undefined;
  const ready = fontsReady && profileLoaded;

  useEffect(() => {
    if (ready) SplashScreen.hideAsync();
  }, [ready]);

  if (!ready) return null;

  return (
    <ThemeProvider>
      <Navigator />
    </ThemeProvider>
  );
}

/** Inside <ThemeProvider>, so useTheme() gets the provider's theme instead of a default one. */
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
