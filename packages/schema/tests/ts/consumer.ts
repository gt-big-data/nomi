// Compile-time check that the generated types are usable. Run with `pnpm run typecheck`.
import type { Product, ScoreRecord, Signal, TermTables } from "../../generated/ts";

const product: Product = {
  ndc11: "99999000101",
  spl_set_id: "3f1c2a9e-1111-4c2d-9a7b-000000000001",
  spl_version: 4,
  brand_name: "Sample Pain Reliever",
  generic_name: "acetaminophen",
  marketing_category: "otc_monograph_drug",
  otc_category: "internal_analgesics",
  uses: ["pain", "fever"],
  scope: "in_scope",
  ingredients: [{ unii: "362O9ITL9D", name: "acetaminophen", strength: 500, unit: "mg" }],
};

const signal: Signal = {
  unii: "362O9ITL9D",
  dimension: "liver",
  age_band: "65+",
  sex: "all",
  ic: 2.4,
  ic025: 2.1,
  report_count: 1840,
};

export function scoreTier(record: ScoreRecord, tables: TermTables): ScoreRecord["tier"] {
  if (record.hard_stops_triggered.length > 0) return "red";
  if (record.score >= tables.tier_bands.green_min) return "green";
  return record.score >= tables.tier_bands.yellow_min ? "yellow" : "red";
}

export { product, signal };
