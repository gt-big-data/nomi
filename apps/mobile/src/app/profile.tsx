import { router, Stack } from "expo-router";
import { ScrollView, Text } from "react-native";

import { Button, ProfileSummary } from "@/components";
import { useSavedProfile } from "@/storage/activeProfile";
import { defaultProfile } from "@/storage/profile";
import { useTheme } from "@/theme";

/** Who scores are for, with ways to change it, type a barcode or get back to the camera. */
export default function ProfileScreen() {
  const { colors, space, text } = useTheme();
  const profile = useSavedProfile() ?? defaultProfile;

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      style={{ backgroundColor: colors.bg.surface }}
      contentContainerStyle={{ padding: space[24], gap: space[16] }}
    >
      <Stack.Screen options={{ title: "Profile" }} />
      <Text style={[text("body"), { color: colors.text.secondary }]}>
        Nomi scores medicines for this person once every active ingredient is rated. Your answers
        stay on this phone.
      </Text>
      <ProfileSummary profile={profile} />
      <Button label="Scan a medicine" onPress={() => router.dismissTo("/")} />
      <Button
        type="secondary"
        label="Answer again"
        onPress={() => router.push("/onboarding")}
        accessibilityHint="Asks the profile questions again"
      />
      <Button type="ghost" label="Type a barcode" onPress={() => router.push("/enter")} />
      {__DEV__ && <Button type="ghost" label="Dev menu" onPress={() => router.push("/dev")} />}
    </ScrollView>
  );
}
