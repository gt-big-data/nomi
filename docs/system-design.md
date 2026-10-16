# Nomi system design

This document describes how Nomi works in its intended end state, with the technical details behind
each part. The Nov 20 demo builds a subset of it; section 13 shows which parts exist at the demo and
which come later. For a gentler introduction and glossary, read `docs/nomi-101.md` first.

## 1. Goals and constraints

**What the system must do**

- Identify any OTC medicine from its barcode in under 300 ms, with no network connection.
- Give a 0-100 safety score personalized to the person taking it (age, pregnancy, conditions, other medications).
- Explain every point taken off, with a citation to its source.
- Suggest a safer product used for the same purpose, or say "ask your pharmacist".
- Cover every in-scope OTC product sold in the US, and stay current as FDA data changes.

**Constraints that shape the design**

- **Privacy:** user health data never leaves the device. We hold no accounts and no health records.
- **Explainability:** no black-box scores. Every number traces to a source a pharmacist can check.
- **Cost:** bootstrapped student team. Free tiers and public data only.
- **Commercial use:** every data source must allow it (no DrugBank).

## 2. Architecture overview

Nomi is split into an offline **pipeline** that does all the heavy work and a **phone app** that only
looks things up and adds numbers.

```
OUR SIDE                                              USER'S PHONE
--------                                              ------------
Public sources                                        Camera + Google ML Kit
  openFDA NDC, DailyMed, FAERS, RxNorm,                 barcode -> NDC candidates
  STOPP/START, ACB, published studies                        |
        |                                                    v
        v                                             nomi.sqlite (bundled, updated weekly)
Pipeline (Python, scheduled)                            product lookup
  fetch > ingest > identify > extract > evidence             |
  > rate > score > build > release gate                      v
        |                    ^                        Scoring engine
        v                    | reviews                  sum points for the on-device profile
nomi.sqlite + signed manifest                                |
        |            Review tool (pharmacists)               v
        v                                             Score, reasons, safer option
Cloudflare R2 (CDN)  ---- same file for every user ----> app
                                                      Encrypted local storage:
Supabase (thin): feedback, not-found reports,           profiles, cabinet, history
  reviewer accounts, audit log. No health data.  <---- anonymous reports only
```

**Key idea:** train and compute centrally, infer on the device. Everything that depends only on
public data is precomputed. The only thing computed on the phone is the final sum for the user's
profile, which is why no health data needs to leave it.

## 3. Components

| Component | Tech | Owner | Purpose |
|---|---|---|---|
| Pipeline | Python 3.12, uv, Typer, Polars, DuckDB, Parquet, lxml, Pydantic | Platform, Data Analysis | Turns public data into the dataset |
| Knowledge base | YAML in git, JSON Schema validated | Data Analysis | Curated, cited ingredient ratings |
| Shared contracts | JSON Schema, generated TS types and Pydantic models | Platform | One definition of every data format |
| Dataset | SQLite file + signed manifest on Cloudflare R2 | Platform | Everything the app needs, in one file |
| Mobile app | Expo (React Native, TypeScript), expo-router, Google ML Kit, SQLite | Visualization | Scanning, scoring, display |
| Dashboard | Static site on GitHub Pages | Visualization | Data quality and evidence explorer |
| Review tool | Next.js + Supabase auth | Platform, Visualization | Pharmacist review, gold sets, audit log |
| Thin backend | Supabase (Postgres, storage, row-level security) | Platform | Feedback, not-found reports, reviewer accounts |
| CI/CD | GitHub Actions, EAS Build | Platform | Tests, scheduled pipeline runs, app builds |

## 4. Data sources

| Source | What we use | Refresh | License |
|---|---|---|---|
| openFDA NDC directory | Every OTC product and package NDC, marketing category, label id | Weekly | Public domain |
| DailyMed SPL (Human OTC) | Full labels: ingredients with UNII and strength, Drug Facts sections | Weekly | Public domain |
| FAERS quarterly files | Adverse event reports, 2014 onward | Quarterly | Public domain |
| RxNorm (via UMLS) | Ingredient names and synonyms for matching FAERS text | Monthly | Free UMLS license, `SAB=RXNORM` only |
| STOPP/START, ACB scale | Expert criteria, mainly for older adults | Manual | Published; attribution required |
| Published meta-analyses | Effect sizes for the personalized model | Manual | Facts reused, text not copied |
| All of Us (research) | Real-world outcomes with denominators | Per study | Data use agreement; aggregate results only |

