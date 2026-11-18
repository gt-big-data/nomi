import { router, Stack } from "expo-router";
import { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { Button } from "@/components";
import { spokenLabel, Tappable } from "@/components/Tappable";
import { REFERENCE_BARCODES, STATE_BARCODES } from "@/lib/testBarcodes";
import { borderWidth, minHeight, useTheme } from "@/theme";

function open(barcode: string) {
  router.push({ pathname: "/result", params: { barcode } });
}

/**
 * Type the digits under a barcode, or pick a reference product (NOMI-063). For a box the camera
 * can't read, and for the iOS Simulator, which has no camera.
 */
export default function EnterBarcode() {
  const [digits, setDigits] = useState("");
  const { colors, radius, space, text } = useTheme();
  const ready = digits.length >= 12;

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      keyboardShouldPersistTaps="handled"
      keyboardDismissMode="on-drag"
      contentContainerStyle={{ padding: space[24], gap: space[24] }}
    >
      <Stack.Screen options={{ title: "Type a barcode" }} />
      <View style={{ gap: space[12] }}>
        <Text style={[text("bodyStrong"), { color: colors.text.primary }]}>
          The 12 or 13 numbers under the barcode
        </Text>
        <TextInput
          value={digits}
          onChangeText={(value) => setDigits(value.replace(/\D/g, "").slice(0, 13))}
          keyboardType="number-pad"
          placeholder="e.g. 350580449059"
          placeholderTextColor={colors.text.secondary}
          accessibilityLabel="Barcode numbers"
          accessibilityHint="Type 12 or 13 numbers. A Look it up button appears below."
          style={[
            text("body"),
            styles.input,
            {
              color: colors.text.primary,
              backgroundColor: colors.bg.surface,
              borderColor: colors.border.subtle,
              borderRadius: radius.sm,
              paddingHorizontal: space[16],
            },
          ]}
        />
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
  const { colors, radius, space, text } = useTheme();
  return (
    <View style={{ gap: space[8] }}>
      <Text accessibilityRole="header" style={[text("titleSmall"), { color: colors.text.primary }]}>
        {title}
      </Text>
      <View
        style={[
          styles.list,
          {
            backgroundColor: colors.bg.surface,
            borderColor: colors.border.subtle,
            borderRadius: radius.md,
          },
        ]}
      >
        {items.map(({ name, barcode }, index) => (
          <Tappable
            key={barcode}
            onPress={() => open(barcode)}
            accessibilityLabel={spokenLabel([name, `barcode ${barcode}`])}
            accessibilityHint="Opens the result"
            style={[
              styles.item,
              {
                padding: space[16],
                gap: space[2],
                borderTopColor: colors.border.subtle,
                borderTopWidth: index === 0 ? 0 : StyleSheet.hairlineWidth,
              },
            ]}
          >
            <Text style={[text("bodyStrong"), { color: colors.text.primary }]}>{name}</Text>
            <Text style={[text("footnote"), { color: colors.text.secondary }]}>{barcode}</Text>
          </Tappable>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  input: { minHeight: minHeight.button, borderWidth: borderWidth.control },
  list: { borderWidth: borderWidth.card, overflow: "hidden" },
  item: { minHeight: minHeight.chip, justifyContent: "center" },
});
