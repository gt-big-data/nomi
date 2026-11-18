import { router, Stack } from "expo-router";
import { ScrollView, Text, View } from "react-native";

import { ProductRow } from "@/components";
import { type CabinetItem, useCabinet } from "@/storage/cabinet";
import { useTheme } from "@/theme";

/** Every medicine scanned on this phone, with the ones this person takes at the top. */
export default function Cabinet() {
  const items = useCabinet();
  const { colors, space, text } = useTheme();
  const taking = items.filter((item) => item.taking);
  const scanned = items.filter((item) => !item.taking);

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={{ padding: space[24], gap: space[24] }}
    >
      <Stack.Screen options={{ title: "Home" }} />
      {items.length === 0 ? (
        <Text style={[text("body"), { color: colors.text.secondary }]}>
          Medicines you scan show up here.
        </Text>
      ) : (
        <>
          {taking.length > 0 && <Section title="Taking" items={taking} />}
          {scanned.length > 0 && <Section title="Scanned" items={scanned} />}
        </>
      )}
    </ScrollView>
  );
}

function Section({ title, items }: { title: string; items: CabinetItem[] }) {
  const { colors, space, text } = useTheme();
  return (
    <View style={{ gap: space[12] }}>
      <Text accessibilityRole="header" style={[text("titleSmall"), { color: colors.text.primary }]}>
        {title}
      </Text>
      {items.map((item) => (
        <ProductRow
          key={item.barcode}
          title={item.name}
          subtitle={[item.generic, when(item.seenAt)].filter(Boolean).join(" · ")}
          tier={item.tier}
          score={item.score}
          onPress={() => router.push({ pathname: "/result", params: { barcode: item.barcode } })}
        />
      ))}
    </View>
  );
}

/** "Today", "Yesterday" or a short date. */
function when(ms: number): string {
  const day = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
  const days = Math.round((day(new Date()) - day(new Date(ms))) / 86_400_000);
  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  return new Date(ms).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
