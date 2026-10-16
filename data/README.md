# data/

Local working data for the pipeline. Everything here except this file is gitignored.

| Folder | Contents | Produced by |
|---|---|---|
| `raw/` | Untouched downloads from the R2 mirror, with checksums | `uv run pipeline fetch` |
| `bronze/` | Typed Parquet tables, one per source table | `ingest` stage |
| `silver/` | Cleaned and joined tables: products, label facts, crosswalks, FAERS pairs | `identity`, `extract`, `evidence` stages |
| `gold/` | Scores, signals, benchmarks, alternatives | `evidence`, `score` stages |
| `build/` | `nomi.sqlite` and its manifest for the app | `build` stage |

To get started, run `uv run pipeline fetch all` (available after NOMI-008).
