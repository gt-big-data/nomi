# NOMI-025: package identity

Run from the repository root:

```sh
uv run pipeline identity resolve
```

Reads `Settings.bronze_dir`; writes `product.parquet` and `identity_results.parquet`
under `Settings.silver_dir`. `--report PATH` overrides the default report location.
The command exits 1 below 90% correct coverage (including empty input), after
writing diagnostics. Missing/malformed source files fail the build.

## Provisional upstream interfaces

NOMI-009/010 are not implemented on main yet. Agree these column names with their
owners before running on real inputs. IDs must be strings, preserving leading zeros.
All directory rows must already be filtered to human OTC packages.

| File | Required columns |
| --- | --- |
| ndc.parquet | ndc11, package_ndc (original segmented NDC10) |
| spl_products.parquet | ndc11, spl_set_id, spl_version (integer); display fields such as brand_name, generic_name, marketing_category |
| spl_ingredients.parquet | ndc11, spl_set_id, spl_version, unii, name, strength (numeric), unit; optional per_amount/per_unit |

Each SPL product row represents one package on one label version. Ingredient rows
must be active ingredients for that exact package and label version. Do not join
on set ID alone: one label can contain multiple products with different strengths.
Latest version is determined per set across the full input, including packages
subsequently removed from that label. Multiple current labels for a package are
flagged, never silently selected. Identical duplicate rows are harmless.

A scan resolves only if exactly one distinct parser candidate appears in the NDC
directory, exactly one current label exists, and active ingredients are present
with usable identity and strength fields. Parser errors and each unresolved state
are retained in diagnostics. Candidate ambiguity remains an error even if only
one candidate has a label.

`product.parquet` is the identity-stage intermediate. Category/scope (NOMI-026)
and uses (NOMI-047) still need enrichment before it meets the complete shared
Product schema. No clinical classifications are invented here.

## Coverage

One synthetic UPC-A is generated for every distinct original package NDC in the
directory. The original segmented NDC10 is required: NDC11 padding is ambiguous
and cannot be reversed safely. Invalid originals and normalization mismatches
remain in the denominator. Exact duplicates do not inflate coverage.

A success means the full identity, label and ingredients resolve to the expected
package. Every failure appears in the Markdown report and Parquet diagnostics.
Synthetic coverage does not measure real retail-barcode coverage.

The parser is copied unchanged from `origin/rishan/8-barcode-to-ndc`
(NOMI-007); reconcile it with that branch when merged. It is not a separate parser
implementation. Full-data coverage has not yet been measured: ingestion outputs
are unavailable. Fixture results must not be presented as the ticket's 90% result.
