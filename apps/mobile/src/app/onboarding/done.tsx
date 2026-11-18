import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Button, ProfileSummary } from "@/components";
import { Title } from "@/components/onboarding/Title";
import { useSavedProfile } from "@/storage/activeProfile";
import { defaultProfile } from "@/storage/profile";
import { useTheme } from "@/theme";

/**
 * Done: what Nomi will account for, so people can check their answers before the first scan.
 */
export default function Done() {
  const { colors, space, text } = useTheme();
  const insets = useSafeAreaInsets();
  const profile = useSavedProfile() ?? defaultProfile;

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
          Here’s what you told us. Your answers stay on this phone.
        </Text>
        <ProfileSummary profile={profile} />
      </ScrollView>

      <View
        style={{
          paddingHorizontal: space[16],
          paddingTop: space[12],
          paddingBottom: insets.bottom + space[16],
        }}
      >
        {/* Goes back to the scanner already on the stack instead of opening a second one. */}
        <Button label="Start scanning" onPress={() => router.dismissTo("/")} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
});
