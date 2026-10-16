# packages/schema

Shared data contracts between the pipeline and the app (NOMI-002). Changes need review from both
Platform and Data Analysis.

| Folder | Contents |
|---|---|
| `schemas/` | JSON Schemas: `product`, `ingredient-dimensions`, `term-tables`, `score-record`, `signal`, label extraction |
| `generated/` | TypeScript types and Pydantic models generated from the schemas. Do not edit by hand |
| `examples/` | Hand-verified reference products: Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil, store-brand diphenhydramine (NOMI-015) |
| `fixtures/` | Test vectors shared by Python and TypeScript, such as barcode parsing (NOMI-007) |
| `golden/` | Golden scoring vectors (product, profile, expected score) checked against both implementations in CI (NOMI-057) |
