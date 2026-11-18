/**
 * Label data arrives in whatever case the manufacturer typed: "equate allergy relief",
 * "DIPHENHYDRAMINE HYDROCHLORIDE". These turn it into text that reads well on screen. Mixed case
 * is left alone, because it is usually deliberate ("TYLENOL Extra Strength", "ZzzQuil").
 */

const isUpper = (s: string) => s === s.toUpperCase() && s !== s.toLowerCase();
const isLower = (s: string) => s === s.toLowerCase() && s !== s.toUpperCase();

/** Words with a fixed spelling, whatever case they arrive in. */
const FIXED: Record<string, string> = Object.fromEntries(
  [
    "PM",
    "AM",
    "DM",
    "ER",
    "XR",
    "SR",
    "CR",
    "HBP",
    "SPF",
    "II",
    "III",
    "IV",
    "HCl",
    "mg",
    "mL",
    "OTC",
  ].map((word) => [word.toLowerCase(), word]),
);

function fix(word: string, fallback: string): string {
  return FIXED[word.toLowerCase()] ?? fallback;
}

/** A product name: all-lowercase or all-caps names become Title Case. "ADVIL PM" → "Advil PM". */
export function productName(name: string): string {
  if (!isUpper(name) && !isLower(name)) return name;
  return name
    .toLowerCase()
    .replace(/[a-z0-9]+/g, (word) => fix(word, word.charAt(0).toUpperCase() + word.slice(1)));
}

/** An ingredient or generic name: all-caps becomes sentence case, "Diphenhydramine hydrochloride". */
export function ingredientName(name: string): string {
  if (!isUpper(name) && !isLower(name)) return name;
  const lower = name.toLowerCase().replace(/[a-z0-9]+/g, (word) => fix(word, word));
  return lower.charAt(0).toUpperCase() + lower.slice(1);
}
