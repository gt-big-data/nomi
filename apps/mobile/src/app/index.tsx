import * as Haptics from "expo-haptics";
import { Link, router, Stack, useFocusEffect } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { AppState, Linking, StyleSheet, Text, View } from "react-native";
import { useCameraPermission } from "react-native-vision-camera";
import { CodeScanner } from "react-native-vision-camera-barcode-scanner";

import { Button } from "@/components";
import { openDataset } from "@/lib/dataset";
import { minHeight, useTheme } from "@/theme";

export default function Scanner() {
  const { hasPermission, canRequestPermission, requestPermission } = useCameraPermission();
  const { colors, radius, space, text } = useTheme();
  // A ref, not state: the camera fires many times per second, and a ref changes instantly,
  // so a second frame can't open a second result screen.
  const scanned = useRef(false);
  const [appActive, setAppActive] = useState(AppState.currentState === "active");

  // Turn the camera off while the app is in the background.
  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) =>
      setAppActive(state === "active"),
    );
    return () => subscription.remove();
  }, []);

  // Open the dataset at launch, so the first scan doesn't wait for it.
  useEffect(() => {
    openDataset().catch((error) => console.error("Dataset error:", error));
  }, []);

  // Runs each time this screen comes back into view, e.g. after Back from a result.
  // Unlocks scanning and turns the camera back on; turns it off when another screen covers it.
  const [focused, setFocused] = useState(true);
  useFocusEffect(
    useCallback(() => {
      scanned.current = false;
      setFocused(true);
      return () => setFocused(false);
    }, []),
  );

  if (!hasPermission) {
    return (
      <View
        style={[
          styles.center,
          { backgroundColor: colors.bg.canvas, padding: space[24], gap: space[16] },
        ]}
      >
        <Stack.Screen options={SCREEN} />
        <Text style={[text("body"), styles.message, { color: colors.text.primary }]}>
          Nomi needs the camera to scan barcodes.
        </Text>
        {canRequestPermission ? (
          <Button label="Allow camera" onPress={requestPermission} />
        ) : (
          // Once the user has said no, the system won't ask again; only Settings can change it.
          <Button label="Open Settings" onPress={() => Linking.openSettings()} />
        )}
        {/* Without the camera (or on the iOS Simulator, which has none) you can still type it. */}
        <Button
          type="secondary"
          label="Type a barcode instead"
          onPress={() => router.push("/enter")}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Stack.Screen options={SCREEN} />
      <CodeScanner
        style={StyleSheet.absoluteFill}
        isActive={appActive && focused}
        barcodeFormats={["upc-a", "ean-13"]}
        onBarcodeScanned={(barcodes) => {
          const value = barcodes[0]?.rawValue;
          if (scanned.current || !value) {
            return;
          }
          scanned.current = true;
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          router.push({ pathname: "/result", params: { barcode: value } });
        }}
        onError={(error) => console.error("Scanner error:", error)}
      />
      <View style={[styles.actions, { bottom: space[48], gap: space[12] }]}>
        <Link
          href="/enter"
          style={[
            text("button"),
            styles.action,
            { paddingHorizontal: space[16], paddingVertical: space[12], borderRadius: radius.pill },
          ]}
        >
          Type a barcode
        </Link>
      </View>
    </View>
  );
}

// No header over the camera; "Scan" is what the back button says on the next screen.
const SCREEN = { title: "Scan", headerShown: false };

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: "stretch", justifyContent: "center" },
  message: { textAlign: "center" },
  actions: { position: "absolute", alignSelf: "center", flexDirection: "row" },
  // Fixed colors: it sits on the camera picture, not on a themed background.
  action: {
    minHeight: minHeight.chip,
    overflow: "hidden",
    backgroundColor: "white",
    color: "black",
  },
});
