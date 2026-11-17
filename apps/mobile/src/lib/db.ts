/**
 * Looks up a scanned barcode in the bundled dataset (NOMI-040).
 *
 * Works on any database with a getAllAsync like expo-sqlite's, so the tests run the same SQL
 * against a fixture with node:sqlite. dataset.ts opens the real file on the phone.
 * The tables are in packages/schema/sqlite/nomi.sql.
 */

import { ndcCandidates, type Status as ParseStatus } from "./barcode.ts";

// The PRAGMA user_version the queries here expect (packages/schema/sqlite/nomi.sql).
export const DATASET_SCHEMA_VERSION = 1;

export interface Dataset {
  getAllAsync<T>(sql: string, params: (string | number)[]): Promise<T[]>;
}

export interface Ingredient {
  unii: string;
  name: string;
  strength: number;
  unit: string;
  perAmount: number | null;
  perUnit: string | null;
}

export interface Product {
  // The package's dashed NDC10, e.g. 50580-449-05.
  packageNdc: string;
  ndc11: string;
  brand: string | null;
  generic: string | null;
  form: string | null;
  scope: "in_scope" | "homeopathic" | "out_of_scope";
  reviewStatus: string | null;
  ingredients: Ingredient[];
}

// Status names follow the pipeline's resolver (pipeline/docs/identity.md), plus out_of_scope.
export type Lookup =
  | { status: Exclude<ParseStatus, "ok"> }
  | { status: "not_found" }
  // The package NDCs of every package with the scanned digits.
  | { status: "ambiguous_ndc"; matches: string[] }
  // Only "resolved" products may ever be scored. Homeopathic ones are shown, never scored.
  | { status: "resolved" | "homeopathic" | "out_of_scope"; product: Product };

export type LookupStatus = Lookup["status"];

interface Row {
  package_ndc: string;
  ndc11: string;
  brand: string | null;
  generic: string | null;
  form: string | null;
  scope_flag: string;
  review_status: string | null;
  unii: string | null;
  name: string | null;
  strength: number | null;
  unit: string | null;
  per_amount: number | null;
  per_unit: string | null;
}

/**
 * Throws unless db is a dataset these queries can read: the right schema version, and a meta row
 * that can actually be read, which a half-copied file usually fails.
 */
export async function checkDataset(db: Dataset): Promise<void> {
  const [version] = await db.getAllAsync<{ user_version: number }>("PRAGMA user_version", []);
  if (version?.user_version !== DATASET_SCHEMA_VERSION) {
    throw new Error(
      `nomi.sqlite has schema version ${version?.user_version}, the app needs ` +
        `${DATASET_SCHEMA_VERSION}. Run pnpm db:fixture or pnpm db:copy again.`,
    );
  }
  const [meta] = await db.getAllAsync<{ n: number }>("SELECT count(*) AS n FROM meta", []);
  if (meta?.n !== 1) {
    throw new Error(`nomi.sqlite has ${meta?.n} meta rows, expected 1.`);
  }
}

// One indexed query per scan: products by ndc10, with each one's ingredients.
export const LOOKUP_SQL = `
  SELECT p.package_ndc, p.ndc11, p.brand, p.generic, p.form, p.scope_flag, p.review_status,
         pi.unii, i.name, pi.strength, pi.unit, pi.per_amount, pi.per_unit
  FROM products p
  LEFT JOIN product_ingredients pi ON pi.package_ndc = p.package_ndc
  LEFT JOIN ingredients i ON i.unii = pi.unii
  WHERE p.ndc10 = ?
  ORDER BY p.package_ndc, i.name`;

const SCOPES = new Set(["in_scope", "homeopathic", "out_of_scope"]);

/** Returns the product a scanned barcode is, or why there isn't exactly one. */
export async function lookupBarcode(raw: string, db: Dataset): Promise<Lookup> {
  const parsed = ndcCandidates(raw);
  if (parsed.status !== "ok") {
    return { status: parsed.status };
  }
  // The 4-4-2 candidate is "0" + the 10 digits in the barcode. Match those exactly, as the
  // pipeline's resolver does; the NDC11 candidates could hit a package with other digits.
  const ndc10 = parsed.candidates[0].slice(1);
  const rows = await db.getAllAsync<Row>(LOOKUP_SQL, [ndc10]);

  const matches = [...new Set(rows.map((row) => row.package_ndc))];
  if (matches.length === 0) {
    return { status: "not_found" };
  }
  if (matches.length > 1) {
    // Never pick one of two possible products.
    return { status: "ambiguous_ndc", matches };
  }

  const first = rows[0];
  if (!SCOPES.has(first.scope_flag)) {
    throw new Error(`Unknown scope_flag ${first.scope_flag}`);
  }
  const product: Product = {
    packageNdc: first.package_ndc,
    ndc11: first.ndc11,
    brand: first.brand,
    generic: first.generic,
    form: first.form,
    scope: first.scope_flag as Product["scope"],
    reviewStatus: first.review_status,
    // A product with no ingredient rows (a homeopathic one, say) has one row of nulls.
    ingredients: rows
      .filter((row) => row.unii !== null)
      .map((row) => ({
        unii: row.unii!,
        name: row.name ?? row.unii!,
        strength: row.strength!,
        unit: row.unit!,
        perAmount: row.per_amount,
        perUnit: row.per_unit,
      })),
  };
  const status = product.scope === "in_scope" ? "resolved" : product.scope;
  return { status, product };
}

/** "500 mg", or "50 mg per 30 mL" for liquids. */
export function strengthText(ingredient: Ingredient): string {
  const text = `${ingredient.strength} ${ingredient.unit}`;
  if (ingredient.perAmount === null || ingredient.perUnit === null) {
    return text;
  }
  return `${text} per ${ingredient.perAmount} ${ingredient.perUnit}`;
}
