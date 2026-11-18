import { Text, View } from "react-native";

import { type Profile, profileSummary } from "@/storage/profile";
import { useTheme } from "@/theme";

/**
 * Who Nomi scores for, one answer per row, on a `bg.surface` screen.
 *
 * @example
 * ```tsx
 * <ProfileSummary profile={profile} />
 * ```
 */
export function ProfileSummary({ profile }: { profile: Profile }) {
  const { colors, radius, space, text } = useTheme();
  return (
    <View
      style={{
        backgroundColor: colors.bg.canvas,
        borderRadius: radius.md,
        padding: space[16],
        gap: space[12],
      }}
    >
      {profileSummary(profile).map((row) => (
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
  );
}
