import { Stack, useLocalSearchParams } from "expo-router";
import { ScrollView, StyleSheet, Text } from "react-native";

import { lookupFixture, type ScanResult } from "@/fixtures/scanFixtures";

// Plain text for now; styled components come from NOMI-027.
export default function Result() {
  const { barcode } = useLocalSearchParams<{ barcode: string }>();
  const result = lookupFixture(barcode ?? "");

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: TITLES[result.state] }} />
      <Body result={result} />
      <Text style={styles.barcode}>Barcode {result.barcode}</Text>
    </ScrollView>
  );
}

const TITLES: Record<ScanResult["state"], string> = {
  scored: "Result",
  preliminary: "Preliminary result",
  homeopathic: "Homeopathic",
  not_found: "Not found",
  invalid: "Couldn't read barcode",
};

function Body({ result }: { result: ScanResult }) {
  switch (result.state) {
    case "scored":
      return (
        <>
          <Text style={styles.name}>{result.product.brand_name}</Text>
          <Text>{result.product.generic_name}</Text>
          <Text style={styles.score}>{result.score}/100</Text>
          <Text>Tier: {result.tier}</Text>
        </>
      );
    case "preliminary":
      // docs/system-design.md 8.2: ingredients and label warnings with a "preliminary" badge.
      return (
        <>
          <Text style={styles.badge}>PRELIMINARY</Text>
          <Text style={styles.name}>{result.product.brand_name}</Text>
          <Text style={styles.heading}>Ingredients</Text>
          {result.ingredients.map((line) => (
            <Text key={line}>{line}</Text>
          ))}
          <Text style={styles.heading}>Warnings</Text>
          {result.warnings.map((line) => (
            <Text key={line}>{line}</Text>
          ))}
        </>
      );
    case "homeopathic":
      // docs/system-design.md 5.2: shown as "not evaluated by FDA" and not scored.
      return (
        <>
          <Text style={styles.name}>{result.product.brand_name}</Text>
          <Text>
            This homeopathic product has not been evaluated by the FDA, so Nomi does not score it.
          </Text>
        </>
      );
    case "not_found":
      return <Text>We don't have this product yet.</Text>;
    case "invalid":
      return (
        <Text>
          {result.reason === "not_ndc_barcode"
            ? "This barcode isn't a medicine."
            : "The barcode didn't read cleanly. Please try again."}
        </Text>
      );
  }
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 8 },
  name: { fontSize: 22, fontWeight: "600" },
  score: { fontSize: 48, fontWeight: "700", marginTop: 16 },
  badge: { fontWeight: "700", color: "#8a5a00" },
  heading: { fontWeight: "600", marginTop: 12 },
  barcode: { marginTop: 24, color: "#666" },
});
