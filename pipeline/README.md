# pipeline

Python pipeline that turns public FDA data into the dataset the app ships with. Python 3.12, uv,
Polars, DuckDB, lxml, Pydantic. Tooling setup lands in NOMI-001.

## Stages

| Stage | Package | Output |
|---|---|---|
| fetch | `nomi_pipeline.fetch` | `data/raw/`: mirrored sources with checksums |
| ingest | `nomi_pipeline.ingest` | `data/bronze/`: NDC directory, label products, ingredients and sections, FAERS |
| identity | `nomi_pipeline.identity` | `data/silver/product.parquet`: barcode to product, category, scope |
| extract | `nomi_pipeline.extract` | `data/silver/label_facts.parquet`: warnings, uses, age limits, max dose |
| evidence | `nomi_pipeline.evidence` | `data/gold/signal.parquet`: FAERS signals by risk dimension |
| score | `nomi_pipeline.score` | Term tables, product scores, benchmarks, alternatives |
| build | `nomi_pipeline.build` | `data/build/nomi.sqlite` and manifest, published to R2 |

## Other folders

| Folder | Contents |
|---|---|
| `knowledge/ingredients/` | Risk-dimension ratings per ingredient, one YAML file each, every value cited (NOMI-034, 035) |
| `knowledge/criteria/` | STOPP/START and ACB as structured data (NOMI-018) |
| `knowledge/templates/` | Explanation templates filled in on the phone (NOMI-048) |
| `knowledge/mandated_warnings.yaml` | FDA-required OTC warnings mapped to dimensions (NOMI-017) |
| `tests/fixtures/` | Label snippets, generated test barcodes, regression cases |
| `reports/` | Committed coverage and quality reports |
| `docs/` | Method write-ups, such as signal detection |

The knowledge base is reviewed like code: every change is a PR with citations.

## Identity resolution (NOMI-025)

`uv run pipeline identity resolve` joins the bronze directory and SPL tables,
writes `data/silver/product.parquet`, and reports every unresolved package in
`pipeline/reports/identity_coverage.md`. See [input contracts and coverage methodology](docs/identity.md).
The upstream ingestion interfaces are provisional until NOMI-009/010 merge.
