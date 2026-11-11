// Runs lookupBarcode's SQL against a fixture built by the same code as pnpm db:fixture.
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";
import { test } from "node:test";

import {
  buildDataset,
  ndc11,
  referenceProducts,
  type FixtureProduct,
  type ProductRecord,
} from "../../scripts/fixture.mts";
import { ndcCandidates } from "./barcode.ts";
import {
  checkDataset,
  DATASET_SCHEMA_VERSION,
  LOOKUP_SQL,
  lookupBarcode,
  strengthText,
  type Dataset,
  type LookupStatus,
} from "./db.ts";

/** The UPC-A barcode printed on a package: "3" + its NDC10 digits + a check digit. */
function barcode(packageNdc: string): string {
  const body = "3" + packageNdc.replaceAll("-", "");
  let total = 0;
  for (let i = 0; i < body.length; i++) {
    total += Number(body[i]) * (i % 2 === 0 ? 3 : 1);
  }
  return body + ((10 - (total % 10)) % 10);
}

function made(
  packageNdc: string,
  scope: ProductRecord["scope"],
  ingredients: ProductRecord["ingredients"] = [],
): FixtureProduct {
  return {
    packageNdc,
    product: {
      ndc11: ndc11(packageNdc),
      spl_set_id: "00000000-0000-0000-0000-000000000000",
      brand_name: `Test ${packageNdc}`,
      generic_name: "test",
      otc_category: null,
      scope,
      ingredients,
    },
  };
}

const reference = referenceProducts();
const db = new DatabaseSync(":memory:");
buildDataset(
  db,
  [
    ...reference,
    made("11111-111-11", "homeopathic"),
    made("22222-222-22", "out_of_scope", [
      { unii: "362O9ITL9D", name: "acetaminophen", strength: 80, unit: "mg" },
    ]),
    // Two packages that pad to one NDC11, 12345067809.
    made("12345-0678-9", "in_scope"),
    made("12345-678-09", "in_scope"),
    // Pads to 54321012304, a candidate of a scan of 54321-123-04, which isn't in the dataset.
    made("54321-0123-4", "in_scope"),
    // Its ingredient's name row is deleted below.
    made("33333-333-33", "in_scope", [
      { unii: "0000000000", name: "unnamed", strength: 1, unit: "mg" },
    ]),
    // The same 10 digits, split two ways: two real packages behind one barcode.
    made("1234-5678-90", "in_scope"),
    made("12345-678-90", "in_scope"),
  ],
  "test",
);
db.exec("PRAGMA foreign_keys = OFF; DELETE FROM ingredients WHERE unii = '0000000000'");

function adapt(db: DatabaseSync): Dataset {
  return {
    async getAllAsync<T>(sql: string, params: (string | number)[]) {
      return db.prepare(sql).all(...params) as unknown as T[];
    },
  };
}
const dataset = adapt(db);

/** A fresh fixture of the reference products, for the checkDataset tests. */
function referenceDb(path = ":memory:"): DatabaseSync {
  const fresh = new DatabaseSync(path);
  buildDataset(fresh, referenceProducts(), "test");
  return fresh;
}

const seen = new Set<LookupStatus>();
async function lookup(raw: string) {
  const result = await lookupBarcode(raw, dataset);
  seen.add(result.status);
  return result;
}

