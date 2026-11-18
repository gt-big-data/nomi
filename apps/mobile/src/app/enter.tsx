import { router, Stack } from "expo-router";
import { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { Button, ListGroup, ListRow } from "@/components";
import { spokenLabel } from "@/components/Tappable";
import { REFERENCE_BARCODES, STATE_BARCODES } from "@/lib/testBarcodes";
import { minHeight, useTheme } from "@/theme";

function open(barcode: string) {
  router.push({ pathname: "/result", params: { barcode } });
}

/**
 * Type the digits under a barcode, or pick a reference product (NOMI-063). For a box the camera
 * can't read, and for the iOS Simulator, which has no camera.
 */
export default function EnterBarcode() {
  const [digits, setDigits] = useState("");
  const { colors, space, text } = useTheme();
  const ready = digits.length >= 12;

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="on-drag"
      style={{ backgroundColor: colors.bg.canvas }}
      contentContainerStyle={{
        paddingHorizontal: space[20],
        paddingBottom: space[48],
        gap: space[32],
      }}
    >
      <Stack.Screen options={{ title: "Type a barcode", headerTitle: "" }} />
      <Text accessibilityRole="header" style={[text("largeTitle"), { color: colors.text.primary }]}>
        Type a barcode
      </Text>
      <View style={{ gap: space[12] }}>
        <TextInput
          value={digits}
          onChangeText={(value) => setDigits(value.replace(/\D/g, "").slice(0, 13))}
          keyboardType="number-pad"
          placeholder="e.g. 350580449059"
          placeholderTextColor={colors.text.tertiary}
          selectionColor={colors.brand.primary}
          accessibilityLabel="Barcode numbers"
          accessibilityHint="Type 12 or 13 numbers. A Look it up button appears below."
          style={[
            text("bodyLarge"),
            styles.input,
            {
              color: colors.text.primary,
              backgroundColor: colors.bg.surface,
              borderRadius: 12,
              paddingHorizontal: space[16],
            },
          ]}
        />
        <Text
          style={[text("footnote"), { color: colors.text.tertiary, paddingHorizontal: space[16] }]}
        >
          The 12 or 13 numbers under the barcode
        </Text>
        {/* Button has no disabled state, so it only appears once there are enough digits. */}
        {ready && <Button label="Look it up" onPress={() => open(digits)} />}
      </View>

      <Section title="Reference products" items={REFERENCE_BARCODES} />
      {/* Made-up and misread barcodes, for testing the other states. Not in release builds. */}
      {__DEV__ && <Section title="Other results" items={STATE_BARCODES} />}
    </ScrollView>
  );
}

function Section({
  title,
  items,
}: {
  title: string;
  items: readonly { name: string; barcode: string }[];
}) {
  return (
    <ListGroup title={title}>
      {items.map(({ name, barcode }) => (
        <ListRow
          key={barcode}
          title={name}
          subtitle={barcode}
          onPress={() => open(barcode)}
          accessibilityLabel={spokenLabel([name, `barcode ${barcode}`])}
          accessibilityHint="Opens the result"
        />
      ))}
    </ListGroup>
  );
}

const styles = StyleSheet.create({
  input: { minHeight: minHeight.button, fontVariant: ["tabular-nums"], letterSpacing: 1 },
});
