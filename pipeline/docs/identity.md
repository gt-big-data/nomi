# NOMI-025: package identity

Run from the repository root after `pipeline ingest ndc` and `pipeline ingest spl`:

```sh
uv run pipeline identity resolve
```

It reads `ndc.parquet`, `spl_products.parquet` and `spl_ingredients.parquet` from
`Settings.bronze_dir` and writes `product.parquet` and `identity_results.parquet` to
`Settings.silver_dir`, plus the report at `pipeline/reports/identity_coverage.md`
(`--report PATH` to change it). It exits 1 below 95% coverage (or with no scored packages), after writing everything.

## How a barcode resolves

1. The barcode parser (`identity/barcode.py`, NOMI-007) checks the barcode; the resolver uses the
   10 NDC digits it carries.
2. Exactly one real package, in the NDC directory or on any label, may have the scanned 10 digits
   as its own NDC, and it must be in the directory. Matching on the digits, not just the NDC11,
   matters because two different NDC10s can pad to one NDC11 (`12345-0678-9` and `12345-678-09`).
   Checking the labels too stops a box whose NDC is only on a label from resolving to a different
   directory package. This only covers packages in `spl_products`: the SPL ingest leaves out the
   package codes of kit parts, so a kit part is not protected this way. None of today's kit-part
   codes shares its digits with another package.
3. The package's label product comes from `spl_products`. When the directory names a label
   (`spl_set_id`), only that label is accepted. Without one, the package must be on exactly one
   label.
4. Active ingredients come from `spl_ingredients` for that label's `(spl_set_id, product_index)`,
   not the set id alone, because one label can hold products with different strengths. Bronze keeps
   one version of each label, so no version check is needed here.
5. Every ingredient must meet the product schema: a UNII, name, unit and positive strength, and
   `per_amount` and `per_unit` together with a positive amount.
6. The label must list as many active ingredients as the directory does, when the directory lists
   any (about 1% of directory rows list none, stored as an empty list, and then the check is skipped).
7. The directory must give a brand name and a generic name, as the product schema requires.

| Status | Meaning |
| --- | --- |
| `resolved` | All of the above hold; the product is written to `product.parquet` |
| `homeopathic` | Homeopathic, with no label in the OTC download; identified from the directory only |
| `invalid_format`, `bad_check_digit`, `not_ndc_barcode` | The barcode parser rejected it |
| `not_found` | No directory package has the scanned digits (it may be on a label only) |
| `ambiguous_ndc` | The same 10 digits split two ways are two real packages; this never happens for today's directory packages |
| `missing_label` | In the directory, but no OTC label lists it with the scanned digits |
| `label_mismatch` | On a label, but not the one the directory names |
| `ambiguous_label` | On several labels and the directory names none, or listed twice on the named label |
| `missing_ingredients` | The label product lists no active ingredients |
| `kit` | A kit; ingredients are per part, which the product record cannot hold yet |
| `invalid_ingredients` | An ingredient breaks the product schema's rules |
| `ingredient_conflict` | The label and the directory list a different number of actives; today every case is an ingredient name containing ";", which openFDA's directory splits in two |
| `missing_name` | The directory gives no brand or generic name |
| `invalid_package_ndc`, `ndc_mismatch` | The directory's own package NDC is malformed or disagrees with its NDC11 |

## Outputs

`product.parquet` holds only `resolved` packages, with the product schema's field names: `ndc11`,
`spl_set_id`, `spl_version`, `brand_name`, `generic_name`, `labeler`, `dosage_form`,
`marketing_category` (as the schema's enum value) and `ingredients`. `otc_category`, `uses` and
`scope` are added by NOMI-026 and NOMI-047, so this file does not yet pass the product schema;
NOMI-026 should validate the final records. Homeopathic packages without a label (status
`homeopathic`) cannot be valid product records yet; NOMI-026 can build them from
`identity_results.parquet` and the directory. The few homeopathic packages that do match a label
resolve like any other package and appear here.

`identity_results.parquet` has one row per package: its barcode, status and directory matches.

## Coverage

Each package in the directory gets the barcode it would carry (`3` + NDC10 + check digit), built
from the dashed NDC10 (NDC11 padding cannot be undone safely), and is resolved like a scan.
Sample packages are skipped, since they are not sold.

The target is 95% of scored packages, from system design 5.2 and section 8; the ticket's sprint
milestone was 90%. Homeopathic products are not scored (system design 5.2), so they are reported
apart, with their own list of misses and an overall figure that counts them as found when the
directory identifies them.

This measures the lookup, not real boxes: store-brand barcodes that do not follow the `3` + NDC
pattern need the overrides and name search in system design 5.2.