for (const { packageNdc, product } of reference) {
  test(`finds ${product.brand_name}`, async () => {
    const result = await lookup(barcode(packageNdc));
    assert.equal(result.status, "resolved");
    assert.ok("product" in result);
    assert.equal(result.product.ndc11, product.ndc11);
    assert.equal(result.product.brand, product.brand_name);
    assert.equal(result.product.generic, product.generic_name);
    assert.equal(result.product.scope, "in_scope");
    const expected = product.ingredients
      .map((i) => ({
        unii: i.unii,
        name: i.name,
        strength: i.strength,
        unit: i.unit,
        perAmount: i.per_amount ?? null,
        perUnit: i.per_unit ?? null,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
    assert.deepEqual(result.product.ingredients, expected);
  });
}

test("finds a product from its EAN-13 form", async () => {
  const result = await lookup("0" + barcode("50580-449-05"));
  assert.equal(result.status, "resolved");
  assert.ok("product" in result);
  assert.equal(result.product.brand, "Tylenol Extra Strength");
});

test("rejects a barcode that isn't digits", async () => {
  assert.deepEqual(await lookup("not a barcode"), { status: "invalid_format" });
});

test("rejects a misread check digit", async () => {
  const good = barcode("50580-449-05");
  const bad = good.slice(0, 11) + ((Number(good[11]) + 1) % 10);
  assert.deepEqual(await lookup(bad), { status: "bad_check_digit" });
});

test("reports a valid barcode that isn't a drug", async () => {
  assert.deepEqual(await lookup("012345678905"), { status: "not_ndc_barcode" });
});

test("reports a drug barcode that isn't in the dataset", async () => {
  assert.deepEqual(await lookup(barcode("99999-999-99")), { status: "not_found" });
});

test("shows a homeopathic product without ingredients, and never as resolved", async () => {
  const result = await lookup(barcode("11111-111-11"));
  assert.equal(result.status, "homeopathic");
  assert.ok("product" in result);
  assert.equal(result.product.scope, "homeopathic");
  assert.deepEqual(result.product.ingredients, []);
});

test("shows an out-of-scope product", async () => {
  const result = await lookup(barcode("22222-222-22"));
  assert.equal(result.status, "out_of_scope");
  assert.ok("product" in result);
  assert.equal(result.product.ingredients.length, 1);
});

test("tells apart two packages that pad to one NDC11", async () => {
  for (const packageNdc of ["12345-0678-9", "12345-678-09"]) {
    const result = await lookup(barcode(packageNdc));
    assert.equal(result.status, "resolved");
    assert.ok("product" in result);
    assert.equal(result.product.packageNdc, packageNdc);
    assert.equal(result.product.ndc11, "12345067809");
  }
});

test("doesn't match a package whose NDC10 only pads to a candidate", async () => {
  const scan = barcode("54321-123-04");
  // The trap: 54321-0123-4 is in the dataset as 54321012304, one of this scan's candidates.
  assert.ok(ndcCandidates(scan).candidates.includes(ndc11("54321-0123-4")));
  assert.deepEqual(await lookup(scan), { status: "not_found" });
});

test("never picks between two packages with the scanned digits", async () => {
  assert.deepEqual(await lookup(barcode("1234-5678-90")), {
    status: "ambiguous_ndc",
    matches: ["1234-5678-90", "12345-678-90"],
  });
});

test("uses the ndc10 index, not a table scan", () => {
  const plan = db.prepare(`EXPLAIN QUERY PLAN ${LOOKUP_SQL}`).all("0") as { detail: string }[];
  const details = plan.map((row) => row.detail);
  assert.ok(
    details.some((d) => d.includes("USING INDEX products_ndc10")),
    details.join("; "),
  );
  assert.ok(!details.some((d) => d.startsWith("SCAN")), details.join("; "));
});

test("shows the UNII when an ingredient has no name", async () => {
  const result = await lookup(barcode("33333-333-33"));
  assert.ok("product" in result);
  assert.equal(result.product.ingredients[0].name, "0000000000");
});

test("accepts the fixture", async () => {
  const row = db.prepare("PRAGMA user_version").get() as { user_version: number };
  assert.equal(row.user_version, DATASET_SCHEMA_VERSION);
  await checkDataset(adapt(referenceDb()));
});

test("rejects a dataset with another schema version", async () => {
  const fresh = referenceDb();
  fresh.exec(`PRAGMA user_version = ${DATASET_SCHEMA_VERSION + 1}`);
  await assert.rejects(checkDataset(adapt(fresh)), /schema version/);
});

test("rejects a dataset with an empty or missing meta table", async () => {
  const fresh = referenceDb();
  fresh.exec("DELETE FROM meta");
  await assert.rejects(checkDataset(adapt(fresh)), /meta rows/);
  fresh.exec("DROP TABLE meta");
  await assert.rejects(checkDataset(adapt(fresh)), /no such table/);
});

test("rejects a half-copied dataset", async (t) => {
  const dir = mkdtempSync(join(tmpdir(), "nomi-"));
  t.after(() => rmSync(dir, { recursive: true, force: true }));
  const path = join(dir, "nomi.sqlite");
  referenceDb(path).close();
  const bytes = readFileSync(path);
  writeFileSync(path, bytes.subarray(0, bytes.length / 2));
  await assert.rejects(checkDataset(adapt(new DatabaseSync(path))), /malformed/);
});

test("formats strengths", () => {
  const ingredient = { unii: "X", name: "x", strength: 50, unit: "mg" };
  assert.equal(strengthText({ ...ingredient, perAmount: null, perUnit: null }), "50 mg");
  assert.equal(strengthText({ ...ingredient, perAmount: 30, perUnit: "mL" }), "50 mg per 30 mL");
});

test("covers every status", () => {
  const expected = new Set([
    "invalid_format",
    "bad_check_digit",
    "not_ndc_barcode",
    "not_found",
    "ambiguous_ndc",
    "resolved",
    "homeopathic",
    "out_of_scope",
  ]);
  assert.deepEqual(seen, expected);
});
