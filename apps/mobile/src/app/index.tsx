import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { AppState, Button, Linking, StyleSheet, Text, View } from "react-native";
import { useCameraPermission } from "react-native-vision-camera";
import { CodeScanner } from "react-native-vision-camera-barcode-scanner";

export default function Scanner() {
  const { hasPermission, canRequestPermission, requestPermission } = useCameraPermission();
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

  if (!hasPermission) {
    return (
      <View style={styles.center}>
        <Text>Nomi needs the camera to scan barcodes.</Text>
        {canRequestPermission ? (
          <Button title="Allow camera" onPress={requestPermission} />
        ) : (
          // Once the user has said no, the system won't ask again; only Settings can change it.
          <Button title="Open Settings" onPress={() => Linking.openSettings()} />
        )}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CodeScanner
        style={StyleSheet.absoluteFill}
        isActive={appActive}
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12 },
});
