import { Stack, useLocalSearchParams } from "expo-router";
import { ScrollView, StyleSheet, Text, type TextProps } from "react-native";

import { lookupFixture, type ScanResult } from "@/fixtures/scanFixtures";
import { useTheme } from "@/theme";

// Plain text for now; the NOMI-027 components (ScoreBadge, TierLabel...) can replace it later.
export default function Result() {
  const { barcode } = useLocalSearchParams<{ barcode: string }>();
  const result = lookupFixture(barcode ?? "");

  return (
    // "automatic" starts the content below the see-through header instead of under it.
    <ScrollView contentInsetAdjustmentBehavior="automatic" contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: title(result) }} />
      <Body result={result} />
      <Line style={styles.barcode}>Barcode {result.barcode}</Line>
    </ScrollView>
  );
}

function title(result: ScanResult): string {
  switch (result.state) {
    case "scored":
      return "Result";
    case "preliminary":
      return "Preliminary result";
    case "homeopathic":
      return "Homeopathic";
    case "not_found":
      return "Not found";
    case "invalid":
      return result.reason === "not_ndc_barcode" ? "Not a medicine" : "Couldn't read barcode";
  }
}

/** Text in the theme's color, so it's readable in light and dark mode. */
function Line({ style, ...props }: TextProps) {
  const { colors } = useTheme();
  return <Text style={[{ color: colors.text.primary }, style]} {...props} />;
}

function Body({ result }: { result: ScanResult }) {
  switch (result.state) {
    case "scored":
      return (
        <>
          <Line style={styles.name}>{result.product.brand_name}</Line>
          <Line>{result.product.generic_name}</Line>
          <Line style={styles.score}>{result.score}/100</Line>
          <Line>Tier: {result.tier}</Line>
        </>
      );
    case "preliminary":
      // docs/system-design.md 8.2: ingredients and label warnings with a "preliminary" badge.
      return (
        <>
          <Line style={styles.badge}>PRELIMINARY</Line>
          <Line style={styles.name}>{result.product.brand_name}</Line>
          <Line style={styles.heading}>Ingredients</Line>
          {result.ingredients.map((line) => (
            <Line key={line}>{line}</Line>
          ))}
          <Line style={styles.heading}>Warnings</Line>
          {result.warnings.map((line) => (
            <Line key={line}>{line}</Line>
          ))}
        </>
      );
    case "homeopathic":
      // docs/system-design.md 5.2: shown as "not evaluated by FDA" and not scored.
      return (
        <>
          <Line style={styles.name}>{result.product.brand_name}</Line>
          <Line>
            This homeopathic product has not been evaluated by the FDA, so Nomi does not score it.
          </Line>
        </>
      );
    case "not_found":
      return <Line>We don't have this product yet.</Line>;
    case "invalid":
      return (
        <Line>
          {result.reason === "not_ndc_barcode"
            ? "This barcode isn't a medicine."
            : "The barcode didn't read cleanly. Please try again."}
        </Line>
      );
  }
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 8 },
  name: { fontSize: 22, fontWeight: "600" },
  score: { fontSize: 48, fontWeight: "700", marginTop: 16 },
  badge: { fontWeight: "700" },
  heading: { fontWeight: "600", marginTop: 12 },
  barcode: { marginTop: 24, opacity: 0.6 },
});
