import { router, Stack, useLocalSearchParams } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";

import {
  AlertBanner,
  Button,
  OptionChip,
  RiskFactorRow,
  ScoreBadge,
  TierLabel,
} from "@/components";
import { openDataset } from "@/lib/dataset";
import { lookupBarcode, strengthText, type Lookup, type Product } from "@/lib/db";
import { DEMO_PROFILES, setDemoProfile, useDemoProfile } from "@/lib/demoProfiles";
import { REFERENCE_SCORES } from "@/lib/referenceScoreData";
import {
  findScore,
  profileNotes,
  recordTier,
  riskRows,
  type ScoreRecord,
} from "@/lib/referenceScores";
import { type ProductTier, useTheme } from "@/theme";

type Loaded = Lookup | "error";

/** Looks the barcode up in the bundled dataset. undefined while it runs. */
function useLookup(barcode: string): Loaded | undefined {
  const [result, setResult] = useState<{ barcode: string; lookup: Loaded }>();
  useEffect(() => {
    let current = true;
    openDataset()
      .then((db) => lookupBarcode(barcode, db))
      .catch((error): "error" => {
        console.error("Lookup error:", error);
        return "error";
      })
      .then((lookup) => {
        if (current) setResult({ barcode, lookup });
      });
    return () => {
      current = false;
    };
  }, [barcode]);
  // A result for an earlier barcode is never shown for this one.
  return result?.barcode === barcode ? result.lookup : undefined;
}

export default function Result() {
  const { barcode = "" } = useLocalSearchParams<{ barcode: string }>();
  const lookup = useLookup(barcode);
  const { colors, space, text } = useTheme();

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={{ padding: space[24], gap: space[24] }}
    >
      <Stack.Screen options={{ title: lookup ? title(lookup) : "Looking it up" }} />
      {lookup === undefined ? (
        <ActivityIndicator style={{ marginTop: space[48] }} accessibilityLabel="Looking it up" />
      ) : lookup !== "error" && "product" in lookup ? (
        <ProductResult lookup={lookup} />
      ) : (
        <Message lookup={lookup} />
      )}
      <Text
        accessibilityLabel={`Barcode ${barcode.split("").join(" ")}`}
        style={[text("footnote"), { color: colors.text.secondary }]}
      >
        Barcode {barcode}
      </Text>
    </ScrollView>
  );
}

type Found = Extract<Lookup, { product: Product }>;
type NotFound = Exclude<Loaded, Found>;

function title(lookup: Loaded): string {
  if (lookup === "error") return "Something went wrong";
  switch (lookup.status) {
    case "resolved":
    case "homeopathic":
    case "out_of_scope":
      return "Result";
    case "not_found":
    case "ambiguous_ndc":
      return "Not found";
    case "not_ndc_barcode":
      return "Not a medicine";
    case "invalid_format":
    case "bad_check_digit":
      return "Couldn't read barcode";
  }
}

const MESSAGES: Record<Exclude<NotFound, "error">["status"] | "error", string> = {
  invalid_format: "Those numbers aren't a whole barcode. Check them and try again.",
  bad_check_digit: "One of the numbers is off. Scan it again or check the numbers.",
  not_ndc_barcode: "This barcode isn't on a medicine we can look up.",
  not_found: "We don't have this product yet.",
  ambiguous_ndc: "This barcode matches more than one product, so we won't guess which one it is.",
  error: "Couldn't open the product database. Close Nomi and open it again.",
};

function Message({ lookup }: { lookup: NotFound }) {
  const { colors, space, text } = useTheme();
  return (
    <View style={{ gap: space[24] }}>
      <Text style={[text("body"), { color: colors.text.primary }]}>
        {MESSAGES[lookup === "error" ? lookup : lookup.status]}
      </Text>
      <Button label="Try another barcode" onPress={goBack} />
    </View>
  );
}

/** Back to the camera or the barcode list, whichever opened this. A deep link has neither. */
function goBack() {
  if (router.canGoBack()) router.back();
  else router.replace("/");
}

