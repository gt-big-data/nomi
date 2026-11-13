import { router } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { Button, Icon, type IconName, Logo } from "@/components";
import { Title } from "@/components/onboarding/Title";
import { defaultProfile, saveProfile } from "@/storage/profile";
import { useIconScale, useTheme } from "@/theme";

const promises: { icon: IconName; text: string }[] = [
  { icon: "person", text: "Scores for who it’s for: you, a parent, a child" },
  { icon: "doc", text: "Every warning has a source" },
  { icon: "shield", text: "No account. Your answers stay on this phone." },
];

/** Size of the circles behind the promise icons, from the design. */
const PROMISE_CIRCLE = 40;

/** Welcome: what Nomi does and the privacy promise, before any questions. */
export default function Welcome() {
  const { colors, radius, space, text } = useTheme();
  const insets = useSafeAreaInsets();
  const iconScale = useIconScale();
  const circle = PROMISE_CIRCLE * iconScale;

  const next = () => {
    router.push("/onboarding/who");
  };
  const skip = () => {
    saveProfile(defaultProfile);
    router.replace("/");
  };

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
        <Logo />
        <Title>Know what’s in the box before you buy it.</Title>
        <Text style={[text("body"), { color: colors.text.secondary }]}>
          Scan any over-the-counter medicine for a 0–100 safety score, the risks in plain English,
          and a safer option.
        </Text>
        <View style={{ gap: space[12], paddingTop: space[8] }}>
          {promises.map((p) => (
            <View key={p.text} style={[styles.promise, { gap: space[12] }]}>
              <View
                style={[
                  styles.circle,
                  {
                    width: circle,
                    height: circle,
                    borderRadius: radius.pill,
                    backgroundColor: colors.brand.tint,
                  },
                ]}
              >
                <Icon name={p.icon} size="feature" scale={iconScale} color={colors.brand.text} />
              </View>
              <Text style={[text("body"), styles.shrink, { color: colors.text.primary }]}>
                {p.text}
              </Text>
            </View>
          ))}
        </View>
      </ScrollView>

      <View
        style={{
          paddingHorizontal: space[16],
          paddingTop: space[12],
          paddingBottom: insets.bottom + space[16],
          gap: space[8],
        }}
      >
        <Button label="Get started" onPress={next} />
        <Button
          type="ghost"
          label="Skip for now"
          onPress={skip}
          accessibilityHint="Scores for an adult 18 to 64. You can change this in Profile."
        />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  promise: { flexDirection: "row", alignItems: "center" },
  circle: { alignItems: "center", justifyContent: "center" },
  shrink: { flex: 1, minWidth: 0 },
});
