import { useFonts } from "expo-font";
import { Inter_400Regular } from "@expo-google-fonts/inter/400Regular";
import { Inter_600SemiBold } from "@expo-google-fonts/inter/600SemiBold";
import { Inter_700Bold } from "@expo-google-fonts/inter/700Bold";
import { Inter_800ExtraBold } from "@expo-google-fonts/inter/800ExtraBold";

/**
 * Loads the four Inter weights the type scale uses. Call it once in the root layout and render
 * nothing (or keep the splash screen) until it returns true. Fonts ship with the app, so this
 * works offline. If loading fails, it still returns true and text falls back to the system font.
 */
export function useNomiFonts(): boolean {
  const [loaded, error] = useFonts({
    Inter_400Regular,
    Inter_600SemiBold,
    Inter_700Bold,
    Inter_800ExtraBold,
  });
  return loaded || error != null;
}