function ProductResult({ lookup }: { lookup: Found }) {
  const { product } = lookup;
  const profile = useDemoProfile();
  const { colors, space, text } = useTheme();
  // Only an in-scope product that resolved to one package may show a score.
  const scorable =
    lookup.status === "resolved" && REFERENCE_SCORES.some((r) => r.ndc11 === product.ndc11);
  const record = scorable ? findScore(REFERENCE_SCORES, product.ndc11, profile) : undefined;
  const tier: ProductTier = record ? recordTier(record) : "none";

  return (
    <>
      <View style={{ gap: space[4] }}>
        <Text
          accessibilityRole="header"
          style={[text("titleLarge"), { color: colors.text.primary }]}
        >
          {product.brand ?? product.ndc11}
        </Text>
        {product.generic ? (
          <Text style={[text("body"), { color: colors.text.secondary }]}>{product.generic}</Text>
        ) : null}
      </View>

      {/* The verdict and who it's for, together (docs/design/score-visualization.md). */}
      <View style={[styles.center, { gap: space[12] }]}>
        <ScoreBadge tier={tier} score={record?.score} />
        <TierLabel tier={tier} align="center" />
        {record && (
          <Text style={[text("footnote"), { color: colors.text.secondary }]}>Draft score</Text>
        )}
        {scorable && <ProfileSwitcher />}
      </View>

      {record ? (
        <ScoreDetails record={record} />
      ) : (
        <AlertBanner
          type="info"
          title={unscoredTitle(lookup, scorable)}
          body={unscoredBody(lookup, scorable)}
        />
      )}

      <View style={{ gap: space[8] }}>
        <Text
          accessibilityRole="header"
          style={[text("titleSmall"), { color: colors.text.primary }]}
        >
          Active ingredients
        </Text>
        {product.ingredients.length === 0 ? (
          <Text style={[text("body"), { color: colors.text.secondary }]}>None listed.</Text>
        ) : (
          product.ingredients.map((ingredient) => (
            <Text key={ingredient.unii} style={[text("body"), { color: colors.text.primary }]}>
              {ingredient.name} {strengthText(ingredient)}
            </Text>
          ))
        )}
      </View>
    </>
  );
}

function unscoredTitle(lookup: Found, scorable: boolean): string {
  switch (lookup.status) {
    case "homeopathic":
      return "Homeopathic product";
    case "out_of_scope":
      return "Not a product Nomi scores";
    case "resolved":
      return scorable ? "Not scored for this person yet" : "Not scored yet";
  }
}

function unscoredBody(lookup: Found, scorable: boolean): string {
  switch (lookup.status) {
    case "homeopathic":
      return "It hasn't been evaluated by the FDA, so Nomi doesn't score it.";
    case "out_of_scope":
      return "Nomi scores over-the-counter medicines for pain, allergy, sleep, colds and digestion.";
    case "resolved":
      return scorable
        ? "Pick another profile above to see a score."
        : "We have this product's ingredients but haven't scored it yet.";
  }
}

/** The three demo profiles, so the audience can see the score change with who takes it. */
function ProfileSwitcher() {
  const profile = useDemoProfile();
  const { colors, space, text } = useTheme();
  return (
    <View style={[styles.center, { gap: space[8] }]}>
      <Text style={[text("footnote"), styles.centerText, { color: colors.text.secondary }]}>
        For: {profile.description}
      </Text>
      <View
        accessibilityRole="radiogroup"
        accessibilityLabel="Who will take it"
        style={[styles.row, { gap: space[8] }]}
      >
        {DEMO_PROFILES.map((option) => (
          <OptionChip
            key={option.id}
            mode="single"
            label={option.label}
            selected={option.id === profile.id}
            onPress={() => setDemoProfile(option)}
          />
        ))}
      </View>
    </View>
  );
}

function ScoreDetails({ record }: { record: ScoreRecord }) {
  const { colors, space, text } = useTheme();
  const rows = riskRows(record);
  return (
    <>
      {record.hard_stops_triggered.map((stop) => (
        <AlertBanner
          key={stop.id}
          type="danger"
          title="The label says not to use it"
          body={stop.message}
        />
      ))}
      {profileNotes(record).map((note, index) => (
        <AlertBanner key={index} type="warning" title="What the label says" body={note} />
      ))}
      <View style={{ gap: space[12] }}>
        <Text
          accessibilityRole="header"
          style={[text("titleSmall"), { color: colors.text.primary }]}
        >
          Why this score
        </Text>
        {rows.length === 0 ? (
          <Text style={[text("body"), { color: colors.text.primary }]}>
            No risks lowered this draft score.
          </Text>
        ) : (
          rows.map((row) => (
            <RiskFactorRow
              key={row.dimension}
              factor={row.name}
              detail={row.detail}
              points={row.points}
              citations={row.citations.map((citation) => ({
                source: citation.source,
                onPress: citation.url ? () => openSource(citation.url!) : undefined,
              }))}
            />
          ))
        )}
      </View>
      <Text style={[text("footnote"), { color: colors.text.secondary }]}>
        Draft score, worked out by hand from the FDA label and published guidelines. Each risk takes
        its own points off, and the score stops at 0. Not medical advice: ask a pharmacist or doctor
        before you take it.
      </Text>
    </>
  );
}

function openSource(url: string) {
  WebBrowser.openBrowserAsync(url).catch((error) => console.error("Couldn't open source:", error));
}

const styles = StyleSheet.create({
  center: { alignItems: "center" },
  centerText: { textAlign: "center" },
  row: { flexDirection: "row", flexWrap: "wrap", justifyContent: "center" },
});
