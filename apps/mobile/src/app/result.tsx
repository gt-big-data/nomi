import { useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

// Shows the scanned barcode for now; the five result states come next (NOMI-030).
export default function Result() {
  const { barcode } = useLocalSearchParams<{ barcode: string }>();

  return (
    <View style={styles.container}>
      <Text style={styles.digits}>{barcode}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  digits: { fontSize: 28, fontWeight: "600" },
});
