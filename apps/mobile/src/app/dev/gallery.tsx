import { type ReactNode, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Stack, useLocalSearchParams } from "expo-router";

import {
  AlertBanner,
  Button,
  type ButtonType,
  CitationChip,
  type CitationSource,
  citationSourceText,
  OptionChip,
  ProductRow,
  RiskFactorRow,
  ScoreBadge,
  TierLabel,
} from "@/components";
import { type ColorScheme, ThemeProvider, type UiTier, useNomiFonts, useTheme } from "@/theme";

/**
 * Shows every core component in every state.
 * Open /dev/gallery, or /dev/gallery?scheme=dark&scale=2 to start in dark mode at 200% text.
 */
export default function GalleryScreen() {
  const params = useLocalSearchParams<{ scheme?: string; scale?: string }>();
  const fontsReady = useNomiFonts();
  // What the link asks for, until someone taps a chip.
  const fromLink: SchemeChoice =
    params.scheme === "light" || params.scheme === "dark" ? params.scheme : "system";
  const [picked, setScheme] = useState<SchemeChoice | null>(null);
  const [pickedScale, setScale] = useState<number | null>(null);
  const scheme = picked ?? fromLink;
  const scale = pickedScale ?? (scales.includes(Number(params.scale)) ? Number(params.scale) : 1);

  return (
    <ThemeProvider scheme={scheme === "system" ? undefined : scheme} textScale={scale}>
      {/* The gallery leaves room for the status bar itself, so it has no header. */}
      <Stack.Screen options={{ headerShown: false }} />
      {fontsReady ? (
        <Gallery scheme={scheme} onScheme={setScheme} scale={scale} onScale={setScale} />
      ) : (
        <Loading />
      )}
    </ThemeProvider>
  );
}

type SchemeChoice = ColorScheme | "system";
const schemes: { value: SchemeChoice; label: string }[] = [
  { value: "system", label: "System" },
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
];
/** 300% is about the largest iOS accessibility text size. */
const scales = [1, 1.5, 2, 3];

const scoreExamples: { tier: UiTier; score: number }[] = [
  { tier: "low", score: 84 },
  { tier: "moderate", score: 52 },
  { tier: "high", score: 28 },
  { tier: "stop", score: 62 },
  { tier: "none", score: 0 },
];

const buttonExamples: { type: ButtonType; label: string }[] = [
  { type: "primary", label: "See safer alternative" },
  { type: "secondary", label: "Add to Mom’s cabinet" },
  { type: "outline", label: "Check it for someone else" },
  { type: "ghost", label: "Not now" },
  { type: "success", label: "Add Claritin to Mom’s cabinet" },
  { type: "danger", label: "Delete all my data" },
];

const ageGroups = ["Under 2", "2–5", "6–11", "12–17", "18–64", "65+"];
const conditions = ["High blood pressure", "Glaucoma", "Asthma", "Kidney disease"];

const products: { tier: UiTier; score: number; title: string; subtitle: string }[] = [
  { tier: "low", score: 84, title: "Claritin", subtitle: "Loratadine 10 mg · For Mom" },
  {
    tier: "moderate",
    score: 52,
    title: "Sudafed Sinus Congestion",
    subtitle: "For Mom · Yesterday",
  },
  { tier: "high", score: 28, title: "Benadryl Allergy", subtitle: "For Mom · 2:14 PM" },
  { tier: "stop", score: 62, title: "Children’s Benadryl Allergy", subtitle: "For Lily · Oct 20" },
  { tier: "none", score: 0, title: "Homeopathic cold remedy", subtitle: "For Me · Oct 18" },
];

