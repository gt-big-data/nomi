import { router, Stack } from "expo-router";
import { ScrollView, Text } from "react-native";

import { Button, ListGroup, ListRow } from "@/components";
import { useSavedProfile } from "@/storage/activeProfile";
import { defaultProfile, profileSummary } from "@/storage/profile";
import { useTheme } from "@/theme";

/** Who scores are for, with ways to change it or type a barcode. */
export default function ProfileScreen() {
  const { colors, space, text } = useTheme();
  const profile = useSavedProfile() ?? defaultProfile;

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      style={{ backgroundColor: colors.bg.canvas }}
      contentContainerStyle={{
        paddingHorizontal: space[20],
        paddingBottom: space[48],
        gap: space[32],
      }}
    >
      <Stack.Screen options={{ title: "Profile", headerTitle: "" }} />
      <Text accessibilityRole="header" style={[text("largeTitle"), { color: colors.text.primary }]}>
        Profile
      </Text>
      <ListGroup
        title="Your answers"
        footer="Your answers stay on this phone. Nomi scores a medicine for this person once every active ingredient is rated."
      >
        {profileSummary(profile).map((row) => (
          <ListRow
            key={row.label}
            title={row.label}
            trailing={
              <Text
                numberOfLines={2}
                style={[
                  text("bodyLarge"),
                  { color: colors.text.secondary, maxWidth: "55%", textAlign: "right" },
                ]}
              >
                {row.value}
              </Text>
            }
            accessibilityLabel={`${row.label}: ${row.value}`}
          />
        ))}
        <ListRow
          title="Answer the questions again"
          onPress={() => router.push("/onboarding")}
          accessibilityLabel="Answer the questions again"
          accessibilityHint="Asks the profile questions again"
        />
      </ListGroup>
      <ListGroup>
        <ListRow
          title="Type a barcode"
          onPress={() => router.push("/enter")}
          accessibilityLabel="Type a barcode"
        />
      </ListGroup>
      {__DEV__ && <Button type="ghost" label="Dev menu" onPress={() => router.push("/dev")} />}
    </ScrollView>
  );
}
