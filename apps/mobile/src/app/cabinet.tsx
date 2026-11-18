import { router, Stack } from "expo-router";
import { ScrollView, StyleSheet, Text, View } from "react-native";

import {
  BottomBar,
  Button,
  Icon,
  ListGroup,
  ListRow,
  ScoreBadge,
  useBottomBarSpace,
} from "@/components";
import { spokenLabel } from "@/components/Tappable";
import { ingredientName, productName } from "@/lib/displayName";
import { type CabinetItem, useCabinet } from "@/storage/cabinet";
import { productTierColors, productTierText, useTheme } from "@/theme";

/** Every medicine scanned on this phone, with the ones this person takes at the top. */
export default function Home() {
  const items = useCabinet();
  const { colors, space, text } = useTheme();
  const bottomSpace = useBottomBarSpace();
  const taking = items.filter((item) => item.taking);
  const scanned = items.filter((item) => !item.taking);

  return (
    <View style={[styles.flex, { backgroundColor: colors.bg.canvas }]}>
      <Stack.Screen options={{ title: "Home", headerTitle: "" }} />
      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        contentContainerStyle={[
          items.length === 0 && styles.grow,
          { paddingHorizontal: space[20], paddingBottom: bottomSpace, gap: space[32] },
        ]}
      >
        <View style={{ gap: space[4] }}>
          <Text
            accessibilityRole="header"
            style={[text("largeTitle"), { color: colors.text.primary }]}
          >
            Home
          </Text>
          {items.length > 0 && (
            <Text style={[text("subhead"), { color: colors.text.secondary }]}>
              {items.length} {items.length === 1 ? "medicine" : "medicines"} scanned on this phone
            </Text>
          )}
        </View>
        {items.length === 0 ? (
          <View style={[styles.empty, { gap: space[12] }]}>
            <View style={[styles.emptyIcon, { backgroundColor: colors.brand.tint }]}>
              <Icon name="scan" size="empty" color={colors.brand.text} />
            </View>
            <Text style={[text("verdict"), styles.center, { color: colors.text.primary }]}>
              Nothing scanned yet
            </Text>
            <Text style={[text("bodyLarge"), styles.center, { color: colors.text.secondary }]}>
              Medicines you scan show up here.
            </Text>
          </View>
        ) : (
          <>
            {taking.length > 0 && <Section title="Taking" items={taking} />}
            {scanned.length > 0 && <Section title="Scanned" items={scanned} />}
          </>
        )}
      </ScrollView>
      <BottomBar>
        <Button label="Scan a medicine" icon="scan" onPress={() => router.dismissTo("/")} />
      </BottomBar>
    </View>
  );
}

function Section({ title, items }: { title: string; items: CabinetItem[] }) {
  const { colors, text } = useTheme();
  return (
    <ListGroup title={title} inset={68}>
      {items.map((item) => {
        const c = productTierColors(colors, item.tier);
        const name = productName(item.name);
        const generic = item.generic ? ingredientName(item.generic) : undefined;
        const rest = [generic, when(item.seenAt)].filter(Boolean).join(" · ");
        return (
          <ListRow
            key={item.barcode}
            title={name}
            leading={<ScoreBadge tier={item.tier} score={item.score} size="small" decorative />}
            subtitle={
              <Text numberOfLines={1} style={[text("footnote"), { color: colors.text.secondary }]}>
                <Text style={[text("caption"), { color: c.text }]}>
                  {productTierText[item.tier]}
                </Text>
                {rest ? ` · ${rest}` : ""}
              </Text>
            }
            onPress={() => router.push({ pathname: "/result", params: { barcode: item.barcode } })}
            accessibilityLabel={spokenLabel([
              name,
              item.score === undefined || item.tier === "stop" || item.tier === "none"
                ? productTierText[item.tier]
                : `Score ${item.score}, ${productTierText[item.tier]}`,
              rest,
            ])}
            accessibilityHint="Opens the result"
          />
        );
      })}
    </ListGroup>
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

const styles = StyleSheet.create({
  flex: { flex: 1 },
  grow: { flexGrow: 1 },
  center: { textAlign: "center" },
  empty: { flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 12 },
  emptyIcon: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: "center",
    justifyContent: "center",
  },
});
