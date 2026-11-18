import { useFonts } from "expo-font";
import { Figtree_400Regular } from "@expo-google-fonts/figtree/400Regular";
import { Figtree_600SemiBold } from "@expo-google-fonts/figtree/600SemiBold";
import { Figtree_700Bold } from "@expo-google-fonts/figtree/700Bold";

/** Loads Figtree, the poster's typeface. Returns true once the fonts are ready (or failed), so the app can render. */
export function useNomiFonts(): boolean {
  const [loaded, error] = useFonts({
    Figtree_400Regular,
    Figtree_600SemiBold,
    Figtree_700Bold,
  });
  return loaded || error != null;
}
