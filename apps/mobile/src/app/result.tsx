import { router, Stack, useLocalSearchParams } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";

import {
  AlertBanner,
  BottomBar,
  Button,
  GlassButton,
  Icon,
  ListGroup,
  ListRow,
  RiskList,
  ScoreBadge,
  SegmentedControl,
  useBottomBarSpace,
} from "@/components";
import { ingredientName, productName } from "@/lib/displayName";
import { openDataset } from "@/lib/dataset";
import { lookupBarcode, strengthText, type Lookup, type Product } from "@/lib/db";
import { DEMO_PROFILES, type ScoredFor, setScoredFor, useScoredFor } from "@/lib/demoProfiles";
import { profileNotes, recordTier, riskRows, type ScoreRecord } from "@/lib/referenceScores";
import { score } from "@/scoring/engine";
import { RATINGS } from "@/scoring/ratingsData";
import { useSavedProfile } from "@/storage/activeProfile";
import { recordScan, setTaking, useCabinet } from "@/storage/cabinet";
import {
  conditionText,
  defaultProfile,
  medicationTypeText,
  personaText,
  type Profile,
  type Relation,
  toScoringProfile,
} from "@/storage/profile";
import { type ProductTier, productTierColors, productTierText, useTheme } from "@/theme";

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
  const { colors, space } = useTheme();
  const bottomSpace = useBottomBarSpace();
  const found = lookup !== undefined && lookup !== "error" && "product" in lookup;

  // Only scans that found a product go to Home; ProductResult saves them with their score.

  return (
    <View style={[styles.flex, { backgroundColor: colors.bg.canvas }]}>
      <Stack.Screen
        options={{ title: lookup ? title(lookup) : "Looking it up", headerTitle: "" }}
      />
      <ScrollView
        contentInsetAdjustmentBehavior="automatic"
        contentContainerStyle={[
          found ? null : styles.grow,
          {
            paddingHorizontal: space[20],
            paddingTop: space[8],
            paddingBottom: bottomSpace,
            gap: space[24],
          },
        ]}
      >
        {lookup === undefined ? (
          <ActivityIndicator style={{ marginTop: space[48] }} accessibilityLabel="Looking it up" />
        ) : found ? (
          <ProductResult lookup={lookup} barcode={barcode} />
        ) : (
          <Message lookup={lookup} barcode={barcode} />
        )}
      </ScrollView>
      {found && <ResultActions barcode={barcode} product={lookup.product} status={lookup.status} />}
      {lookup !== undefined && !found && (
        <BottomBar>
          <Button label="Scan again" icon="scan" onPress={scanAgain} />
          <Button type="ghost" label="Type a barcode" onPress={() => router.dismissTo("/enter")} />
        </BottomBar>
      )}
    </View>
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
  not_ndc_barcode: "This barcode doesn't carry a drug code, so Nomi can't match it yet.",
  not_found: "Nomi looked this barcode up on your phone and found no match.",
  ambiguous_ndc: "This barcode matches more than one product, so we won't guess which one it is.",
  error: "Couldn't open the product database. Close Nomi and open it again.",
};

// The headline on screens with no product; MESSAGES says why.
const HEADLINES: Record<Exclude<NotFound, "error">["status"] | "error", string> = {
  invalid_format: "Couldn't read that barcode",
  bad_check_digit: "Couldn't read that barcode",
  not_ndc_barcode: "Can't look this one up yet",
  not_found: "We don't have this product yet",
  ambiguous_ndc: "More than one product matches",
  error: "Something went wrong",
};

/** A centered empty state: one icon, a headline, why, and the barcode. */
function Message({ lookup, barcode }: { lookup: NotFound; barcode: string }) {
  const { colors, space, text } = useTheme();
  const key = lookup === "error" ? lookup : lookup.status;
  return (
    <View style={[styles.empty, { gap: space[12] }]}>
      <View style={[styles.emptyIcon, { backgroundColor: colors.brand.tint }]}>
        <Icon name="notFound" size="empty" color={colors.brand.text} />
      </View>
      <Text
        accessibilityRole="header"
        style={[
          text("verdict"),
          styles.centerText,
          { color: colors.text.primary, marginTop: space[8] },
        ]}
      >
        {HEADLINES[key]}
      </Text>
      <Text style={[text("bodyLarge"), styles.centerText, { color: colors.text.secondary }]}>
        {MESSAGES[key]}
      </Text>
      {barcode ? (
        <Text
          accessibilityLabel={`Barcode ${barcode.split("").join(" ")}`}
          style={[text("footnote"), styles.digits, { color: colors.text.tertiary }]}
        >
          {barcode}
        </Text>
      ) : null}
    </View>
  );
}

/** Back to the camera, even from a result opened from the typed barcode screen or a deep link. */
function scanAgain() {
  router.dismissTo("/");
}

// Found but not yet checked by a second person: shown with a "preliminary" badge (system design 8.2).
const REVIEWED = new Set(["sampled_ok", "pharmacist_reviewed"]);

/**
 * The v0 engine's score for this product and profile, or the active ingredients it has no ratings
 * for. The one place scores come from.
 */
