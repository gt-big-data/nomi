import { router, Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, type TextProps } from "react-native";

import { AlertBanner, Button } from "@/components";
import { openDataset } from "@/lib/dataset";
import { lookupBarcode, strengthText, type Lookup, type Product } from "@/lib/db";
import { type TypographyName, useTheme } from "@/theme";

type Loaded = Lookup | "error";
type Found = Extract<Lookup, { product: Product }>;
type NotFound = Exclude<Loaded, Found>;

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

  return (
    // "automatic" starts the content below the see-through header instead of under it.
    <ScrollView contentInsetAdjustmentBehavior="automatic" contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: lookup ? title(lookup) : "Looking it up" }} />
      {lookup === undefined ? (
        <ActivityIndicator style={styles.loading} accessibilityLabel="Looking it up" />
      ) : lookup !== "error" && "product" in lookup ? (
        <ProductResult lookup={lookup} />
      ) : (
        <Message lookup={lookup} />
      )}
      <Line type="footnote" secondary style={styles.barcode}>
        Barcode {barcode}
      </Line>
    </ScrollView>
  );
}

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

// Barcode errors, where scanning again may help.
const UNREADABLE = new Set<keyof typeof MESSAGES>([
  "invalid_format",
  "bad_check_digit",
  "not_ndc_barcode",
]);

function Message({ lookup }: { lookup: NotFound }) {
  const status = lookup === "error" ? lookup : lookup.status;
  return (
    <>
      <Line>{MESSAGES[status]}</Line>
      {UNREADABLE.has(status) && <Button label="Scan again" onPress={scanAgain} />}
    </>
  );
}

/** Back to the camera. A deep link has nothing to go back to. */
function scanAgain() {
  if (router.canGoBack()) router.back();
  else router.replace("/");
}

/** Text in a theme text style and color, so it's readable in light and dark mode. */
function Line({
  type = "body",
  secondary = false,
  style,
  ...props
}: TextProps & { type?: TypographyName; secondary?: boolean }) {
  const { colors, text } = useTheme();
  return (
    <Text
      style={[
        text(type),
        { color: secondary ? colors.text.secondary : colors.text.primary },
        style,
      ]}
      {...props}
    />
  );
}

// Found but not yet checked by a second person: shown with a "preliminary" badge (system design 8.2).
const REVIEWED = new Set(["sampled_ok", "pharmacist_reviewed"]);

function ProductResult({ lookup }: { lookup: Found }) {
  const { product } = lookup;
  return (
    <>
      {lookup.status === "resolved" && !REVIEWED.has(product.reviewStatus ?? "") && (
        <Line type="label">Preliminary</Line>
      )}
      <Line type="titleLarge" accessibilityRole="header">
        {product.brand ?? product.ndc11}
      </Line>
      {product.generic ? <Line secondary>{product.generic}</Line> : null}
      {lookup.status === "homeopathic" && (
        // docs/system-design.md 5.2: shown as "not evaluated by FDA" and not scored.
        <AlertBanner
          type="info"
          title="Homeopathic product"
          body="It hasn't been evaluated by the FDA, so Nomi doesn't score it."
        />
      )}
      {lookup.status === "out_of_scope" && (
        <AlertBanner
          type="info"
          title="Not a product Nomi scores"
          body="Nomi scores over-the-counter medicines for pain, allergy, sleep, colds and digestion."
        />
      )}
      <Line type="titleSmall" accessibilityRole="header" style={styles.heading}>
        Active ingredients
      </Line>
      {product.ingredients.length === 0 ? (
        <Line secondary>None listed.</Line>
      ) : (
        product.ingredients.map((ingredient) => (
          <Line key={ingredient.unii}>
            {ingredient.name} {strengthText(ingredient)}
          </Line>
        ))
      )}
    </>
  );
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 8 },
  loading: { marginTop: 48 },
  heading: { marginTop: 12 },
  barcode: { marginTop: 24 },
});
