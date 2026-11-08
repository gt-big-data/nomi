# pipeline

Python pipeline that turns public FDA data into the dataset the app ships with. Python 3.12, uv,
Polars, DuckDB, lxml, Pydantic. Tooling setup lands in NOMI-001.

## Getting raw data

Raw data lives in the Hugging Face dataset [`nomi-bdbi-gt/nomi-raw-data`](https://huggingface.co/datasets/nomi-bdbi-gt/nomi-raw-data)
(see ADR-0003). Copy `.env.example` to `.env`, then:

```bash
uv run pipeline fetch all
```

This downloads `data/raw/ndc/`, `data/raw/dailymed-otc/`, and `data/raw/faers/` and verifies
checksums. Already-fresh files are skipped. To fetch a single source:

```bash
uv run pipeline fetch ndc
uv run pipeline fetch dailymed-otc
uv run pipeline fetch faers
```

The dataset is public, so no token or `.env` is needed to fetch; `RAW_STORE` defaults to it.
`RAW_STORE` can be any fsspec URL (`hf://`, `s3://`, a local folder), and can pin a snapshot
with `@<commit>` after the dataset name.

### Mirroring new data

Only needed when a source updates. You need write access to the dataset: run
`hf auth login` once or set a write-scoped `HF_TOKEN` in `.env`.
Mirroring adds files to the existing manifest and skips files that haven't changed, so rerunning it
on the whole FAERS folder uploads only the new quarter. Only files named like the source's own files
are uploaded (never `.partial` downloads or dotfiles). Mirror with `RAW_STORE` unpinned (no `@<commit>`).

```bash
uv run python pipeline/scripts/download_sources.py faers ~/nomi-downloads/faers
uv run python pipeline/scripts/mirror.py faers ~/nomi-downloads/faers
```

DailyMed is about 34 GB, almost all product images. Strip it to label XML (about 350 MB) first:

```bash
uv run python pipeline/scripts/download_sources.py dailymed-otc ~/nomi-downloads/dailymed
uv run python pipeline/scripts/slim_dailymed.py ~/nomi-downloads/dailymed ~/nomi-downloads/dailymed-xml
uv run python pipeline/scripts/mirror.py dailymed-otc ~/nomi-downloads/dailymed-xml
```

Only public FDA and NLM files go in this dataset. Never mirror RxNorm (UMLS license), user data,
or anything we produce.

## Stages

| Stage | Package | Output |
|---|---|---|
| fetch | `nomi_pipeline.fetch` | `data/raw/`: mirrored sources with checksums |
| ingest | `nomi_pipeline.ingest` | `data/bronze/`: NDC directory, label products, ingredients and sections, FAERS |
| identity | `nomi_pipeline.identity` | `data/silver/product.parquet`: barcode to product, category, scope |
| extract | `nomi_pipeline.extract` | `data/silver/label_facts.parquet`: warnings, uses, age limits, max dose |
| evidence | `nomi_pipeline.evidence` | `data/gold/signal.parquet`: FAERS signals by risk dimension |
| score | `nomi_pipeline.score` | Term tables, product scores, benchmarks, alternatives |
| build | `nomi_pipeline.build` | `data/build/nomi.sqlite` and manifest, published to R2 (NOMI-038) |

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
