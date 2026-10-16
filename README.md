# Nomi

Scan any over-the-counter medicine in the pharmacy aisle and get a safety score personalized to who
it's for, the specific risks behind it with sources, and a safer option for the same use.

Built by the GT Big Data Big Impact Nomi team.

## How it works

1. **Identify.** The barcode on a drug box contains its NDC. We resolve it to the exact product,
   ingredients and strengths using FDA's NDC directory and DailyMed labels.
2. **Extract.** Rules and an offline LLM pull facts from each label's Drug Facts panel: uses, age
   limits, maximum dose, FDA-mandated warnings, conditions to ask a doctor about.
3. **Evidence.** Each ingredient is rated on about 15 risk dimensions (liver, GI bleeding, blood
   pressure, kidney, cognition, sedation, interactions and more) from mandated warnings, published
   criteria (STOPP/START, ACB) and FAERS adverse event signals. Every value is cited.
4. **Score.** A transparent rubric turns those ratings into a 0-100 score per persona and health
   condition, exported as lookup tables.
5. **On the phone.** The full dataset ships to the app as one SQLite file. The app computes the
   personalized score locally, so scans are instant, work offline, and health data never leaves
   the device.

## Learn more

- `docs/nomi-101.md`: product overview and glossary, start here
- `docs/system-design.md`: full architecture and technical details
- `planning/`: sprint plan and backlog

## Repository layout

```
apps/
  mobile/          Expo (React Native, TypeScript) consumer app
  dashboard/       Static data quality and evidence dashboard (GitHub Pages)
packages/
  schema/          Shared data contracts (JSON Schema), reference products, test vectors
pipeline/          Python data and scoring pipeline
  src/nomi_pipeline/
    fetch/         Raw data from the R2 mirror
    ingest/        NDC directory, DailyMed labels, FAERS, RxNorm
    identity/      Barcode parsing and product resolution
    extract/       Label fact extraction (rules and LLM)
    evidence/      FAERS normalization and signals
    score/         Rubric, term tables, benchmarks, alternatives
    build/         On-device SQLite dataset and releases
  knowledge/       Curated, cited knowledge base (reviewed through PRs)
  tests/           Tests and fixtures
docs/
  adr/             Architecture decision records
  scoring/         Risk dimensions and personas
  rubric/          Scoring rubric versions
  demo/            Demo script
  research/        User research syntheses (anonymized)
planning/          Backlog, sprint plan and issue tooling
data/              Local pipeline data (gitignored)
```

## Getting started

Tooling setup (pnpm, uv, linters, CI) lands in NOMI-001. Until then, see `planning/README.md` for the
sprint plan and the GitHub issues for what to pick up.

## Data and privacy

- All drug data comes from public sources (openFDA, DailyMed, FAERS, RxNorm). See `docs/data-sources.md`.
- Raw and generated data is never committed. Use `uv run pipeline fetch`.
- User profiles, conditions and scan history stay on the device. See `docs/adr/0002-privacy.md`.

Nomi provides information from public FDA data and published criteria. It is not medical advice.
