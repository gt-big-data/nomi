import { useTheme } from "@/theme";

import { Pill } from "./Pill";

/** Same values as `CitationSource` in @nomi/schema (citation.source). */
export type CitationSource =
  | "fda_label"
  | "otc_monograph"
  | "stopp_start"
  | "acb"
  | "faers"
  | "publication"
  | "pharmacist_review";

/** What each source is called in the app. */
export const citationSourceText: Record<CitationSource, string> = {
  fda_label: "FDA label",
  otc_monograph: "OTC monograph",
  stopp_start: "STOPP/START",
  acb: "ACB scale",
  faers: "FDA reports",
  publication: "Research",
  pharmacist_review: "Pharmacist",
};

type CitationChipProps = {
  source: CitationSource;
  /** Open the source (citation.url or its quote). Leave out for a chip that only labels. */
  onPress?: () => void;
};

/**
 * Where a value comes from. One chip per citation.
 *
 * @example
 * ```tsx
 * // citation.url is optional, so only make the chip tappable when there is one
 * <CitationChip
 *   source={citation.source}
 *   onPress={citation.url ? () => Linking.openURL(citation.url!) : undefined}
 * />
 * <CitationChip source="acb" />
 * ```
 */
export function CitationChip({ source, onPress }: CitationChipProps) {
  const { colors } = useTheme();
  const displayText = citationSourceText[source];
  return (
    <Pill
      icon="doc"
      label={displayText}
      textStyle="caption"
      background={colors.brand.tint}
      foreground={colors.brand.text}
      accessibilityLabel={`Source: ${displayText}`}
      onPress={onPress}
      role="link"
      accessibilityHint="Opens the source"
    />
  );
}
