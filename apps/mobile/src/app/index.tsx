import { CameraView, useCameraPermissions } from "expo-camera";
import * as Haptics from "expo-haptics";
import { useState } from "react";
import { Button, StyleSheet, Text, View } from "react-native";

export default function Scanner() {
  const [permission, requestPermission] = useCameraPermissions();
  const [digits, setDigits] = useState<string | null>(null);

  // Permission status is still loading.
  if (!permission) {
    return <View />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.center}>
        <Text>Nomi needs the camera to scan barcodes.</Text>
        <Button title="Allow camera" onPress={requestPermission} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <CameraView
        style={StyleSheet.absoluteFill}
        barcodeScannerSettings={{ barcodeTypes: ["upc_a", "ean13"] }}
        // Stop scanning while a result is shown, so one box doesn't buzz repeatedly.
        onBarcodeScanned={
          digits
            ? undefined
            : ({ data }) => {
                Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
                setDigits(data);
              }
        }
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
