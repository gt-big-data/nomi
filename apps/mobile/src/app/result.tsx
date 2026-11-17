import { router, Stack, useLocalSearchParams } from "expo-router";
import { ScrollView, StyleSheet, Text, type TextProps, View } from "react-native";

import { AlertBanner, Button, ScoreBadge, TierLabel } from "@/components";
import { lookupFixture, type ScanResult } from "@/lib/scanFixtures";
import { productTier, type TypographyName, useTheme } from "@/theme";

export default function Result() {
  const { barcode } = useLocalSearchParams<{ barcode?: string | string[] }>();
  const result = lookupFixture((Array.isArray(barcode) ? barcode[0] : barcode) ?? "");

  return (
    // "automatic" starts the content below the see-through header instead of under it.
    <ScrollView contentInsetAdjustmentBehavior="automatic" contentContainerStyle={styles.container}>
      <Stack.Screen options={{ title: title(result) }} />
      <Body result={result} />
      <Line type="footnote" secondary style={styles.barcode}>
        Barcode {result.barcode}
      </Line>
    </ScrollView>
  );
}

function title(result: ScanResult): string {
  switch (result.state) {
    case "scored":
      return "Result";
    case "preliminary":
      return "Preliminary result";
    case "homeopathic":
      return "Homeopathic";
    case "not_found":
      return "Not found";
    case "invalid":
      return result.reason === "not_ndc_barcode" ? "Can't look up" : "Couldn't read barcode";
  }
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

function Body({ result }: { result: ScanResult }) {
  switch (result.state) {
    case "scored": {
      const tier = productTier({ tier: result.tier });
      return (
        <>
          <Line type="titleLarge" accessibilityRole="header">
            {result.product.brand_name}
          </Line>
          <Line secondary>{result.product.generic_name}</Line>
          {/* The score is test data: release builds show the product without it. */}
          {__DEV__ ? (
            <>
              {/* The verdict and who it's for, together (docs/design/score-visualization.md). */}
              <View style={styles.score}>
                <TierLabel tier={tier} align="center" />
                <Line secondary>{result.profileText}</Line>
                <ScoreBadge tier={tier} score={result.score} />
              </View>
              <AlertBanner
                type="warning"
                title="Draft score from test data"
                body="Not medical advice."
              />
            </>
          ) : (
            <Line>Nomi hasn't scored this product yet.</Line>
          )}
        </>
      );
    }
    case "preliminary":
      // docs/system-design.md 8.2: ingredients and label warnings with a "preliminary" badge.
      return (
        <>
          <Line type="label">Preliminary</Line>
          <Line type="titleLarge" accessibilityRole="header">
            {result.product.brand_name}
          </Line>
          <Line type="titleSmall" accessibilityRole="header" style={styles.heading}>
            Ingredients
          </Line>
          {result.ingredients.map((line) => (
            <Line key={line}>{line}</Line>
          ))}
          <Line type="titleSmall" accessibilityRole="header" style={styles.heading}>
            Warnings
          </Line>
          {result.warnings.map((line) => (
            <Line key={line}>{line}</Line>
          ))}
        </>
      );
    case "homeopathic":
      // docs/system-design.md 5.2: shown as "not evaluated by FDA" and not scored.
      return (
        <>
          <Line type="titleLarge" accessibilityRole="header">
            {result.product.brand_name}
          </Line>
          <Line>
            This homeopathic product has not been evaluated by the FDA, so Nomi does not score it.
          </Line>
        </>
      );
    case "not_found":
      return <Line>We don't have this product yet.</Line>;
    case "invalid":
      return (
        <>
          <Line>
            {result.reason === "not_ndc_barcode"
              ? "We can't look up this barcode yet."
              : "The barcode didn't read cleanly. Please try again."}
          </Line>
          <Button label="Scan again" onPress={scanAgain} />
        </>
      );
  }
}

/** Back to the camera. A deep link has nothing to go back to. */
function scanAgain() {
  if (router.canGoBack()) router.back();
  else router.replace("/");
}

const styles = StyleSheet.create({
  container: { padding: 24, gap: 8 },
  score: { alignItems: "center", gap: 12, marginTop: 16 },
  heading: { marginTop: 12 },
  barcode: { marginTop: 24 },
});
