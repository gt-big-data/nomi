import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Button } from "@/components";
import { Title } from "@/components/onboarding/Title";
import {
  conditionText,
  medicationTypeText,
  personaText,
  relationText,
  useProfile,
} from "@/storage/profile";
import { useTheme } from "@/theme";

/**
 * Done: what Nomi will account for, so people can check their answers before the first scan.
 */
export default function Done() {
  const { colors, radius, space, text } = useTheme();
  const insets = useSafeAreaInsets();
  const profile = useProfile();

  const rows: { label: string; value: string }[] = [
    { label: "For", value: relationText[profile.relation] },
    { label: "Scored as", value: personaText[profile.persona] },
    {
      label: "Health conditions",
      value: profile.conditions.map((c) => conditionText[c]).join(", ") || "None",
    },
    {
      label: "Medicines",
      value: profile.medication_types.map((m) => medicationTypeText[m]).join(", ") || "None",
    },
  ];

  return (
    <View style={[styles.fill, { backgroundColor: colors.bg.surface }]}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + space[48],
          paddingHorizontal: space[24],
          paddingBottom: space[24],
          gap: space[16],
        }}
      >
        <Title>You’re all set</Title>
        <Text style={[text("body"), { color: colors.text.secondary }]}>
          Scores will match these answers. They stay on this phone, and you can change them anytime
          in Profile.
        </Text>
        <View
          style={{
            backgroundColor: colors.bg.canvas,
            borderRadius: radius.md,
            padding: space[16],
            gap: space[12],
          }}
        >
          {rows.map((row) => (
            <View
              key={row.label}
              accessible
              accessibilityLabel={`${row.label}: ${row.value}`}
              style={{ gap: space[2] }}
            >
              <Text style={[text("label"), { color: colors.text.secondary }]}>{row.label}</Text>
              <Text style={[text("bodyStrong"), { color: colors.text.primary }]}>{row.value}</Text>
            </View>
          ))}
        </View>
      </ScrollView>

      <View
        style={{
          paddingHorizontal: space[16],
          paddingTop: space[12],
          paddingBottom: insets.bottom + space[16],
        }}
      >
        {/* Replace, so Back from the scanner doesn't return to onboarding. */}
        <Button label="Start scanning" onPress={() => router.replace("/")} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
});
