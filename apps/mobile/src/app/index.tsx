import * as Haptics from "expo-haptics";
import { useState } from "react";
import { Button, StyleSheet, Text, View } from "react-native";
import { useCameraPermission } from "react-native-vision-camera";
import { CodeScanner } from "react-native-vision-camera-barcode-scanner";

export default function Scanner() {
  const { hasPermission, requestPermission } = useCameraPermission();
  const [digits, setDigits] = useState<string | null>(null);

  if (!hasPermission) {
    return (
      <View style={styles.center}>
        <Text>Nomi needs the camera to scan barcodes.</Text>
        <Button title="Allow camera" onPress={requestPermission} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CodeScanner
        style={StyleSheet.absoluteFill}
        isActive={true}
        barcodeFormats={["upc-a", "ean-13"]}
        onBarcodeScanned={(barcodes) => {
          const value = barcodes[0]?.rawValue;
          // Ignore scans while a result is shown, so one box doesn't buzz repeatedly.
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