Raw downloads are mirrored once to R2 and pulled with `uv run pipeline fetch`. Raw data is never
committed to git.

## 5. Pipeline

### 5.1 Stages

| Stage | Input | Output | Notes |
|---|---|---|---|
| fetch | R2 mirror | `data/raw/` with checksums | One command per source |
| ingest | raw files | `data/bronze/*.parquet` | Typed tables; latest label version per set id; FAERS dedup by latest `caseversion` per `caseid` |
| identify | NDC directory, labels | `data/silver/product.parquet` | Package NDC to label to ingredients; OTC category; scope flags |
| extract | label sections | `data/silver/label_facts.parquet` | Rules plus LLM, see 5.3 |
| evidence | FAERS, RxNorm | `data/gold/signal.parquet` | Bayesian signals by risk dimension, age band, sex |
| rate | knowledge base, label facts, criteria | ingredient severities | Validated YAML; every value cited |
| score | severities, rubric or model | term tables, product scores, benchmarks, alternatives | See section 6 |
| build | all gold outputs | `nomi.sqlite` + `manifest.json` | See section 7 |
| release | build + previous release | published dataset | Release gate, see 5.4 |

Data layers live under `data/`: **bronze** (raw as tables), **silver** (cleaned and joined),
**gold** (final outputs), **build** (the app file). Every run writes a manifest recording input
versions, code commit and output hashes, so any score can be traced to the exact data and code that
produced it. Stages skip work when their inputs haven't changed.

### 5.2 Identity resolution

- A drug UPC-A barcode is `3` + NDC10 + check digit. The NDC10 can be split 4-4-2, 5-3-2 or 5-4-1, so
  the parser emits three NDC11 candidates; only one exists in FDA data.
- The same parser exists in Python (pipeline) and TypeScript (app), tested against one shared fixture file.
- Coverage is measured on barcodes generated from every package in the NDC directory, where the
  correct answer is known. Target: 95% or higher.
- Barcodes that don't follow the `3` + NDC pattern are handled with reviewed overrides and in-app
  name search.
- Each product gets an OTC category (from monograph and ingredients), consumer uses (pain, sleep,
  heartburn...), and a scope flag. Homeopathic products are shown as "not evaluated by FDA" and not
  scored. Drug-cosmetics (sunscreen, hand sanitizer, fluoride toothpaste) are out of scope at first.

### 5.3 Label extraction

- SPL labels mark each Drug Facts section with a LOINC code (for example `34071-1` Warnings), so
  sections are split reliably.
