import { Redirect, router, Stack } from "expo-router";
import { ScrollView, StyleSheet } from "react-native";

import { Button } from "@/components";
import { space } from "@/theme";

/**
 * Development tools. The test barcodes moved to /enter, where the demo uses them.
 * Only in development builds; a release build sends you to the camera.
 */
export default function DevMenu() {
  if (!__DEV__) return <Redirect href="/" />;

  return (
    // "automatic" starts the list below the see-through header instead of under it.
    <ScrollView contentInsetAdjustmentBehavior="automatic" contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: "Dev menu" }} />
      <Button
        type="secondary"
        label="Component gallery"
        onPress={() => router.push("/dev/gallery")}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: space[24], gap: space[12] },
});
