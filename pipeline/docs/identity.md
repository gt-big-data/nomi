# NOMI-025: package identity

Run from the repository root after `pipeline ingest ndc` and `pipeline ingest spl`:

```sh
uv run pipeline identity resolve
```

It reads `ndc.parquet`, `spl_products.parquet` and `spl_ingredients.parquet` from
`Settings.bronze_dir` and writes `product.parquet` and `identity_results.parquet` to
`Settings.silver_dir`, plus the report at `pipeline/reports/identity_coverage.md`
(`--report PATH` to change it). It exits 1 below 90% coverage, after writing everything.

## How a barcode resolves

1. The barcode parser (`identity/barcode.py`, NOMI-007) gives up to three NDC11 candidates.
2. Exactly one candidate must be in the NDC directory. Two or more is `ambiguous_ndc`: the same
   10 digits split two ways are two real packages, and the barcode cannot tell them apart.
3. The package's label product comes from `spl_products` (latest version of each label). If the
   package is on more than one label, the directory's `spl_set_id` picks one; otherwise it is
   `ambiguous_label`.
4. Active ingredients come from `spl_ingredients` for that label's `(spl_set_id, product_index)`,
   not the set id alone, because one label can hold products with different strengths.
5. Every ingredient needs a UNII, name, unit and a positive strength, or the result is
   `invalid_ingredients`.

Other outcomes are kept, never guessed:

| Status | Meaning |
| --- | --- |
| `not_found` | No candidate is in the directory |
| `missing_label` | The package is in the directory but on no OTC label |
| `missing_ingredients` | The label product lists no active ingredients |
| `kit` | A kit; ingredients are per part, which the product record cannot hold yet |
| `homeopathic` | Homeopathic, with no label in the OTC download; identified from the directory only |
| `invalid_package_ndc`, `ndc_mismatch` | The directory's own package NDC is malformed or disagrees with its NDC11 |

## Coverage

Each package in the directory gets the barcode it would carry (`3` + NDC10 + check digit), built
from the dashed NDC10 (NDC11 padding cannot be undone safely), and is resolved like a scan.
Sample packages are skipped, since they are not sold.

Homeopathic products are shown as "not evaluated by FDA" and not scored (system design 5.2). Their
labels are not in DailyMed's OTC download, so they are kept in `product.parquet` with no
ingredients and counted apart from the 90% target.

This measures the lookup, not real boxes: store-brand barcodes that do not follow the `3` + NDC
pattern need the overrides and name search in system design 5.2.

`product.parquet` is the identity stage only. OTC category, scope (NOMI-026) and uses (NOMI-047)
are added later.
