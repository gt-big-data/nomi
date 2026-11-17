import * as Haptics from "expo-haptics";
import { useEffect, useState } from "react";
import { AppState, Button, Linking, StyleSheet, Text, View } from "react-native";
import { useCameraPermission } from "react-native-vision-camera";
import { CodeScanner } from "react-native-vision-camera-barcode-scanner";

import { openDataset } from "@/lib/dataset";
import { lookupBarcode, strengthText, type Lookup, type Product } from "@/lib/db";

interface Scan {
  digits: string;
  // Missing while the lookup runs.
  lookup?: Lookup | "error";
}

// What to say when there is no single product to show. Nothing here is ever scored.
const MESSAGES: Record<Exclude<Lookup, { product: Product }>["status"] | "error", string> = {
  invalid_format: "Couldn't read that barcode. Try again.",
  bad_check_digit: "Couldn't read that barcode. Try again.",
  not_ndc_barcode: "We can't look up this barcode yet.",
  not_found: "We don't have this product yet.",
  ambiguous_ndc: "This barcode matches more than one product.",
  error: "Couldn't open the product database.",
};

// Found but not yet checked by a second person: shown with a "preliminary" badge (system design 8.2).
const REVIEWED = new Set(["sampled_ok", "pharmacist_reviewed"]);

function Result({ lookup }: { lookup: Lookup | "error" }) {
  if (lookup === "error" || !("product" in lookup)) {
    return (
      <Text style={styles.message}>{MESSAGES[lookup === "error" ? lookup : lookup.status]}</Text>
    );
  }
  const { product } = lookup;
  return (
    <View style={styles.product}>
      <Text style={styles.brand}>{product.brand ?? product.ndc11}</Text>
      {product.generic ? <Text>{product.generic}</Text> : null}
      {product.ingredients.map((ingredient) => (
        <Text key={ingredient.unii}>
          {ingredient.name} {strengthText(ingredient)}
        </Text>
      ))}
      {lookup.status === "homeopathic" && (
        <Text style={styles.note}>
          Homeopathic: not evaluated by FDA, so Nomi doesn't score it.
        </Text>
      )}
      {lookup.status === "out_of_scope" && (
        <Text style={styles.note}>Nomi doesn't score this kind of product.</Text>
      )}
      {!REVIEWED.has(product.reviewStatus ?? "") && <Text style={styles.note}>Preliminary</Text>}
    </View>
  );
}

export default function Scanner() {
  const { hasPermission, canRequestPermission, requestPermission } = useCameraPermission();
  const [scan, setScan] = useState<Scan | null>(null);
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
        isActive={appActive && !scan}
        barcodeFormats={["upc-a", "ean-13"]}
        onBarcodeScanned={(barcodes) => {
          const value = barcodes[0]?.rawValue;
          if (scan || !value) {
            return;
          }
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          const current: Scan = { digits: value };
          setScan(current);
          openDataset()
            .then((db) => lookupBarcode(value, db))
            .catch((error): "error" => {
              console.error("Lookup error:", error);
              return "error";
            })
            // Ignore the answer if the user has already moved on to another scan.
            .then((lookup) =>
              setScan((shown) => (shown === current ? { ...current, lookup } : shown)),
            );
        }}
        onError={(error) => console.error("Scanner error:", error)}
      />
      {scan && (
        <View style={styles.result}>
          <Text style={styles.digits}>{scan.digits}</Text>
          {scan.lookup && <Result lookup={scan.lookup} />}
          <Button title="Scan again" onPress={() => setScan(null)} />
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
  digits: { fontSize: 15, color: "gray", marginBottom: 8 },
  product: { alignItems: "center", gap: 4, marginBottom: 8 },
  brand: { fontSize: 22, fontWeight: "600" },
  message: { fontSize: 17, marginBottom: 8, textAlign: "center" },
  note: { color: "gray", textAlign: "center" },
});
