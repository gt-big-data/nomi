-- The tables of nomi.sqlite that the app reads today (NOMI-040). See docs/system-design.md 7.1.
--
-- The single source of these tables: the app's fixture (apps/mobile/scripts/fixture.mts) runs this
-- file, and the pipeline's build of data/build/nomi.sqlite (NOMI-038) must create the same tables,
-- ideally by running this file too. The other tables in 7.1 are added here as they are built.
--
-- The app checks user_version when it opens the file. Bump it, and DATASET_SCHEMA_VERSION in
-- apps/mobile/src/lib/db.ts, whenever these tables change in a way the app's queries notice.
PRAGMA user_version = 1;

-- One row: where this file came from (provenance).
CREATE TABLE meta (
  dataset_version TEXT NOT NULL,
  model_version TEXT,
  rubric_version TEXT,
  built_at TEXT NOT NULL
);

-- One row per package, keyed by its dashed NDC10 (package_ndc, e.g. 50580-449-05). The app finds a
-- scan by ndc10: the same 10 digits without dashes, which are the digits printed in the barcode.
-- Neither ndc10 nor ndc11 is unique:
-- - Two packages can pad to one NDC11 (12345-0678-9 and 12345-678-09 are both 12345067809), so the
--   app must not look up by NDC11 (pipeline/docs/identity.md).
-- - One barcode's 10 digits can be two packages (1234-5678-90 and 12345-678-90), which the app
--   reports as ambiguous.
--
-- Which packages get a row, by the pipeline resolver's status:
-- - resolved: with its ingredient rows and the product schema's scope as scope_flag.
-- - homeopathic: scope_flag homeopathic, ingredient rows optional.
-- - ambiguous_ndc: every package behind the barcode, so the app says "ambiguous" and not "not
--   found". One known only from a label needs just package_ndc, ndc10, ndc11 and scope_flag
--   out_of_scope, with the rest null and no ingredient rows: the app returns ambiguous_ndc before
--   it reads any other column.
-- Leave out packages with any other status (missing_label, kit, ingredient_conflict and so on); the
-- app shows those as not found.
--
-- The app treats only scope_flag in_scope as scorable. A homeopathic package (marketing category
-- unapproved_homeopathic) always gets scope_flag homeopathic, including one that resolved with a
-- label, and an out-of-scope one gets out_of_scope. Never default scope_flag to in_scope.
CREATE TABLE products (
  package_ndc TEXT PRIMARY KEY,
  ndc10 TEXT NOT NULL,
  ndc11 TEXT NOT NULL,
  set_id TEXT,
  brand TEXT,
  generic TEXT,
  form TEXT,
  -- The product schema's otc_category.
  category TEXT,
  -- The product schema's scope: in_scope, homeopathic (shown, never scored) or out_of_scope.
  scope_flag TEXT NOT NULL,
  -- The product schema's review_status.
  review_status TEXT
);
CREATE INDEX products_ndc10 ON products (ndc10);

-- Active ingredients per package. Strength is per unit of the dosage form, or per per_amount
-- per_unit for liquids (50 mg per 30 mL).
CREATE TABLE product_ingredients (
  package_ndc TEXT NOT NULL REFERENCES products (package_ndc),
  unii TEXT NOT NULL REFERENCES ingredients (unii),
  strength REAL NOT NULL,
  unit TEXT NOT NULL,
  per_amount REAL,
  per_unit TEXT,
  PRIMARY KEY (package_ndc, unii)
);

-- Display names.
CREATE TABLE ingredients (
  unii TEXT PRIMARY KEY,
  name TEXT NOT NULL
);