- **Rules** extract fields with standard wording: FDA-mandated warnings (Liver, Stomach bleeding,
  Heart attack and stroke, Reye's syndrome...), age limits, maximum daily dose, allergens.
- **LLM extraction** (Claude, Message Batches API, structured output, offline) handles variable fields:
  conditions to ask a doctor about, interacting drug classes, uses.
- Fields where both extractors agree are accepted automatically. Disagreements go to the review queue.
- Accuracy is measured per field against a pharmacist-annotated gold set. Prompt and model version are
  stored in provenance. Expected cost is under $50 per full run.

### 5.4 Release gate

A dataset is published only if:

1. All schema validations pass.
2. Invariant tests pass (for example: an NSAID is never green for 65+ with kidney disease; salicylates are a hard stop for children; more risk never raises a score).
3. Coverage thresholds hold (identity, extraction, knowledge base).
4. Golden vectors give identical results in Python and TypeScript.
5. A score diff against the previous release has been reviewed. Any product whose score moves more than a set threshold or changes tier goes to a pharmacist in the review tool before release.

## 6. Scoring

### 6.1 Concepts

- **Risk dimensions** (about 15): liver, GI bleeding, cardiovascular/blood pressure, kidney,
  anticholinergic/cognitive, sedation/falls, serotonergic and interactions, bleeding with
  anticoagulants, pediatric-specific, rebound/overuse, pregnancy/lactation, duplicate dosing,
  excipients, local/skin, efficacy evidence. Defined in `docs/scoring/dimensions.md`.
- **Personas:** adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding.
- **Modifiers:** conditions (hypertension, kidney or liver disease, glaucoma, enlarged prostate...) and
  medication classes (anticoagulants, MAOIs/SSRIs, other sedatives...).
- **Severity:** 0-3 per ingredient, dimension and persona, with a citation.
- **Hard stops:** rules that make a product red regardless of points, usually a label "do not use"
  for that persona or condition.

### 6.2 The scoring function

All models export the same additive form, so the app never changes when the model does.

```
points(product, profile) = sum over dimensions d of
                           combine_d( term[i, d, persona] + sum of term[i, d, modifier]
                                      for each ingredient i and each modifier in the profile )

score = clamp(100 - points, 0, 100)
tier  = red if any hard stop fires, else band(score)   # green 75+, yellow 50-74, red below 50
```

- `term[...]` values come from the term tables. Each row carries a citation id.
- `combine_d` merges ingredients within a dimension (for example, the highest contribution plus a
  stacking penalty when two ingredients hit the same dimension, such as two sedating antihistamines).
  The exact rule is defined in the rubric.
- Duplicate ingredients across products (acetaminophen in NyQuil and Tylenol) are flagged by the
  Medicine Cabinet rather than the single-product score.

### 6.3 Model versions

| Version | How term values are set | Status |
|---|---|---|
| **Rubric v0** | Fixed points per severity, written in `docs/rubric/v0.md`, reviewed by faculty | Demo |
| **Evidence-synthesis v1** | For each dimension, a Bayesian model of relative risk: a baseline per ingredient plus log relative-risk terms for age, sex, conditions, co-medications, dose and duration. Priors come from published effect sizes; age- and sex-stratified FAERS signals update them; pharmacist pairwise judgments calibrate the mapping from risk to points. Because log relative risks add up, the model exports directly as additive term tables. | Post-demo |
| **Validated v2** | Selected relationships checked against real-world outcomes in All of Us (for example NSAIDs and acute kidney injury by age and kidney disease) | Research |

Every version must beat the previous one on agreement with a held-out pharmacist panel (quadratic
weighted kappa), pass every invariant, and stay additive and explainable.

### 6.4 FAERS evidence

- Drug names are normalized to ingredients (exact, RxNorm synonyms, then fuzzy matching tuned on a
  hand-labeled set).
- Signals use the BCPNN information component with shrinkage:
  `IC = log2((observed + 0.5) / (expected + 0.5))`, with IC025 (lower 95% bound) above 0 counting as a signal.
- Computed per ingredient, MedDRA event group, age band and sex, then mapped to risk dimensions.
- Validated against public reference sets of known drug and event pairs (OMOP, EU-ADR).
- FAERS has no denominator, so signals are supporting evidence, not risk rates. Limitations
  (masking, notoriety bias, duplicates) are documented and shown in the dashboard.

### 6.5 Benchmarks and alternatives

- **Benchmarks:** for each use and persona, the pipeline exports percentile breakpoints of the score
  distribution. The phone places a personalized score among them ("better than 82% of pain relievers
  for you"). Products are never compared across uses.
- **Alternatives:** the pipeline precomputes candidates that share a use (preferring single-ingredient
  products). The phone ranks them for the active profile, drops any with a hard stop, and shows the
  tradeoff by dimension. If nothing is clearly better, it says "ask your pharmacist".

## 7. The dataset file

### 7.1 Format

One SQLite file, `nomi.sqlite`, target 20 MB compressed or less.

| Table | Key columns | Purpose |
|---|---|---|
| `meta` | dataset_version, model_version, rubric_version, built_at | Provenance shown in the app |
| `products` | ndc11 (PK), set_id, brand, generic, form, category, scope_flag, review_status | Barcode lookup |
| `product_ingredients` | ndc11, unii, strength, unit | Ingredients per product |
| `ingredients` | unii (PK), name | Display names |
| `product_uses` | ndc11, use | For benchmarks and alternatives |
| `label_warnings` | ndc11, warning_code | Mandated warnings found on the label |
| `terms` | unii, dimension, persona_or_modifier, points, citation_id | The scoring model |
| `hard_stops` | unii or ndc11, persona_or_modifier, reason, citation_id | Override rules |
| `benchmarks` | use, persona, breakpoints (JSON) | Percentile lookup |
| `alternatives` | ndc11, alt_ndc11, shared_use, tradeoff (JSON) | Candidate lists |
| `citations` | id, source, title, section, url | Sources behind every value |
| `templates` | id, dimension, severity, text | Explanation sentences |
| `products_fts` | FTS5 over brand, generic, ingredient names | Offline name search |
| `interactions` | class_a, class_b, severity, citation_id | Medicine Cabinet checks |

### 7.2 Distribution and updates

1. The build publishes `nomi-<version>.sqlite.zst` and `manifest.json` to R2, behind Cloudflare's CDN.
2. The manifest holds version, SHA-256, size, minimum app version and an Ed25519 signature.
3. The app ships with a bundled copy so it works on first launch with no network.
4. About once a week the app fetches the manifest. If newer and compatible, it downloads the file,
   checks hash and signature, and swaps it in atomically. The previous version is kept for rollback.
5. Every user downloads the same file, so the server learns nothing about what anyone scans.

## 8. Mobile app

### 8.1 Structure

```
apps/mobile/src/
  app/         screens: scanner, result, compare, onboarding, profiles, search, cabinet
  components/  UI components from the Figma library
  lib/         barcode parser, database access, dataset updater
  scoring/     scoring engine: lookups and sums only
  storage/     encrypted profile, cabinet and history storage
```

### 8.2 Scan flow

1. The app opens straight to the camera (react-native-vision-camera).
2. Google ML Kit detects UPC-A or EAN-13 on the device; the phone vibrates.
3. The barcode parser produces three NDC11 candidates; one indexed query finds the product.
4. The scoring engine sums term-table points for the active profile, applies hard stops, and computes the benchmark percentile.
5. The result screen shows the score, tier, who it's for, the dimension breakdown with citations, the explanation and alternatives.

Target: under 300 ms from barcode in frame to result, fully offline. Products found but not yet
verified show ingredients and label warnings with a "preliminary" badge. Unknown barcodes fall back
to manual entry and name search.

### 8.3 Scoring engine rules

- Only lookups and arithmetic. All modeling stays in the pipeline.
- A CI job runs golden vectors through both the Python and TypeScript implementations and fails on
  any difference, so the user always sees the score we checked.

### 8.4 Profiles and Medicine Cabinet

- Multiple profiles (me, my child, my parent), each with persona and optional conditions and medication types.
- Medicine Cabinet: products a user takes regularly. New scans are checked against it for duplicate
  ingredients (acetaminophen in two products) and class interactions from the `interactions` table.
- All stored locally and encrypted. The key lives in the iOS Keychain or Android Keystore.

## 9. Privacy and security

| Rule | How it's enforced |
|---|---|
| Health data stays on the device | No API accepts profile data; scoring runs locally |
| Nothing identifying in analytics | Only content-free events ("scan succeeded"); never product, profile or condition. Crash reports are scrubbed |
| No accounts for consumers | Nothing to breach; no login required |
| Optional sync (future) | End-to-end encrypted; server stores ciphertext it can't read |
| Reports are anonymous | Feedback and not-found reports contain barcode, dataset version and an optional label photo, never profile data |
| Datasets can't be tampered with | Signed manifest checked before swapping |
| No training on user data | Unless a user opts in to a separate research program |

This keeps Nomi outside most health-data obligations (FTC Health Breach Notification Rule, Washington's
My Health My Data Act). Legal review is tracked in NOMI-021. Decisions are recorded in
`docs/adr/0002-privacy.md`.

## 10. Thin backend and review tool

**Supabase** (free tier) holds only non-health data:

| Table | Contents |
|---|---|
| `feedback` | ndc11, dataset version, reason code, optional text |
| `not_found` | barcode, optional label photo path |
| `reviewers` | pharmacist and annotator accounts with credentials |
| `reviews` | item, decision, before and after values, reviewer, timestamp (append-only audit log) |
| `pairwise_judgments` | product A, product B, profile, which is riskier, reviewer |

Row-level security allows anonymous inserts to `feedback` and `not_found` only, with rate limits.

**Review tool** (Next.js): invite-only queues for extraction disagreements, knowledge base changes,
score diffs from the release gate, explanation templates, gold-set annotation, and pairwise "which is
riskier for this profile" judgments that calibrate the scoring model. Every decision is logged with
the reviewer's credentials.

## 11. Operations

| Concern | Approach |
|---|---|
| Scheduling | GitHub Actions cron: weekly NDC and DailyMed; quarterly FAERS; manual runs anytime |
| Reproducibility | Run manifests with input hashes and code commit; deterministic outputs |
| Monitoring | Dashboard regenerated each run: coverage, extraction agreement, knowledge base progress, signals |
| App releases | EAS Build to TestFlight and Play testing tracks, then the stores |
| Data releases | Independent of app releases, through the release gate |
| Rollback | Previous dataset kept on the device and on R2 |
| Disputed scores | In-app report, review queue, fix at the rubric or knowledge base level, never one product by hand |

## 12. Testing and evaluation

| What | How | Target |
|---|---|---|
| Barcode parsing | Shared Python and TypeScript fixtures | 100% pass |
| Identity resolution | Generated barcodes from every package NDC; real boxes before releases | 95% or higher correct |
| Label extraction | Per-field precision and recall vs pharmacist gold set | Mandated warnings 98% recall or higher |
| FAERS name matching | Hand-labeled strings | 97% precision or higher |
| Signal detection | AUC on OMOP / EU-ADR reference sets | Beat raw reporting odds ratio |
| Scores | Invariants, golden vectors, pharmacist panel agreement | All invariants pass; each model beats the last |
| Phone and pipeline parity | Golden vectors in CI | Identical |
| App performance | Timed scans on low-end phones | Under 300 ms offline |
| Accessibility | VoiceOver, TalkBack, large text | Full flow usable |

## 13. Demo scope vs end state

| Part | Nov 20 demo | End state |
|---|---|---|
| Coverage | Pipeline runs on all OTC products; four aisles fully verified (pain/fever, allergy/sleep, cough/cold, digestive) | All in-scope OTC products verified |
| Scoring model | Rubric v0 | Evidence-synthesis v1, then validated v2 |
| Clinical review | Faculty review of the rubric if a partner is in place | Ongoing pharmacist review through the review tool |
| Pipeline runs | Manual | Scheduled with release gate |
| Dataset updates | Bundled in the app | Signed over-the-air updates |
| Backend | None | Supabase for feedback, reports and reviewers |
| Medicine Cabinet | Not built | On-device with duplicate and interaction checks |
| Distribution | Dev builds on team phones | App Store and Google Play |
| B2B | None | Read-only API serving the same dataset to partners |

## 14. Cost

| Item | Cost |
|---|---|
| Cloudflare R2 (raw data, datasets, CDN) | Free tier: 10 GB storage, no download fees |
| GitHub Actions and Pages | Free for public repos |
| Supabase | Free tier |
| LLM label extraction | Under $50 per full run, a few runs per year |
| Apple developer account | $99 per year |
| Google Play developer account | $25 one time |
| Servers for scoring | None |

## 15. Known risks and mitigations

| Risk | Mitigation |
|---|---|
| Barcode without an embedded NDC | Reviewed overrides, name search, not-found reports |
| Missing or odd label sections | Preliminary badge with ingredients and warnings |
| Wrong rating or score | Citations on every value, invariants, release-gate review, in-app disputes |
| FAERS bias and noise | Shrinkage, stratification, used only as supporting evidence |
| Phone and pipeline disagree | Golden-vector parity check blocks merges |
| Stale data | Scheduled runs; dataset date shown in the app |
| Regulatory questions (FDA device software, liability) | Information framing, disclaimers, legal review (NOMI-021) |
| Brand disputes | Published rubric, consistent rules, citations |
