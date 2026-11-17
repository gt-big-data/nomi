/**
 * Builds a small nomi.sqlite from product records, for the app until the pipeline's build
 * (NOMI-038) lands, and for the lookup tests. The tables come from packages/schema/sqlite/nomi.sql.
 */

import { readdirSync, readFileSync } from "node:fs";
import type { DatabaseSync } from "node:sqlite";

const SCHEMA_SQL = new URL("../../../packages/schema/sqlite/nomi.sql", import.meta.url);
const EXAMPLES = new URL("../../../packages/schema/examples/", import.meta.url);

// The fields of packages/schema/schemas/product.schema.json that the dataset holds.
export interface ProductRecord {
  ndc11: string;
  spl_set_id: string;
  brand_name: string;
  generic_name: string;
  dosage_form?: string;
  otc_category: string | null;
  scope: "in_scope" | "homeopathic" | "out_of_scope";
  ingredients: {
    unii: string;
    name: string;
    strength: number;
    unit: string;
    per_amount?: number;
    per_unit?: string;
  }[];
  review_status?: string;
}

export interface FixtureProduct {
  // The package's dashed NDC10, e.g. 50580-449-05. Product records keep only the NDC11, which
  // can't be turned back into the digits printed in the barcode.
  packageNdc: string;
  product: ProductRecord;
}

// Package NDCs of the reference products (NOMI-015), from the openFDA NDC directory.
const REFERENCE_PACKAGES: Record<string, string> = {
  "00280608020": "0280-6080-20", // Aleve Liquid Gels
  "50580044905": "50580-449-05", // Tylenol Extra Strength
  "69423099516": "69423-995-16", // Vicks NyQuil Cold and Flu
  "79903029710": "79903-297-10", // Equate Allergy Relief
  "84126031604": "84126-316-04", // ZzzQuil Nighttime Sleep-Aid
};

const BUILT_AT = "2025-01-01T00:00:00Z";

/** The NDC11 of a dashed NDC10: each part zero-padded to 5-4-2. */
export function ndc11(packageNdc: string): string {
  const parts = packageNdc.split("-");
  if (!/^(\d{4}-\d{4}-\d{2}|\d{5}-\d{3}-\d{2}|\d{5}-\d{4}-\d)$/.test(packageNdc)) {
    throw new Error(`Expected a dashed NDC10, got ${packageNdc}`);
  }
  return parts[0].padStart(5, "0") + parts[1].padStart(4, "0") + parts[2].padStart(2, "0");
}

/** The five reference products in packages/schema/examples. */
export function referenceProducts(): FixtureProduct[] {
  return (
    readdirSync(EXAMPLES, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      // Sorted, so every build writes the same file.
      .sort((a, b) => a.name.localeCompare(b.name))
      .map((entry) => {
        const file = new URL(`${entry.name}/product.json`, EXAMPLES);
        const product: ProductRecord = JSON.parse(readFileSync(file, "utf8"));
        const packageNdc = REFERENCE_PACKAGES[product.ndc11];
        if (!packageNdc) {
          throw new Error(`No package NDC for ${product.ndc11}; add it to REFERENCE_PACKAGES`);
        }
        return { packageNdc, product };
      })
  );
}

/** Creates the tables in an empty database and fills them. */
export function buildDataset(
  db: DatabaseSync,
  products: FixtureProduct[],
  datasetVersion: string,
): void {
  db.exec(readFileSync(SCHEMA_SQL, "utf8"));
  db.prepare("INSERT INTO meta (dataset_version, built_at) VALUES (?, ?)").run(
    datasetVersion,
    // Fixed, so rebuilding gives the same file and the same asset hash.
    BUILT_AT,
  );
  const insertProduct = db.prepare(
    `INSERT INTO products (package_ndc, ndc10, ndc11, set_id, brand, generic, form, category,
       scope_flag, review_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
  );
  const insertIngredient = db.prepare(
    `INSERT INTO product_ingredients (package_ndc, unii, strength, unit, per_amount, per_unit)
       VALUES (?, ?, ?, ?, ?, ?)`,
  );
  const insertName = db.prepare("INSERT OR IGNORE INTO ingredients (unii, name) VALUES (?, ?)");

  for (const { packageNdc, product: p } of products) {
    if (ndc11(packageNdc) !== p.ndc11) {
      throw new Error(`${packageNdc} is not NDC11 ${p.ndc11}`);
    }
    insertProduct.run(
      packageNdc,
      packageNdc.replaceAll("-", ""),
      p.ndc11,
      p.spl_set_id,
      p.brand_name,
      p.generic_name,
      p.dosage_form ?? null,
      p.otc_category,
      p.scope,
      p.review_status ?? null,
    );
    for (const i of p.ingredients) {
      insertName.run(i.unii, i.name);
      insertIngredient.run(
        packageNdc,
        i.unii,
        i.strength,
        i.unit,
        i.per_amount ?? null,
        i.per_unit ?? null,
      );
    }
  }
}