function scoreFor(product: Product, profile: Profile): Scored {
  const { medication_types, ...rest } = toScoringProfile(profile);
  const result = score(product, { ...rest, medicationTypes: medication_types }, RATINGS);
  return "missing" in result
    ? { missing: result.missing, childLabel: result.reason === "child_label" }
    : { record: result, missing: [], childLabel: false };
}

type Scored = { record?: ScoreRecord; missing: string[]; childLabel: boolean };

function ProductResult({ lookup, barcode }: { lookup: Found; barcode: string }) {
  const { product } = lookup;
  const options = useProfileOptions();
  const scoredFor = useScoredFor();
  const profile = options.find((option) => option.id === scoredFor) ?? options[0];
  const { colors, space, text } = useTheme();
  // Only an in-scope product that resolved to one package may show a score.
  const { record, missing, childLabel }: Scored =
    lookup.status === "homeopathic"
      ? { missing: [], childLabel: false }
      : scoreFor(product, profile);
  const shown = lookup.status === "resolved" ? record : undefined;
  const tier: ProductTier = shown ? recordTier(shown) : "none";
  const name = product.brand ? productName(product.brand) : product.ndc11;

  useEffect(() => {
    recordScan({
      barcode,
      name,
      generic: product.generic ? ingredientName(product.generic) : undefined,
      tier,
      score: shown?.score,
    });
  }, [barcode, name, product.generic, tier, shown?.score]);

  const stop = shown && tier === "stop";
  const subtitle = [
    product.generic ? ingredientName(product.generic) : null,
    product.ingredients.length === 1 ? strengthText(product.ingredients[0]) : null,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <>
      <View style={{ gap: space[4] }}>
        {lookup.status === "resolved" && !REVIEWED.has(product.reviewStatus ?? "") && (
          <View style={[styles.inline, { gap: space[4] }]}>
            <Icon name="info" size="pill" color={colors.text.tertiary} />
            <Text style={[text("footnote"), { color: colors.text.tertiary }]}>Preliminary</Text>
          </View>
        )}
        <Text accessibilityRole="header" style={[text("title"), { color: colors.text.primary }]}>
          {name}
        </Text>
        {subtitle ? (
          <Text style={[text("subhead"), { color: colors.text.secondary }]}>{subtitle}</Text>
        ) : null}
      </View>

      {/* The verdict leads; who it's for comes right under it. */}
      <View style={{ gap: space[20] }}>
        {stop ? (
          <StopCard messages={shown.hard_stops_triggered.map((s) => s.message)} />
        ) : (
          <Verdict tier={tier} record={shown} />
        )}
        {(shown || childLabel) && (
          <View style={{ gap: space[8] }}>
            <SegmentedControl
              label="Who will take it"
              options={options.map((o) => ({ id: o.id, label: o.label }))}
              selected={profile.id}
              onSelect={setScoredFor}
            />
            <Text style={[text("footnote"), styles.centerText, { color: colors.text.tertiary }]}>
              For: {profile.description}
            </Text>
          </View>
        )}
      </View>

      {shown ? (
        <ScoreDetails record={shown} />
      ) : (
        <AlertBanner
          type="info"
          title={childLabel ? "Not scored for this age yet" : unscoredTitle(lookup)}
          body={
            childLabel
              ? "Labels with the same ingredients can allow different ages, and Nomi hasn't checked this one's yet. Follow the label's directions for age, and ask a pharmacist."
              : unscoredBody(lookup, missing)
          }
        />
      )}

      {product.ingredients.length > 0 && (
        <ListGroup title="Active ingredients">
          {product.ingredients.map((ingredient) => (
            <ListRow
              key={ingredient.unii}
              title={ingredientName(ingredient.name)}
              trailing={
                <Text style={[text("subhead"), { color: colors.text.secondary }]}>
                  {strengthText(ingredient)}
                </Text>
              }
              accessibilityLabel={`${ingredientName(ingredient.name)}, ${strengthText(ingredient)}`}
            />
          ))}
        </ListGroup>
      )}

      <View style={{ gap: space[4] }}>
        <Text style={[text("footnote"), { color: colors.text.tertiary }]}>
          Not medical advice. Ask a pharmacist or doctor before you take it.
        </Text>
        <Text
          accessibilityLabel={`Barcode ${barcode.split("").join(" ")}`}
          style={[text("footnote"), { color: colors.text.tertiary }]}
        >
          Barcode {barcode}
        </Text>
      </View>
    </>
  );
}

/**
 * "I take this" and "Scan again", pinned to the bottom. A product that must not be used for this
 * person only gets "Scan again", so the screen never invites taking it.
 */
