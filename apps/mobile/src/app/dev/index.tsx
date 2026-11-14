import { Redirect, router, Stack } from "expo-router";
import { ScrollView, StyleSheet } from "react-native";

import { Button } from "@/components";
import { FIXTURE_BARCODES } from "@/fixtures/scanFixtures";

const STATES = [
  { label: "Scored", barcode: FIXTURE_BARCODES.scored },
  { label: "Preliminary", barcode: FIXTURE_BARCODES.preliminary },
  { label: "Homeopathic", barcode: FIXTURE_BARCODES.homeopathic },
  { label: "Not found", barcode: FIXTURE_BARCODES.not_found },
  { label: "Invalid", barcode: FIXTURE_BARCODES.invalid },
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
