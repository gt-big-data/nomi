import * as Haptics from "expo-haptics";
import { useEffect, useState } from "react";
import { AppState, Button, Linking, StyleSheet, Text, View } from "react-native";
import { useCameraPermission } from "react-native-vision-camera";
import { CodeScanner } from "react-native-vision-camera-barcode-scanner";

export default function Scanner() {
  const { hasPermission, canRequestPermission, requestPermission } = useCameraPermission();
  const [digits, setDigits] = useState<string | null>(null);
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
        // Pause while a result is shown, so one box doesn't buzz repeatedly.
        isActive={appActive && !digits}
        barcodeFormats={["upc-a", "ean-13"]}
        onBarcodeScanned={(barcodes) => {
          const value = barcodes[0]?.rawValue;
          if (digits || !value) {
            return;
          }
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          setDigits(value);
        }}
        onError={(error) => console.error("Scanner error:", error)}
      />
      {digits && (
        <View style={styles.result}>
          <Text style={styles.digits}>{digits}</Text>
          <Button title="Scan again" onPress={() => setDigits(null)} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12 },
  result: {
    position: "absolute",
    bottom: 48,
    left: 24,
    right: 24,
    padding: 16,
    borderRadius: 12,
    backgroundColor: "white",
    alignItems: "center",
  },
  digits: { fontSize: 28, fontWeight: "600", marginBottom: 8 },
});
