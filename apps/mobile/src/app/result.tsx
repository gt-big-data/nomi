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
import { DEMO_PROFILES, type ScoredFor, setScoredFor, useScoredFor } from "@/lib/demoProfiles";
import { REFERENCE_SCORES } from "@/lib/referenceScoreData";
import {
  findScore,
  profileNotes,
  recordTier,
  riskRows,
  type ScoreRecord,
} from "@/lib/referenceScores";
import { useSavedProfile } from "@/storage/activeProfile";
import {
  conditionText,
  defaultProfile,
  medicationTypeText,
  personaText,
  type Profile,
  type Relation,
  toScoringProfile,
} from "@/storage/profile";
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
  const params = useLocalSearchParams<{ barcode?: string | string[] }>();
  const barcode = (Array.isArray(params.barcode) ? params.barcode[0] : params.barcode) ?? "";
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
      {lookup !== undefined && <Button label="Scan again" onPress={scanAgain} />}
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
      return "Can't look up";
    case "invalid_format":
    case "bad_check_digit":
      return "Couldn't read barcode";
  }
}

// What to say when there is no single product to show. Nothing here is ever scored.
const MESSAGES: Record<Exclude<NotFound, "error">["status"] | "error", string> = {
  invalid_format: "The barcode didn't read cleanly. Please try again.",
  bad_check_digit: "The barcode didn't read cleanly. Please try again.",
  not_ndc_barcode: "We can't look up this barcode yet.",
  not_found: "We don't have this product yet.",
  ambiguous_ndc: "This barcode matches more than one product, so we won't guess which one it is.",
  error: "Couldn't open the product database. Close Nomi and open it again.",
};

function Message({ lookup }: { lookup: NotFound }) {
  const { colors, text } = useTheme();
  return (
    <Text style={[text("body"), { color: colors.text.primary }]}>
      {MESSAGES[lookup === "error" ? lookup : lookup.status]}
    </Text>
  );
}

/** Back to the camera, even from a result opened from the typed barcode screen or a deep link. */
function scanAgain() {
  router.dismissTo("/");
}

// Found but not yet checked by a second person: shown with a "preliminary" badge (system design 8.2).
const REVIEWED = new Set(["sampled_ok", "pharmacist_reviewed"]);

/**
 * The score for this product and profile, and whether the product has a score for anyone, so the
 * screen can tell "not scored yet" from "not scored for this person". The one place scores come
 * from: the scoring engine replaces the draft reference scores here.
 */
function scoreFor(ndc11: string, profile: Profile): { scorable: boolean; record?: ScoreRecord } {
  return {
    scorable: REFERENCE_SCORES.some((r) => r.ndc11 === ndc11),
    record: findScore(REFERENCE_SCORES, ndc11, toScoringProfile(profile)),
  };
}

function ProductResult({ lookup }: { lookup: Found }) {
  const { product } = lookup;
  const options = useProfileOptions();
  const scoredFor = useScoredFor();
  const profile = options.find((option) => option.id === scoredFor) ?? options[0];
  const { colors, space, text } = useTheme();
  // Only an in-scope product that resolved to one package may show a score.
  const { scorable, record } =
    lookup.status === "resolved" ? scoreFor(product.ndc11, profile) : { scorable: false };
  const tier: ProductTier = record ? recordTier(record) : "none";

  return (
    <>
      <View style={{ gap: space[4] }}>
        {lookup.status === "resolved" && !REVIEWED.has(product.reviewStatus ?? "") && (
          <Text style={[text("label"), { color: colors.text.primary }]}>Preliminary</Text>
        )}
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
        {scorable && <ProfileSwitcher options={options} selected={profile} />}
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

/** What the saved profile's chip says. */
const SAVED_LABEL: Record<Relation, string> = {
  self: "You",
  someone_else: "Them",
  child: "Your child",
};

type ProfileOption = Profile & { id: ScoredFor; label: string; description: string };

/** The saved profile first, then the three demo profiles. */
function useProfileOptions(): ProfileOption[] {
  const saved = useSavedProfile() ?? defaultProfile;
  const description = [
    personaText[saved.persona],
    ...saved.conditions.map((condition) => conditionText[condition]),
    ...saved.medication_types.map((type) => medicationTypeText[type]),
  ].join(", ");
  return [
    { ...saved, id: "saved", label: SAVED_LABEL[saved.relation], description },
    ...DEMO_PROFILES,
  ];
}

/** The saved profile and the demo profiles, so the audience can see the score change with who takes it. */
function ProfileSwitcher({
  options,
  selected,
}: {
  options: ProfileOption[];
  selected: ProfileOption;
}) {
  const { colors, space, text } = useTheme();
  return (
    <View style={[styles.center, { gap: space[8] }]}>
      <Text style={[text("footnote"), styles.centerText, { color: colors.text.secondary }]}>
        For: {selected.description}
      </Text>
      <View
        accessibilityRole="radiogroup"
        accessibilityLabel="Who will take it"
        style={[styles.row, { gap: space[8] }]}
      >
        {options.map((option) => (
          <OptionChip
            key={option.id}
            mode="single"
            label={option.label}
            selected={option.id === selected.id}
            onPress={() => setScoredFor(option.id)}
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
