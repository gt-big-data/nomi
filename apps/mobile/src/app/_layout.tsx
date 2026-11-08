import { DarkTheme, DefaultTheme, Stack, ThemeProvider as NavThemeProvider } from "expo-router";

import { ThemeProvider, useTheme } from "@/theme";

export default function RootLayout() {
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
    <ThemeProvider>
      <NavThemeProvider value={navTheme}>
        <Stack />
      </NavThemeProvider>
    </ThemeProvider>
  );
}