function Gallery({
  scheme,
  onScheme,
  scale,
  onScale,
}: {
  scheme: SchemeChoice;
  onScheme: (s: SchemeChoice) => void;
  scale: number;
  onScale: (s: number) => void;
}) {
  const { colors, space, text } = useTheme();
  const insets = useSafeAreaInsets();
  const [age, setAge] = useState("65+");
  const [picked, setPicked] = useState<string[]>(["High blood pressure"]);
  const noop = () => {};

  return (
    <ScrollView
      style={{ backgroundColor: colors.bg.canvas }}
      contentContainerStyle={[
        styles.page,
        {
          padding: space[16],
          paddingTop: insets.top + space[16],
          paddingBottom: insets.bottom + space[48],
          gap: space[32],
        },
      ]}
    >
      <View style={{ gap: space[8] }}>
        <Text
          accessibilityRole="header"
          style={[text("titleLarge"), { color: colors.text.primary }]}
        >
          Component gallery
        </Text>
        <Text style={[text("callout"), { color: colors.text.secondary }]}>
          Shows every core component in every state.
        </Text>
        <Group label="Theme">
          {schemes.map((s) => (
            <OptionChip
              key={s.value}
              mode="single"
              label={s.label}
              selected={scheme === s.value}
              onPress={() => onScheme(s.value)}
            />
          ))}
        </Group>
        <Group label="Text size">
          {scales.map((s) => (
            <OptionChip
              key={s}
              mode="single"
              label={`${s * 100}%`}
              selected={scale === s}
              onPress={() => onScale(s)}
            />
          ))}
        </Group>
        <Text style={[text("footnote"), { color: colors.text.secondary }]}>
          Text size previews large text on the web. On a phone, also try the system text size
          setting.
        </Text>
      </View>

      <Section
        title="Score badge"
        about="Large is the ring on the result screen; small is the dot in lists. Stop hides the number; None has no score. Always shown with a tier label."
      >
        <Wrap>
          {scoreExamples.map((e) => (
            <View key={e.tier} style={[styles.center, { gap: space[8] }]}>
              <ScoreBadge tier={e.tier} score={e.score} size="large" />
              <TierLabel tier={e.tier} />
            </View>
          ))}
        </Wrap>
        <Wrap>
          {scoreExamples.map((e) => (
            <ScoreBadge key={e.tier} tier={e.tier} score={e.score} size="small" />
          ))}
        </Wrap>
      </Section>

      <Section
        title="Tier label"
        about="The tier word with its own icon shape, so tiers never depend on color alone."
      >
        <Wrap>
          {scoreExamples.map((e) => (
            <TierLabel key={e.tier} tier={e.tier} />
          ))}
        </Wrap>
      </Section>

      <Section title="Citation chip" about="One per citation.source value. Tap opens the source.">
        <Wrap>
          {(Object.keys(citationSourceText) as CitationSource[]).map((source) => (
            <CitationChip key={source} source={source} onPress={noop} />
          ))}
        </Wrap>
      </Section>

      <Section
        title="Button"
        about="One primary per screen. The gem marks an action that needs Premium."
      >
        {buttonExamples.map((b) => (
          <Button key={b.type} type={b.type} label={b.label} onPress={noop} />
        ))}
        <Button type="primary" gem label="See Premium" onPress={noop} />
        <Button type="secondary" gem label="Add to cabinet" onPress={noop} />
      </Section>

      <Section
        title="Option chip"
        about="Onboarding answers and filters. Tap to try: one choice for age, any number for conditions."
      >
        <Wrap>
          {ageGroups.map((a) => (
            <OptionChip
              key={a}
              mode="single"
              label={a}
              selected={age === a}
              onPress={() => setAge(a)}
            />
          ))}
        </Wrap>
        <Wrap>
          {conditions.map((c) => (
            <OptionChip
              key={c}
              label={c}
              selected={picked.includes(c)}
              onPress={() =>
                setPicked((p) => (p.includes(c) ? p.filter((x) => x !== c) : [...p, c]))
              }
            />
          ))}
        </Wrap>
      </Section>

      <Section
        title="Risk factor row"
        about="One per contributions[] item, largest first. High is 15+ points, Moderate 5–14, Low under 5."
      >
        <RiskFactorRow
          factor="Memory & thinking"
          detail="Strong anticholinergic (ACB score 3)"
          points={38}
          maxPoints={38}
          onPress={noop}
        />
        <RiskFactorRow
          factor="Drowsiness & falls"
          detail="Sedating; next-day drowsiness"
          points={14}
          maxPoints={38}
          onPress={noop}
        />
        <RiskFactorRow
          factor="Newer options work as well"
          detail="Older antihistamine"
          points={4}
          maxPoints={38}
          onPress={noop}
        />
      </Section>

      <Section title="Product row" about="History, Cabinet, Search and Compare. One per tier.">
        {products.map((p) => (
          <ProductRow
            key={p.tier}
            tier={p.tier}
            score={p.score}
            title={p.title}
            subtitle={p.subtitle}
            onPress={noop}
          />
        ))}
      </Section>

      <Section
        title="Alert banner"
        about="The type follows how serious it is, not just that it happened."
      >
        <AlertBanner
          type="danger"
          title="Same ingredient as ZzzQuil"
          body="In Mom’s cabinet · tap to see why"
          onPress={noop}
        />
        <AlertBanner
          type="warning"
          title="Preliminary score"
          body="A pharmacist hasn’t checked this product yet."
        />
        <AlertBanner
          type="info"
          title="Ask your pharmacist"
          body="We didn’t find a safer option for Mom."
        />
        <AlertBanner
          type="success"
          title="No interactions in Mom’s cabinet"
          body="Checked 4 medicines."
        />
      </Section>
    </ScrollView>
  );
}

function Section({
  title,
  about,
  children,
}: {
  title: string;
  about: string;
  children: ReactNode;
}) {
  const { colors, space, text } = useTheme();
  return (
    <View style={{ gap: space[12] }}>
      <View style={{ gap: space[4] }}>
        <Text
          accessibilityRole="header"
          style={[text("titleSmall"), { color: colors.text.primary }]}
        >
          {title}
        </Text>
        <Text style={[text("footnote"), { color: colors.text.secondary }]}>{about}</Text>
      </View>
      {children}
    </View>
  );
}

function Group({ label, children }: { label: string; children: ReactNode }) {
  const { colors, space, text } = useTheme();
  return (
    <View accessibilityRole="radiogroup" accessibilityLabel={label} style={{ gap: space[4] }}>
      <Text style={[text("label"), { color: colors.text.secondary }]}>{label}</Text>
      <Wrap>{children}</Wrap>
    </View>
  );
}

function Wrap({ children }: { children: ReactNode }) {
  const { space } = useTheme();
  return <View style={[styles.wrap, { gap: space[8] }]}>{children}</View>;
}

function Loading() {
  const { colors } = useTheme();
  return (
    <View style={[styles.loading, { backgroundColor: colors.bg.canvas }]}>
      <ActivityIndicator color={colors.brand.primary} />
    </View>
  );
}

const styles = StyleSheet.create({
  page: { width: "100%", maxWidth: 640, alignSelf: "center" },
  wrap: { flexDirection: "row", flexWrap: "wrap", alignItems: "center" },
  center: { alignItems: "center" },
  loading: { flex: 1, alignItems: "center", justifyContent: "center" },
});
