import { Redirect, router, Stack } from "expo-router";
import { ScrollView, StyleSheet } from "react-native";

import { Button } from "@/components";

// Barcodes for the states the bundled fixture (pnpm db:fixture) can show. Homeopathic,
// out-of-scope and ambiguous products aren't in it; db.test.ts covers those.
const STATES = [
  { label: "Found", barcode: "350580449059" }, // Tylenol Extra Strength
  { label: "Found (EAN-13)", barcode: "0350580449059" },
  { label: "Not found", barcode: "399999004015" }, // Labeler 99999 isn't assigned by the FDA.
  { label: "Not a drug barcode", barcode: "4006381333931" },
  { label: "Misread", barcode: "350580449058" }, // Tylenol with its last digit off by one.
];

/**
 * Opens each result state as if its barcode had been scanned (NOMI-030).
 * Only in development builds, like /dev/gallery; a release build sends you to the camera.
 */
export default function DevMenu() {
  if (!__DEV__) return <Redirect href="/" />;

  return (
    // "automatic" starts the list below the see-through header instead of under it.
    <ScrollView contentInsetAdjustmentBehavior="automatic" contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: "Dev menu" }} />
      {STATES.map(({ label, barcode }) => (
        <Button
          key={label}
          type="secondary"
          label={label}
          onPress={() => router.push({ pathname: "/result", params: { barcode } })}
        />
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 12 },
});
