/**
 * Pretend scan results, one per result state, until the real database lands (NOMI-040).
 *
 * Field names copy packages/schema (brand_name, score, tier) so real data can replace these easily.
 */

import { ndcCandidates, type Status } from "@/lib/barcode";

export type Tier = "green" | "yellow" | "red";

interface Product {
  brand_name: string;
  generic_name: string;
}

// Only "scored" has a score, so TypeScript won't compile code that shows a score
// on the homeopathic or not-found screens.
export type ScanResult =
  | { state: "scored"; barcode: string; product: Product; score: number; tier: Tier }
  | {
      state: "preliminary";
      barcode: string;
      product: Product;
      ingredients: string[];
      warnings: string[];
    }
  | { state: "homeopathic"; barcode: string; product: Product }
  | { state: "not_found"; barcode: string }
  | { state: "invalid"; barcode: string; reason: Exclude<Status, "ok"> };

// Products we "have", keyed by barcode digits.
const PRODUCTS: Record<string, ScanResult> = {
  // Real product: packages/schema/examples/tylenol, adult 18-64. Draft score until the rubric is set.
  "350580449059": {
    state: "scored",
    barcode: "350580449059",
    product: { brand_name: "Tylenol Extra Strength", generic_name: "acetaminophen" },
    score: 49,
    tier: "red",
  },
  // Made up. Labeler 99999 isn't assigned by the FDA.
  "399999002011": {
    state: "preliminary",
    barcode: "399999002011",
    product: { brand_name: "Fixture Allergy", generic_name: "cetirizine" },
    ingredients: ["Cetirizine HCl 10 mg"],
    warnings: ["May cause drowsiness.", "Do not use with other antihistamines."],
  },
  "399999003018": {
    state: "homeopathic",
    barcode: "399999003018",
    product: { brand_name: "Fixture Cold Remedy", generic_name: "zincum gluconicum" },
  },
};

/** One barcode per state, for the dev menu. */
export const FIXTURE_BARCODES = {
  scored: "350580449059",
  preliminary: "399999002011",
  homeopathic: "399999003018",
  not_found: "399999004015", // A valid drug barcode that isn't in PRODUCTS.
  invalid: "4006381333931", // A real EAN-13 that isn't a medicine.
} as const;

/** Turns scanned digits into a result. */
export function lookupFixture(barcode: string): ScanResult {
  const parsed = ndcCandidates(barcode);
  if (parsed.status !== "ok") {
    return { state: "invalid", barcode, reason: parsed.status };
  }
  return PRODUCTS[barcode] ?? { state: "not_found", barcode };
}