function ResultActions({
  barcode,
  product,
  status,
}: {
  barcode: string;
  product: Product;
  status: Found["status"];
}) {
  const taking = useCabinet().some((item) => item.barcode === barcode && item.taking);
  const options = useProfileOptions();
  const scoredFor = useScoredFor();
  const profile = options.find((option) => option.id === scoredFor) ?? options[0];
  const record = status === "resolved" ? scoreFor(product, profile).record : undefined;
  if (record && recordTier(record) === "stop") {
    return (
      <BottomBar>
        <Button label="Scan again" icon="scan" onPress={scanAgain} />
      </BottomBar>
    );
  }
  return (
    <BottomBar row>
      <GlassButton
        tall
        icon={taking ? "checkCircle" : "plus"}
        label={taking ? "Taking" : "I take this"}
        selected={taking}
        hint={taking ? "Removes it from what you take" : "Adds it to what you take, on Home"}
        onPress={() => setTaking(barcode, !taking)}
        style={styles.flex}
      />
      <View style={styles.flex}>
        <Button label="Scan again" icon="scan" onPress={scanAgain} />
      </View>
    </BottomBar>
  );
}

/** The ring with the tier word and how many points the risks took off, side by side. */
function Verdict({ tier, record }: { tier: ProductTier; record?: ScoreRecord }) {
  const { colors, space, text } = useTheme();
  const c = productTierColors(colors, tier);
  const rows = record ? riskRows(record) : [];
  const points = rows.reduce((sum, row) => sum + row.points, 0);
  const summary = !record
    ? null
    : rows.length === 0
      ? "No risks lowered the score."
      : `${rows.length} ${rows.length === 1 ? "risk" : "risks"} took ${points} points off.`;
  return (
    <View style={[styles.inline, { gap: space[20] }]}>
      <ScoreBadge tier={tier} score={record?.score} />
      <View style={[styles.flex, { gap: space[8] }]}>
        <Text style={[text("verdict"), { color: c.text }]}>{productTierText[tier]}</Text>
        {summary ? (
          <Text style={[text("subhead"), { color: colors.text.primary }]}>{summary}</Text>
        ) : null}
      </View>
    </View>
  );
}

/** "Do not use": the one tinted card in the app, so it never looks like an ordinary score. */
function StopCard({ messages }: { messages: string[] }) {
  const { colors, space, text } = useTheme();
  return (
    <View
      accessible
      accessibilityRole="alert"
      accessibilityLabel={`Do not use. ${messages.join(" ")}`}
      style={[
        styles.stopCard,
        {
          backgroundColor: colors.tier.high.tint,
          borderColor: colors.tier.high.mark + "33",
          padding: space[20],
          gap: space[16],
        },
      ]}
    >
      <View style={[styles.inline, { gap: space[16] }]}>
        <View style={[styles.stopDisc, { backgroundColor: colors.tier.stop.fill }]}>
          <Icon name="stop" size="stop" color={colors.tier.stop.on} />
        </View>
        <Text style={[text("title"), styles.flex, { color: colors.tier.high.text }]}>
          Do not use
        </Text>
      </View>
      {messages.map((message, index) => (
        <Text key={index} style={[text("bodyLarge"), { color: colors.text.primary }]}>
          {message}
        </Text>
      ))}
    </View>
  );
}

function unscoredTitle(lookup: Found): string {
  return lookup.status === "homeopathic" ? "Homeopathic product" : "Not scored yet";
}

function unscoredBody(lookup: Found, missing: string[]): string {
  if (lookup.status === "homeopathic") {
    return "It hasn't been evaluated by the FDA, so Nomi doesn't score it.";
  }
  if (missing.length > 0) {
    const names = missing.map((name) => name.toLowerCase()).join(", ");
    return `Nomi scores a product once every active ingredient is rated. Not rated yet: ${names}.`;
  }
  return "Nomi hasn't rated this product's ingredients yet.";
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

function ScoreDetails({ record }: { record: ScoreRecord }) {
  const stopped = record.hard_stops_triggered.length > 0;
  const { colors, text } = useTheme();
  const rows = riskRows(record);
  return (
    <>
      {profileNotes(record).map((note, index) => (
        <AlertBanner key={index} type="warning" title="What the label says" body={note} />
      ))}
      {rows.length === 0 ? (
        <Text style={[text("bodyLarge"), { color: colors.text.primary }]}>
          No risks lowered this draft score.
        </Text>
      ) : (
        <RiskList
          title={stopped ? "Other risks" : "Why this score"}
          items={rows.map((row) => ({
            id: row.dimension,
            factor: row.name,
            detail: row.detail,
            points: row.points,
            citations: row.citations.map(({ source, section, url }) => ({
              source,
              section,
              onPress: url ? () => openSource(url) : undefined,
            })),
          }))}
        />
      )}
    </>
  );
}

function openSource(url: string) {
  WebBrowser.openBrowserAsync(url).catch((error) => console.error("Couldn't open source:", error));
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  grow: { flexGrow: 1 },
  inline: { flexDirection: "row", alignItems: "center" },
  centerText: { textAlign: "center" },
  digits: { fontVariant: ["tabular-nums"], letterSpacing: 1 },
  empty: { flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 12 },
  emptyIcon: {
    width: 88,
    height: 88,
    borderRadius: 44,
    alignItems: "center",
    justifyContent: "center",
  },
  stopCard: { borderRadius: 24, borderWidth: 1 },
  stopDisc: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: "center",
    justifyContent: "center",
  },
});
