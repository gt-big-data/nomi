# Nomi backlog: sprints to the Nov 20 demo

One ticket = one person, one week. New to the project? Read `docs/nomi-101.md`. To write a ticket, follow `planning/ticket-template.md`.

`create_issues.py` parses this file, so keep the format. Post-demo epics are in `post-demo.md`.

---

# Sprint 1: Oct 16 to Oct 22

## NOMI-001: Set up repo tooling, CI and branch protection
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** Make the repo install with one command and block broken code from reaching `main`.

**Deliverable:** pnpm and uv workspaces, `.github/workflows/ci.yml`, `CONTRIBUTING.md` and branch protection on `main`

**Tasks**
- [ ] Set up pnpm workspace and uv project with Python 3.12
- [ ] Add lint, format and type-check config plus pre-commit hooks
- [ ] Add CI that runs lint, typecheck and tests per package
- [ ] Protect `main`: PR, 1 approval, green CI, squash only
- [ ] Write `CONTRIBUTING.md`, CODEOWNERS, PR and issue templates

**Done when:** `pnpm install && uv sync` works on a fresh clone on macOS and Linux, and a PR with a lint error is blocked.

---

## NOMI-002: Define shared data contracts as JSON Schemas
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

**Goal:** Write the shared data formats every team codes against, with generated types for the app and pipeline.

**Deliverable:** Five schemas plus `common.schema.json` in `packages/schema/schemas/`, generated types in `packages/schema/generated/`

**Tasks**
- [ ] Write `product`, `ingredient-dimensions`, `term-tables`, `score-record` and `signal` schemas
- [ ] Require a citation on every non-zero severity and modifier
- [ ] Add a valid and an invalid sample per schema, tested in CI
- [ ] Generate TypeScript types and Pydantic models with a `codegen` script

**Done when:** All schemas merged, CI fails when generated files are stale, and both cofounders approve.

---

## NOMI-003: Write the architecture and privacy ADRs
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** Record how scores are computed and that health data stays on the phone.

**Deliverable:** `docs/adr/0001-architecture.md` and `docs/adr/0002-privacy.md`

**Tasks**
- [ ] Write ADR-0001 with the chosen design and four rejected options
- [ ] Write ADR-0002 with the privacy rules, legal points marked pending law clinic review
- [ ] Add a privacy checklist to the PR template and link both ADRs from `README.md`

**Done when:** Both ADRs are merged with Status `accepted` and approved by both cofounders.

**Notes:** ADR means architecture decision record: a short doc explaining one decision and why.

---

## NOMI-004: Write the demo script and present it
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** Give every team one shared picture of the Nov 20 demo and which tickets make it work.

**Deliverable:** `docs/demo/script.md`

**Tasks**
- [ ] Write the six demo beats in order
- [ ] List the tickets each beat depends on
- [ ] Add key dates: feature freeze Nov 12, code freeze Nov 17, blind test Nov 18
- [ ] Present the script at the Oct 19 kickoff

**Done when:** Script is merged, presented at kickoff and linked in every team channel.

---

## NOMI-005: Book a first pharmacy faculty meeting
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** Start a partnership with pharmacy faculty who can validate our scores.

**Deliverable:** A one-page pitch PDF and a contact tracking sheet in the team shared drive

**Tasks**
- [ ] Write the one-page partnership pitch
- [ ] List at least 10 Georgia pharmacy faculty in the tracking sheet
- [ ] Send personal emails, including APhA-ASP chapters at Mercer, UGA and PCOM Georgia

**Done when:** At least 10 emails sent and at least 1 meeting booked, both recorded in the sheet.

**Notes:** Post counts only on this issue; keep contact details out of the repo.

---

## NOMI-006: Audit data source licenses
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** Confirm we are allowed to use each dataset commercially before we build on it.

**Deliverable:** `docs/data-sources.md`

**Tasks**
- [ ] Add one row per source with URL, license, commercial use, attribution and refresh cadence
- [ ] Cover openFDA NDC, FAERS, DailyMed, RxNorm, ACB, STOPP/START, Beers, MedDRA and DrugBank
- [ ] Record the RxNorm UMLS requirement and the Beers decision
- [ ] Write the no-raw-data-in-git rule; list questions for the law clinic (NOMI-021)

**Done when:** Doc is merged with every source filled in or marked "open question", and reviewed by the other cofounder.

---

## NOMI-020: Set up the pipeline project and CLI
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

**Goal:** Give the backend pipeline a runnable skeleton so every data ticket plugs into the same CLI, config and tests.

**Deliverable:** `pipeline/pyproject.toml`, a `uv run pipeline` CLI, `pipeline/src/nomi_pipeline/config.py` and `.env.example`

**Tasks**
- [ ] Create the uv package with a Typer CLI entry point named `pipeline`
- [ ] Add empty commands for each stage: fetch, ingest, identity, extract, evidence, score, build
- [ ] Load data paths and R2 credentials from `.env` in `config.py`
- [ ] Add logging and a pytest setup with one passing test

**Done when:** `uv run pipeline --help` lists every stage and `uv run pytest pipeline` passes in CI.

**Notes:** NOMI-001 sets up repo-wide tooling; this ticket is the pipeline's own skeleton. NOMI-008, 009 and 010 add their commands here.

---

## NOMI-007: Turn scanned barcodes into NDC codes
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint) | **Extra:** good first issue

**Goal:** Turn scanned barcode digits into possible NDC codes, in both Python and TypeScript.

**Deliverable:** `pipeline/src/nomi_pipeline/identity/barcode.py` and `apps/mobile/src/lib/barcode.ts`

**Tasks**
- [ ] Write `ndc_candidates` (Python) and `ndcCandidates` (TypeScript)
- [ ] Add at least 30 cases to `packages/schema/fixtures/barcodes.json`
- [ ] Test both versions against the same fixture file

**Done when:** Both functions return identical output for every case, covering every status.

**Notes:** NDC is FDA's product code; drug barcodes usually contain it. Pairs with the ML Kit scanner in NOMI-011; the Python copy is used by the pipeline.

---

## NOMI-008: Mirror raw data to R2 and build fetch
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint), NOMI-006 (same sprint), NOMI-020 (same sprint)

**Goal:** Let any developer get all raw data with one command.

**Deliverable:** An R2 bucket with `ndc/`, `dailymed-otc/` and `faers/`, plus `uv run pipeline fetch <source>`

**Tasks**
- [ ] Mirror each source to R2 with a checksum `manifest.json`
- [ ] Use a read-only team token; keep write keys in GitHub Actions secrets
- [ ] Build `pipeline fetch` to download into `data/raw/` and verify checksums

**Done when:** A new member gets all raw data with one command using `pipeline/README.md`, and a corrupted file is caught by a test.

**Notes:** R2 is Cloudflare's file storage. Never commit data or credentials.

---

## NOMI-009: Ingest the openFDA NDC directory
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-008 (same sprint), NOMI-020 (same sprint)

**Goal:** Turn the raw NDC directory into one clean table of human OTC products.

**Deliverable:** `uv run pipeline ingest ndc` writing `data/bronze/ndc.parquet`

**Tasks**
- [ ] Keep only `HUMAN OTC DRUG` products
- [ ] Normalize every package NDC to 11 digits and log bad ones
- [ ] Save row counts and null rates to `data/bronze/ndc.stats.json`
- [ ] Add a DuckDB `ndc` view and tests with a small fixture

**Done when:** Running it twice gives identical output and `uv run pytest pipeline/tests/ingest` passes.

---

## NOMI-010: Parse DailyMed OTC labels
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-008 (same sprint), NOMI-020 (same sprint)

**Goal:** Extract products and ingredients from every DailyMed OTC label.

**Deliverable:** `uv run pipeline ingest spl` writing `spl_products.parquet` and `spl_ingredients.parquet` to `data/bronze/`

**Tasks**
- [ ] Parse set id, version, products and package NDCs from the latest label version
- [ ] Parse active ingredients with UNII and strength, and inactive ingredients
- [ ] Log failures to `spl_parse_failures.parquet` and add fixture tests

**Done when:** At least 98% of OTC labels parse without error, with the number in the PR.

**Notes:** SPL is the XML format FDA labels use. UNII is FDA's ingredient id.

---

## NOMI-011: Build the ML Kit barcode scanner in the Expo app
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

**Goal:** Get a phone app that opens to the camera and reads OTC barcodes on-device with Google ML Kit.

**Deliverable:** Expo app in `apps/mobile` with ML Kit scanning, installed on one iPhone and one Android phone

**Tasks**
- [ ] Create a TypeScript Expo app with expo-router (dev build)
- [ ] Add camera plus Google ML Kit barcode scanning on iOS and Android
- [ ] Read UPC-A and EAN-13 offline; buzz and show the digits on scan
- [ ] Record the ML Kit library choice and build steps in `apps/mobile/README.md`

**Done when:** On both phones, median of 10 timed scans is 300 ms or less, with timings in the PR.

**Notes:** ML Kit runs on the phone, so scanning works with no signal. ML Kit libraries don't run in Expo Go, so use a dev build.

---

## NOMI-012: Build the Figma tokens and component library
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** Give designers and developers one shared set of colors, type and components.

**Deliverable:** A published Figma library "Nomi Library", linked in `apps/mobile/README.md`

**Tasks**
- [ ] Create light and dark color tokens, including score tier colors
- [ ] Add a type scale and spacing scale
- [ ] Build the 8 core components, such as score badge and citation chip
- [ ] Add a contrast table and color-blind checks page

**Done when:** Every score state passes WCAG AA contrast in both modes and every tier is distinguishable in all four color-vision views.

---

## NOMI-013: Build a clickable prototype of the demo
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-004 (same sprint)

**Goal:** Show every screen the Nov 20 demo needs as one clickable flow.

**Deliverable:** Figma file "Nomi Demo Prototype", linked in the issue

**Tasks**
- [ ] Draw scanner, result, comparison, onboarding and profile screens
- [ ] Draw the preliminary, homeopathic, not found and hard stop states
- [ ] Label each screen with its data fields; report gaps to NOMI-002
- [ ] Walk 3 people outside the team through it

**Done when:** Every screen is reachable from the scanner and walkthrough feedback is logged in the issue.

---

## NOMI-014: Test three score visualization concepts
**Team:** visualization | **Priority:** P1 | **Sprint:** S1 | **Depends on:** none

**Goal:** Pick the clearest way to show the score and its breakdown, based on user tests.

**Deliverable:** `docs/design/score-visualization.md`

**Tasks**
- [ ] Design three score and three breakdown concepts with the same data
- [ ] Test them with 5 people; log anonymized notes in the issue
- [ ] Write up the choice and reasons
- [ ] Add the chosen design to the NOMI-012 library

**Done when:** 5 tests done and the decision doc is merged.

---

## NOMI-015: Hand-research five reference products
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-002 (same sprint)

**Goal:** Create five hand-checked example products every team can test against.

**Deliverable:** Five folders in `packages/schema/examples/` (Tylenol, Aleve, ZzzQuil, NyQuil, store-brand diphenhydramine)

**Tasks**
- [ ] Write `product.json` for each from its FDA label
- [ ] Write draft cited severities in `ingredient-dimensions.json`
- [ ] Write `expected-scores.json` for adult, 65+ with high blood pressure, and child 6-11
- [ ] Have a second person check every value against the label

**Done when:** All examples validate against the NOMI-002 schemas in CI.

---

## NOMI-016: Define risk dimensions, severity and personas
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** Define the terms every ingredient is scored on, with stable ids the code uses.

**Deliverable:** `docs/scoring/dimensions.md`

**Tasks**
- [ ] List about 15 risk dimensions with a real label example each
- [ ] Define the 0-3 severity scale with criteria and examples
- [ ] List 8 personas and at least 8 modifiers (conditions that change risk)
- [ ] Name the evidence sources allowed for each dimension

**Done when:** Merged with all five sections and approved by both cofounders and the Data Analysis team.

---

## NOMI-017: Catalogue FDA-mandated OTC warnings
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Goal:** List every FDA-required OTC warning so we can detect them on labels.

**Deliverable:** `pipeline/knowledge/mandated_warnings.yaml` and 50 snippets in `pipeline/tests/fixtures/warnings/`

**Tasks**
- [ ] Add each warning with wording variants, ingredients, dimension and citation
- [ ] Collect 50 real label snippets with expected warnings, at least 5 negatives
- [ ] Cover every catalogue entry at least twice
- [ ] Add a test that checks the YAML and fixtures

**Done when:** At least 10 warnings catalogued and `uv run pytest pipeline/tests/knowledge` passes.

---

## NOMI-018: Digitize STOPP/START and ACB criteria
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-006 (same sprint)

**Goal:** Turn the OTC-relevant parts of two clinical criteria lists into cited data files.

**Deliverable:** `pipeline/knowledge/criteria/stopp_start.yaml` and `pipeline/knowledge/criteria/acb.yaml`

**Tasks**
- [ ] Add one cited row per OTC-relevant item; never copy text verbatim
- [ ] List skipped criteria and reasons in the PR
- [ ] Add a validation test in `pipeline/tests/knowledge/test_criteria.py`
- [ ] Have a second person spot-check 20 rows

**Done when:** `uv run pytest pipeline/tests/knowledge` passes in CI and the spot check is in the PR.

---

## NOMI-019: Build the RxNorm-to-UNII ingredient crosswalk
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S1 | **Depends on:** NOMI-006 (same sprint)

**Goal:** Link each OTC ingredient's FDA id to its RxNorm ids and name synonyms.

**Deliverable:** `data/silver/ingredient_crosswalk.parquet` and `pipeline/reports/crosswalk_unlinked.csv`

**Tasks**
- [ ] Apply for a free UMLS license; never share the credentials
- [ ] Mirror RxNorm to R2, fetchable with `uv run pipeline fetch rxnorm`
- [ ] Build the crosswalk from one command
- [ ] Export unlinked ingredients with a reason

**Done when:** At least 98% of OTC ingredients from NOMI-009 are linked and `uv run pytest pipeline/tests/identity` passes.

---

# Sprint 2: Oct 23 to Oct 29

## NOMI-021: Get free legal advice and write decision memo
**Team:** cofounders | **Priority:** P0 | **Sprint:** S2 | **Depends on:** none

**Goal:** Get free advice on Nomi's legal, IP and FDA risks and record our decisions before outside users touch the app.

**Deliverable:** A private decision memo in the cofounders' shared drive and a one-page team summary

**Tasks**
- [ ] Summarize GT IP policy and Big Data Big Impact spin-out rules
- [ ] Apply to CREATE-X, or note why not
- [ ] Hold a law-school clinic consult covering all six questions
- [ ] Decide who owns the Apple and Google developer accounts
- [ ] Write the memo and present the team summary at Friday demo

**Done when:** Clinic answers to all six questions are in the memo, and no memo content is in the repo.

---

## NOMI-022: Interview 10 OTC buyers and synthesize findings
**Team:** cofounders | **Priority:** P1 | **Sprint:** S2 | **Depends on:** none

**Goal:** Learn how people buy OTC medicine so explanations and onboarding use their words.

**Deliverable:** `docs/research/interviews-round-1.md`

**Tasks**
- [ ] Write the interview script and add it to the file
- [ ] Run 10 interviews in a 5 / 3 / 2 mix
- [ ] Write themes: pains, trust signals, privacy concerns, vocabulary
- [ ] Keep raw notes in the private shared drive only

**Done when:** 10 interviews done, synthesis merged with no names or identifying details, presented at Friday demo.

---

## NOMI-023: Split DailyMed labels into Drug Facts sections
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-010

**Goal:** Break every OTC label into its Drug Facts sections so the label extractors can read them.

**Deliverable:** `data/bronze/spl_sections.parquet` via `uv run pipeline ingest sections`, plus `pipeline/reports/spl-section-coverage.md`

**Tasks**
- [ ] Parse all 12 Drug Facts section types, including nested ones
- [ ] Keep both raw and cleaned text for every row
- [ ] Test on at least 5 fixture labels
- [ ] Commit the per-section coverage report with failure count

**Done when:** The command writes the table and `uv run pytest pipeline/tests/ingest` passes.

---

## NOMI-024: Load and deduplicate FAERS reports since 2014
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-008

**Goal:** Load FDA adverse event reports into clean tables so Data Analysis can find safety signals.

**Deliverable:** Seven tables in `data/bronze/faers/` via `uv run pipeline ingest faers`, plus `pipeline/reports/faers-dedup.md`

**Tasks**
- [ ] Load all seven tables for every quarter from 2014Q1
- [ ] Keep only the latest version of each case
- [ ] Keep drug roles, age, sex, indications and all drugs per report
- [ ] Commit per-quarter dedup stats

**Done when:** Two runs on the same inputs give identical files and fixture tests pass.

---

## NOMI-025: Resolve barcodes to products
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-007, NOMI-009, NOMI-010, NOMI-020

**Goal:** Turn a scanned barcode into the exact product and its ingredients, so the app knows what was scanned.

**Deliverable:** `data/silver/product.parquet` and a coverage report in `pipeline/reports/identity_coverage.md`

**Tasks**
- [ ] Look up each barcode's NDC candidates in the NDC directory
- [ ] Join the match to its DailyMed label to get ingredients and strengths
- [ ] Flag barcodes with zero or multiple matches
- [ ] Generate a test barcode for every OTC package and list every miss

**Done when:** At least 90% of generated test barcodes resolve to the right product by Oct 29.

**Notes:** A drug barcode is `3` + the 10-digit NDC + a check digit, so we can build one for every package in FDA's list and know the right answer.

---

## NOMI-026: Tag every product with OTC category and scope
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-009, NOMI-010

**Goal:** Label each product with its OTC category or mark it homeopathic or out of scope, so we only score real medicines.

**Deliverable:** `pipeline/knowledge/otc_categories.yaml`, new `otc_category` and `scope_flag` columns on `data/silver/product.parquet`, and `pipeline/reports/category-counts.md`

**Tasks**
- [ ] Write the category list with matching rules
- [ ] Flag homeopathic products and non-medicines like sunscreen
- [ ] Spot check 30 products and record results
- [ ] Commit counts per category and flag

**Done when:** Every product has a category or scope flag (no nulls) and tests pass.

---

## NOMI-027: Build app theme and core UI components
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-011, NOMI-012

**Goal:** Turn the Figma library into reusable app code so every screen looks consistent.

**Deliverable:** `apps/mobile/src/theme/`, eight components in `apps/mobile/src/components/`, and a gallery at `apps/mobile/src/app/dev/gallery.tsx`

**Tasks**
- [ ] Code light and dark color, type and spacing tokens
- [ ] Build the eight components with screen-reader labels
- [ ] Show every component in every state on the gallery screen
- [ ] Attach light and dark screenshots to the PR

**Done when:** Gallery matches Figma, no hard-coded colors, and no clipped text at the largest text size.

---

## NOMI-028: Build onboarding and profile screens
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-013, NOMI-016

**Goal:** Ask who the user scans for and their health details quickly, with no account needed.

**Deliverable:** Screens in `apps/mobile/src/app/onboarding/` and a `Profile` type in `apps/mobile/src/storage/profile.ts`

**Tasks**
- [ ] Build five question screens plus a done screen
- [ ] Make every screen skippable, defaulting to adult 18-64
- [ ] Use condition and medication lists from NOMI-016
- [ ] Confirm no network requests during onboarding

**Done when:** 3 people finish onboarding in under 60 seconds each, with times in the PR.

---

## NOMI-029: Build result screen v1
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-015, NOMI-027 (same sprint)

**Goal:** Show a product's score, ingredients and explanation so users understand what they scanned.

**Deliverable:** Result screen in `apps/mobile/src/app/result/` and loader `apps/mobile/src/lib/examples.ts`

**Tasks**
- [ ] Load the five reference products from `packages/schema/examples/`
- [ ] Show score, tier word, ingredients, explanation and disclaimer
- [ ] Show the hard-stop banner when it applies
- [ ] Add screenshots next to Figma frames in the PR

**Done when:** All five reference products render and match Figma, reviewed by a teammate.

---

## NOMI-030: Connect scanning to every result state
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-011

**Goal:** Make every possible scan outcome reachable so we can build and test each one.

**Deliverable:** Scan navigation in `apps/mobile/src/app/` and `apps/mobile/src/fixtures/scanFixtures.ts`

**Tasks**
- [ ] Wire camera to haptic to result on iPhone and Android
- [ ] Build states: scored, preliminary, homeopathic, not found, invalid
- [ ] Add a dev menu entry that opens each state
- [ ] Make back always return to a working camera

**Done when:** All five states are reachable by fixture scan and dev menu, and homeopathic and not-found never show a score.

---

## NOMI-031: Build rule-based label extractor
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-017, NOMI-023 (same sprint)

**Goal:** Pull warnings, age limits and dosing facts from labels using text rules.

**Deliverable:** `pipeline/src/nomi_pipeline/extract/rules.py` with tests in `pipeline/tests/extract/test_rules.py`

**Tasks**
- [ ] Extract warnings, age limits, dosing and allergens with evidence text
- [ ] Write 5+ test cases per field group
- [ ] Agree field names with the NOMI-032 owner

**Done when:** Mandated-warning recall is at least 98% on the NOMI-017 fixtures.

**Notes:** Use the NOMI-017 label snippets until NOMI-023 lands.

---

## NOMI-032: Build LLM label extraction v1
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-002, NOMI-016

**Goal:** Use Claude to pull structured facts from label text and check it is affordable.

**Deliverable:** Extraction schema in `packages/schema/schemas/` and `pipeline/src/nomi_pipeline/extract/llm.py`

**Tasks**
- [ ] Define the nine-field extraction schema with generated types
- [ ] Run on 200 labels across categories
- [ ] Record model id and prompt hash on every row
- [ ] Report validation failures and cost per label in the PR

**Done when:** Projected cost for all in-scope labels is under $50 and no API key is in the repo.

---

## NOMI-033: Match FAERS drug names to ingredients
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S2 | **Depends on:** NOMI-019

**Goal:** Map messy FAERS drug names to our ingredients so side-effect reports count correctly.

**Deliverable:** `pipeline/src/nomi_pipeline/evidence/name_matcher.py` and `pipeline/tests/fixtures/faers_names_labeled.csv`

**Tasks**
- [ ] Hand-label 500 FAERS names, 50 double-labeled
- [ ] Match by exact name, then RxNorm synonyms, then fuzzy
- [ ] Expand combination names to all ingredients
- [ ] Tune the fuzzy threshold on the tuning half only

**Done when:** Precision is at least 97% on the held-out half, enforced by a test.

---

## NOMI-034: Rate pain, fever and digestive ingredients
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-016, NOMI-018

**Goal:** Rate how risky each ingredient in these aisles is for each persona, with sources.

**Deliverable:** 16 ingredient files in `pipeline/knowledge/ingredients/`, e.g. `acetaminophen.yaml`

**Tasks**
- [ ] Rate severity on every risk dimension and persona
- [ ] Cite every non-zero severity and modifier
- [ ] Have a second person spot check five values
- [ ] List any uncovered aisle ingredients in the PR

**Done when:** All 16 files pass schema validation with full citations.

---

## NOMI-035: Rate allergy, sleep and cough/cold ingredients
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-016, NOMI-018

**Goal:** Rate how risky each ingredient in these aisles is for each persona, with sources.

**Deliverable:** 12 ingredient files in `pipeline/knowledge/ingredients/`, e.g. `diphenhydramine.yaml`

**Tasks**
- [ ] Rate severity on every risk dimension and persona
- [ ] Cite every non-zero severity and modifier
- [ ] Have a second person spot check five values
- [ ] List any uncovered aisle ingredients in the PR

**Done when:** All 12 files pass schema validation, and every ingredient in these aisles' products is covered or explained.

---

# Sprint 3: Oct 30 to Nov 5

## NOMI-036: Review rubric with faculty partner
**Team:** cofounders | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-005, NOMI-049 (same sprint)

**Goal:** Get expert feedback on the scoring rubric and turn it into work for Sprint 4.

**Deliverable:** One `rubric-review` GitHub issue per change and a "Rubric v0 review feedback" tracking issue

**Tasks**
- [ ] Send the review packet 48 hours before the meeting
- [ ] Hold a one-hour review and file one issue per change
- [ ] Confirm the credit agreement in writing

**Done when:** All change issues are filed and linked before Sprint 4 planning (Nov 6).

**Notes:** If no faculty partner has signed on, run an internal review and file a follow-up issue.

---

## NOMI-037: Raise barcode coverage to 95%
**Team:** platform | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-025

**Goal:** Fix resolver misses so the demo's blind scan works.

**Deliverable:** Resolver fixes, `pipeline/knowledge/barcode_overrides.csv`, and `pipeline/tests/fixtures/identity_regression.csv`

**Tasks**
- [ ] Fix resolver misses by category
- [ ] Add reviewed overrides for barcodes with no NDC
- [ ] Add a regression row for every fixed barcode
- [ ] Update the coverage report with before and after numbers

**Done when:** At least 95% of generated test barcodes resolve correctly and identity tests pass.

---

## NOMI-038: Build and publish the SQLite dataset
**Team:** platform | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-002, NOMI-025

**Goal:** Pack product data into one file the app can search offline.

**Deliverable:** `data/build/nomi.sqlite` and `manifest.json` via `uv run pipeline build`, published to R2

**Tasks**
- [ ] Commit the table and index schema in `build/schema.sql`
- [ ] Write a manifest with version, input hashes, commit and counts
- [ ] Add a manual GitHub Action that uploads to R2
- [ ] Test lookups for all five reference products

**Done when:** File is in R2 under `datasets/v0.1.0/` and NDC11 lookups take under 10 ms on a mid-range Android.

---

## NOMI-039: Store encrypted profiles on device
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-028, NOMI-003

**Goal:** Save health profiles securely on the phone, never on the network.

**Deliverable:** `apps/mobile/src/storage/profiles.ts` wired to the onboarding and profile screens

**Tasks**
- [ ] Store profiles with `expo-secure-store`
- [ ] Support create, edit, delete and switch for 3+ profiles
- [ ] Add "Delete all my data" with confirmation
- [ ] Inspect network traffic and document it in the PR
- [ ] Add no analytics or crash-reporting SDK

**Done when:** No profile data leaves the device, and after "Delete all my data" the app reopens to onboarding.

---

## NOMI-040: Show real product data after an offline scan
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-007, NOMI-030, NOMI-038 (same sprint)

**Goal:** Ship the dataset in the app so scans show real products with no internet.

**Deliverable:** `apps/mobile/src/lib/db.ts` with `lookupBarcode`, wired into the scan flow

**Tasks**
- [ ] Bundle `nomi.sqlite` as an app asset via `db:fixture` and `db:copy`
- [ ] Route invalid, not-found and homeopathic barcodes to their states
- [ ] Write lookup unit tests

**Done when:** Scan to product takes under 300 ms in airplane mode on one iPhone and one Android.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-038 lands.

---

## NOMI-041: Build the "why this score" breakdown
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-029, NOMI-014

**Goal:** Show which risks lowered the score and the sources behind each one.

**Deliverable:** `apps/mobile/src/components/DimensionBreakdown.tsx` and `apps/mobile/src/app/result/dimension.tsx`

**Tasks**
- [ ] Show one bar per risk dimension on the result screen
- [ ] Open explanation and citations on tap, working offline
- [ ] Make it readable in grayscale and with screen readers
- [ ] Test with 5 people and log answers in the PR

**Done when:** 5 testers can explain why a reference product scored the way it did.

---

## NOMI-042: Publish coverage dashboard to GitHub Pages
**Team:** visualization | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-025, NOMI-026

**Goal:** Show the team and demo audience how well we cover real products.

**Deliverable:** Static site in `apps/dashboard/` live on GitHub Pages, fed by `uv run pipeline dashboard-data`

**Tasks**
- [ ] Write the four summary JSON files to `pipeline/reports/dashboard/`
- [ ] Chart barcode coverage, products by category, label section coverage
- [ ] Auto-deploy on merge to `main`
- [ ] Put the live URL in `apps/dashboard/README.md`

**Done when:** Site is live and every headline number matches the pipeline reports.

---

## NOMI-043: Run the whole pipeline with one command
**Team:** platform | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-008

**Goal:** Run every stage in order and record exactly what each run produced.

**Deliverable:** `uv run pipeline run` writing `data/runs/<run_id>/manifest.json`

**Tasks**
- [ ] Register stages and run them in order
- [ ] Skip stages whose inputs have not changed
- [ ] Add `--only`, `--force` and `--dry-run` options
- [ ] Document the command in `pipeline/README.md`

**Done when:** A repeat run skips every stage, and two forced runs give identical output hashes.

---

## NOMI-044: Build FAERS drug-reaction pairs table
**Team:** platform | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-024

**Goal:** Make one tidy table of drug and reaction pairs for signal detection.

**Deliverable:** `data/silver/faers_pairs.parquet` and `pipeline/knowledge/faers_event_groups.yaml`

**Tasks**
- [ ] Keep only primary and secondary suspect drugs
- [ ] Add age band and sex to every row
- [ ] Map reactions to at least nine event groups
- [ ] Record MedDRA license status in the PR

**Done when:** Counts reconcile with NOMI-024 dedup stats in `pipeline/reports/faers_pairs.md` and tests pass.

---

## NOMI-045: Merge label extractors and run on all labels
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-031, NOMI-032

**Goal:** Combine rule and LLM results into one trusted set of label facts.

**Deliverable:** `data/silver/label_facts.parquet` and `pipeline/reports/label_extraction.md`

**Tasks**
- [ ] Accept fields where both extractors agree
- [ ] List disagreements for human review
- [ ] Hand-check 100 labels, 10 by a second person
- [ ] Report per-field accuracy and LLM cost

**Done when:** Every in-scope label has facts and mandated-warning recall is at least 98% on the hand-checked set.

---

## NOMI-046: Map FAERS drug rows to ingredients
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-024, NOMI-033

**Goal:** Link every FAERS report to the OTC ingredients it names.

**Deliverable:** `data/silver/faers_drug_ingredient.parquet` and `pipeline/reports/faers_mapping.md`

**Tasks**
- [ ] Run the name matcher over every FAERS drug row
- [ ] Split combination products into one row per ingredient
- [ ] Review the 500 most common unmapped names
- [ ] Spot check 200 mappings and commit the sample

**Done when:** At least 90% of OTC drug rows are mapped and at least 97% of spot checks are correct.

---

## NOMI-047: Classify product uses into 25 categories
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-032, NOMI-026

**Goal:** Tag what each product treats so we can compare products for the same use.

**Deliverable:** `pipeline/knowledge/uses.yaml` and `data/silver/product_uses.parquet`

**Tasks**
- [ ] Define about 25 uses with keywords and examples
- [ ] Classify every in-scope product from its Uses section
- [ ] Hand-label 200 products, 20 double-labeled
- [ ] Report accuracy and LLM cost

**Done when:** Macro-F1 is at least 0.9 and every in-scope product has at least one use.

---

## NOMI-048: Write plain-language explanation templates
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-016, NOMI-022

**Goal:** Explain each risk in simple, cited sentences the app can fill in.

**Deliverable:** Templates in `pipeline/knowledge/templates/` and tests in `pipeline/tests/knowledge/test_templates.py`

**Tasks**
- [ ] Write templates per dimension (severity 1 to 3) and per modifier
- [ ] Add a CI check for citation slot and reading level
- [ ] Paste rendered output for the five reference products

**Done when:** Every template has a citation slot and reads at grade 8 or below in CI.

**Notes:** Use interview vocabulary from NOMI-022, or note a follow-up if it has not merged.

---

## NOMI-049: Write the rubric v0 scoring spec
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-034, NOMI-035

**Goal:** Define exactly how ingredient ratings become a 0-100 score, clear enough for a pharmacist to review.

**Deliverable:** `docs/rubric/v0.md` and `docs/rubric/v0_examples.py`

**Tasks**
- [ ] Write points, modifiers, hard stops and tiers with reasons
- [ ] Show the rules are monotonic (more risk never raises a score)
- [ ] Compute expected scores for five reference products and three profiles
- [ ] Get both cofounders' approval and send to the faculty partner

**Done when:** Worked examples show NSAIDs never top tier for 65+ with high blood pressure, and salicylates hard-stop for children.

---

# Sprint 4: Nov 6 to Nov 12 (feature freeze Nov 12)

## NOMI-050: Update demo script to v2 and freeze features
**Team:** cofounders | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-004

**Goal:** Make the demo script show only what will really ship on Nov 20, and protect Sprint 5 for fixes and rehearsals.

**Deliverable:** `docs/demo/script.md` v2 with "Demo boxes" and "Cut list" sections, plus a freeze announcement

**Tasks**
- [ ] Ask each Sprint 4 owner what will merge by Nov 12
- [ ] Rewrite the script so every moment matches a real ticket
- [ ] Pick, buy (2 each) and test-scan the demo boxes
- [ ] Write a one-line fallback for every at-risk moment
- [ ] Get all three team leads to confirm, merge, announce freeze Nov 12

**Done when:** Every script moment maps to a merged ticket or the cut list, and the freeze is announced on Nov 12.

**Notes:** Feature freeze (Nov 12): only fixes and polish merge after it. Code freeze is Nov 17.

---

## NOMI-051: Code the scoring rubric in Python
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-049, NOMI-002

**Goal:** Turn the written rubric into deterministic code and export the lookup tables the phone uses to score.

**Deliverable:** `pipeline/src/nomi_pipeline/score/`, `data/gold/term_tables.json` and 30 vectors in `packages/schema/golden/vectors.json`

**Tasks**
- [ ] Implement `score_ingredient` following `docs/rubric/v0.md`
- [ ] Export term tables and hard stops via `uv run pipeline score terms`
- [ ] Add NSAID, salicylate and monotonicity (Hypothesis) tests
- [ ] Test that summing exported rows equals direct scoring
- [ ] Write 30 golden vectors and get a cofounder to review them

**Done when:** Export validates against the `term-tables` schema, is byte-identical across runs, and all tests pass.

**Notes:** Term tables: rows of "this ingredient, dimension, persona costs N points". The phone just adds them up.

---

## NOMI-052: Score combination products and find duplicates
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-051 (same sprint)

**Goal:** Combine ingredient scores into one product score and warn when two products share an active ingredient.

**Deliverable:** `pipeline/src/nomi_pipeline/score/product.py` and `duplicates.py`, with tests

**Tasks**
- [ ] Agree the `score_ingredient` interface with the NOMI-051 owner
- [ ] Implement `score_product` with the rubric's stacking rule
- [ ] Implement `find_duplicates` by matching ingredient IDs across products
- [ ] Add golden vectors for NyQuil, Tylenol PM, Advil PM, Excedrin

**Done when:** NyQuil + Tylenol returns one acetaminophen warning, and the stacking and golden tests pass.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-051 lands.

---

## NOMI-053: Compute FAERS signals per risk dimension
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-044, NOMI-046

**Goal:** Find which problems get reported with each ingredient more often than expected, by age and sex, for the data story.

**Deliverable:** `data/gold/signal.parquet` via `uv run pipeline evidence signals`, plus `pipeline/docs/signals.md`

**Tasks**
- [ ] Write a fixture test with one planted signal first
- [ ] Compute IC and IC025 per ingredient, event group, age band, sex
- [ ] Map event groups to risk dimensions and validate against the schema
- [ ] Write the Method and Limitations sections with the formula cited

**Done when:** Known risks (acetaminophen-liver, NSAIDs-GI bleeding, NSAIDs-kidney, diphenhydramine-cognition 65+) show IC025 > 0.

**Notes:** IC025 above 0 counts as a signal. FAERS has no denominator, so it shows association, not risk rates.

---

## NOMI-054: Export category benchmarks per use and persona
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-047, NOMI-051 (same sprint)

**Goal:** Let the phone say "Better than 82% of pain relievers for you" by exporting score distributions per use.

**Deliverable:** `data/gold/benchmarks.parquet` via `uv run pipeline score benchmarks`

**Tasks**
- [ ] Score every in-scope product per persona, grouped by use
- [ ] Export 21 breakpoints (p0, p5 ... p100) per use and persona
- [ ] Skip groups with fewer than 5 products and log them
- [ ] Spot-check 10 benchmarks by hand in the PR

**Done when:** Every demo-aisle use has breakpoints for adult 18-64 and 65+, and no row mixes two uses.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-051 lands.

---

## NOMI-055: Precompute safer alternatives and tradeoffs
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-047, NOMI-052 (same sprint)

**Goal:** For every product, list same-use alternatives and how they differ, so the app can suggest a safer option.

**Deliverable:** `data/gold/alternatives.parquet` via `uv run pipeline score alternatives`

**Tasks**
- [ ] Find candidates that share a use, excluding hard stops and same-ingredient brands
- [ ] Keep top 10 per persona, preferring single-ingredient products
- [ ] Store per-dimension tradeoffs and an `ask_pharmacist` fallback
- [ ] Hand-check 30 demo-aisle products and fix any bad rules

**Done when:** Shared-use test passes, ZzzQuil never suggests Claritin, and all 30 checked products look sensible.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-052 lands.

---

## NOMI-056: Add scoring data to the SQLite dataset
**Team:** platform | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-038, NOMI-051 (same sprint)

**Goal:** Ship everything the phone needs to score and compare products inside `nomi.sqlite`, rebuilt nightly.

**Deliverable:** `data/build/nomi.sqlite` with new tables, and `.github/workflows/nightly-dataset.yml`

**Tasks**
- [ ] Add `term`, `hard_stop`, `dimension`, `benchmark`, `alternative`, `template` tables
- [ ] Agree table shapes with the NOMI-060 owner on day one
- [ ] Fail the build on schema errors or size over 20 MB
- [ ] Add a nightly workflow that builds and uploads to R2

**Done when:** All six tables exist, compressed size is at most 20 MB, and the nightly job ran green twice.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-051 lands.

---

## NOMI-057: Check Python and phone scores match in CI
**Team:** platform | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-051 (same sprint)

**Goal:** Make it impossible to merge a change where the phone's score differs from the reviewed Python score.

**Deliverable:** `.github/workflows/golden-parity.yml` plus `scripts/compare_golden.py`

**Tasks**
- [ ] Score every golden vector in Python and write `python-results.json`
- [ ] Score the same vectors in TypeScript and write `ts-results.json`
- [ ] Compare both to expected scores and print a mismatch table
- [ ] Run it on scoring PRs and make it a required check

**Done when:** A deliberate one-point mismatch makes the job fail, with the run linked in the PR.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-051 lands.

---

## NOMI-058: Build offline name search into the dataset
**Team:** platform | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-038

**Goal:** Let users find a product by name, offline, when the barcode won't scan.

**Deliverable:** `product_search` FTS5 table in `nomi.sqlite` and `pipeline/src/nomi_pipeline/build/search.py`

**Tasks**
- [ ] Write 20 test queries with expected products first
- [ ] Index brand, generic, ingredient and labeler names
- [ ] Rank results by relevance plus a popularity proxy
- [ ] Measure index size and query time on a phone

**Done when:** All 20 queries return the right product in the top 3, each in under 50 ms on a phone.

**Notes:** FTS5 is SQLite's built-in full-text search. Supports prefix search like `tylen*`.

---

## NOMI-059: Build the release command and publish v0.9
**Team:** platform | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-043, NOMI-056 (same sprint)

**Goal:** Make every dataset release show a person what changed before it reaches a phone.

**Deliverable:** `uv run pipeline release`, `data/build/release-0.9/diff_report.md`, and v0.9 on R2 under `releases/0.9/`

**Tasks**
- [ ] Put coverage thresholds and golden profiles in `pipeline/release.toml`
- [ ] Stop the release if any invariant or threshold fails
- [ ] Diff scores against the previous release for each golden profile
- [ ] Publish v0.9 and have Data Analysis comment on every tier change

**Done when:** Two releases with no changes in between produce an empty diff, and v0.9 is on R2.

**Notes:** If there is no previous release, compare against the latest nightly build.

---

## NOMI-060: Build the on-device scoring engine
**Team:** visualization | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-040, NOMI-051 (same sprint)

**Goal:** Compute each personalized score on the phone by adding exported points, so health data never leaves it.

**Deliverable:** `apps/mobile/src/scoring/engine.ts`, `benchmark.ts` and `sqliteSource.ts`, with tests

**Tasks**
- [ ] Write `scoreProduct` as a pure function: sum points, apply hard stops
- [ ] Write `percentileFor` to place a score among benchmark breakpoints
- [ ] Load data from `nomi.sqlite` with indexed, cached queries
- [ ] Wire it into the result screen

**Done when:** Every golden vector passes, and scoring one product takes under 20 ms on a mid-range phone.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-051 lands. Never log profiles.

---

## NOMI-061: Add benchmark and profile switcher to results
**Team:** visualization | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-041, NOMI-060 (same sprint)

**Goal:** Show the same box scoring differently for different people, live, with context and honest review status.

**Deliverable:** `BenchmarkStrip`, `ProfileSwitcher` and `ReviewStatusBadge` in `apps/mobile/src/components/`, on the result screen

**Tasks**
- [ ] Show "Better than X% of [use] for you" with a small visual
- [ ] Add profile chips that rescore instantly, no loading state
- [ ] Add a Verified / Preliminary badge with icon and text
- [ ] Record the Benadryl 30 vs 75 switch on a real phone

**Done when:** Switching profile updates score, breakdown and benchmark at once, and screen readers read both new elements.

**Notes:** If NOMI-060 isn't ready, use expected scores from `packages/schema/golden/vectors.json`.

---

## NOMI-062: Build the safer-alternative comparison screen
**Team:** visualization | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-055 (same sprint), NOMI-060 (same sprint)

**Goal:** Show why one product may be a better choice than another for this specific person.

**Deliverable:** `apps/mobile/src/app/compare/` and `apps/mobile/src/scoring/rankAlternatives.ts`

**Tasks**
- [ ] Rank candidates by the active profile's score, dropping hard stops
- [ ] Show both products side by side with shared use and a reason
- [ ] Show per-dimension tradeoffs with text labels, not just color
- [ ] Show "Ask your pharmacist" when no candidate scores higher
- [ ] Test Tylenol vs Aleve with a non-expert tester

**Done when:** The tester correctly explains the Tylenol vs Aleve tradeoff for a 70-year-old with high blood pressure.

**Notes:** Start with the reference products in packages/schema/examples/ until NOMI-055 lands.

---

## NOMI-063: Add barcode entry, name search and recents
**Team:** visualization | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-058 (same sprint), NOMI-030

**Goal:** Give users a way to find a product when the camera can't read the barcode.

**Deliverable:** `apps/mobile/src/app/search/` screen and a "Can't scan? Search instead" button on the scanner

**Tasks**
- [ ] Build name search on the FTS index, updating as you type
- [ ] Add typed barcode entry using the same parser and states as scans
- [ ] Store the last 20 scans encrypted on the device
- [ ] Clear recents with "Delete all my data"

**Done when:** A tester finds a product by name in under 10 seconds, and no search text leaves the phone.

**Notes:** Use a SQL `LIKE` query as a stand-in until NOMI-058 lands.

---

# Sprint 5: Nov 13 to Nov 19 (code freeze Nov 17, demo Nov 20)

## NOMI-064: Run the blind test and two rehearsals
**Team:** cofounders | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-050

**Goal:** Find out honestly whether a stranger's box will work on stage, and practice the demo until it runs smoothly.

**Deliverable:** `docs/demo/blind-test.md` and `docs/demo/rehearsals.md`, plus a backup demo video in the shared drive

**Tasks**
- [ ] Have outsiders bring 20 OTC boxes; no team member picks them
- [ ] Scan each in airplane mode on Nov 18 and log the result
- [ ] File a `blind-test` issue for every failure
- [ ] Run full rehearsals on Nov 18 and Nov 19
- [ ] Record a backup video and confirm a spare phone works

**Done when:** At least 18 of 20 boxes resolve and score correctly, and both rehearsals are logged.

**Notes:** Do not commit box photos, names or any health details.

---

## NOMI-065: Release and tag demo dataset v1.0
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-059

**Goal:** Freeze one reviewed dataset for the demo so no score changes in the final days.

**Deliverable:** Dataset v1.0 on R2, git tag `dataset-v1.0`, and the demo build with it at `apps/mobile/assets/nomi.sqlite`

**Tasks**
- [ ] Ask owners to merge data fixes by Nov 16
- [ ] Run `uv run pipeline release` for v1.0 on Nov 16
- [ ] Get both cofounders to approve the diff report
- [ ] Publish, tag, bundle into the demo build, hand to NOMI-068
- [ ] Post the data freeze rule in the team channel

**Done when:** The bundled file's hash matches the manifest, and the manifest's commit matches the tag.

---

## NOMI-066: Fix identity misses on 50 new boxes
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-037

**Goal:** Get an honest accuracy number on unseen boxes and fix the misses before code freeze.

**Deliverable:** `pipeline/tests/fixtures/barcodes_blind.csv`, resolver fixes, and `pipeline/reports/identity-blind-50.md`

**Tasks**
- [ ] Scan 50 boxes from local stores with the app, at least 15 store brands
- [ ] Run the resolver and mark each correct, wrong or not found
- [ ] Fix each miss at its cause and add a regression fixture
- [ ] Rerun the generated test barcodes to confirm nothing broke

**Done when:** At least 48 of 50 resolve correctly, with fixes merged by Nov 16.

---

## NOMI-067: Shrink the dataset and speed up lookups
**Team:** platform | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-056

**Goal:** Make sure the database is never the slow part of a scan, even on a low-end Android phone.

**Deliverable:** Builder changes in `pipeline/src/nomi_pipeline/build/` and `pipeline/reports/dataset-performance.md`

**Tasks**
- [ ] Add a dev-only screen that times each query type
- [ ] Record "before" numbers on the low-end Android phone
- [ ] Add indexes for any query that scans a whole table
- [ ] Drop unused columns and dedupe repeated strings to cut size

**Done when:** Every lookup is under 10 ms, compressed size is at most 20 MB, and golden vectors still pass.

**Notes:** Merge by Nov 16 so it reaches dataset v1.0.

---

## NOMI-068: Prepare four demo phones for offline use
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-065

**Goal:** Have 2 iPhones and 2 Android phones that run the full demo offline, with no surprises on stage.

**Deliverable:** 4 prepared phones, `docs/demo/devices.md` and `docs/demo/day-checklist.md`

**Tasks**
- [ ] Register the iPhones and install the release build with v1.0
- [ ] Set up the same made-up demo profiles on every phone
- [ ] Run the full script in airplane mode on each phone
- [ ] Test screen mirroring and write the demo-day checklist

**Done when:** All four phones pass every script step offline, and the checklist is used before the Nov 19 rehearsal.

**Notes:** If v1.0 isn't ready, practice with the v0.9 build and reinstall later.

---

## NOMI-069: Get scan-to-result under 300 ms
**Team:** visualization | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-060

**Goal:** Make the result appear instantly on every demo phone by fixing the real bottleneck.

**Deliverable:** Timing helper `apps/mobile/src/lib/perf.ts`, performance fixes, and `docs/demo/performance.md`

**Tasks**
- [ ] Add timing marks, on only when `EXPO_PUBLIC_PERF_LOG=1`
- [ ] Measure 20 scans per phone on release builds in airplane mode
- [ ] Fix the slowest step first and remeasure
- [ ] Confirm golden vectors still pass after caching changes

**Done when:** Every measured scan is under 300 ms on every demo phone, merged before Nov 17.

**Notes:** Scan to result: from barcode detected to score on screen. Never log profile data.

---

## NOMI-070: Make demo screens accessible
**Team:** visualization | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-061

**Goal:** Make sure older adults using large text or screen readers can read every score and warning.

**Deliverable:** Fixes in `apps/mobile/src/` and `apps/mobile/docs/accessibility-audit.md`

**Tasks**
- [ ] Walk the demo flow with VoiceOver and TalkBack; fix labels
- [ ] Fix clipped text at the largest text size on both platforms
- [ ] Make sure nothing relies on color alone
- [ ] Check WCAG AA contrast in light and dark mode

**Done when:** Every audit row passes, merged before code freeze on Nov 17.

**Notes:** WCAG AA: at least 4.5:1 contrast for normal text, 3:1 for large text and icons.

---

## NOMI-071: Build the FAERS signal explorer page
**Team:** visualization | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-042, NOMI-053

**Goal:** Show the real-world evidence behind our scores, with its limits stated plainly, for the demo data story.

**Deliverable:** A signals page in `apps/dashboard`, live on GitHub Pages

**Tasks**
- [ ] Export `data/gold/signal.parquet` to JSON in the dashboard build
- [ ] Add filters, a chart with intervals, and a sortable table
- [ ] Add walkthroughs: diphenhydramine 65+, and NSAIDs and kidney
- [ ] Add a limitations section and a script that checks the numbers

**Done when:** The page is live, the check script passes, and it was used in a rehearsal.

**Notes:** If NOMI-053 isn't ready, use a sample file with a "sample data" banner.

---

## NOMI-072: Fix demo UI bugs before code freeze
**Team:** visualization | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-061, NOMI-062

**Goal:** Own the list of UI problems from dry runs so the demo looks finished.

**Deliverable:** A triaged `ui-bug` issue list, P0 fixes, and a copy review approved by a cofounder

**Tasks**
- [ ] Create the `ui-bug` label and ask each team for a dry run
- [ ] Triage daily: P0 or P1, owner, close duplicates
- [ ] Fix every P0, one small PR each
- [ ] Review all demo copy: plain, no medical advice, consistent

**Done when:** Zero open P0 UI bugs on Nov 17, and leftover P1s moved to a post-demo milestone.

**Notes:** P0: anything that breaks or misleads during the demo script. No new features.

---

## NOMI-073: Review scores for the top 100 products
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-052

**Goal:** Catch scores that look wrong to a person and fix their causes before the demo.

**Deliverable:** `pipeline/reports/score-review-top100.csv` and `score-review-top100.md`, plus fix PRs

**Tasks**
- [ ] Pick the 100 most common products and export scores for 3 profiles
- [ ] Compare each score with its label and similar products
- [ ] Fix each flag in the knowledge base or rubric, never one score
- [ ] Hand every issue to the NOMI-074 owner

**Done when:** All 300 rows have a verdict, and every flag is fixed or documented before Nov 17.

**Notes:** Profiles: adult 18-64, 65+ with high blood pressure, child 6-11.

---

## NOMI-074: Expand golden vectors to 100
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-051

**Goal:** Test every aisle and persona, and turn every review issue into a permanent test.

**Deliverable:** 100 vectors in `packages/schema/golden/` and new invariants in `pipeline/tests/score/`

**Tasks**
- [ ] Plan 70 new vectors to fill aisle and persona gaps
- [ ] Compute each expected score by hand, with a points `note`
- [ ] Have a second person check 20 new vectors
- [ ] Add one invariant test per NOMI-073 issue

**Done when:** All 100 vectors pass in Python and TypeScript, and all invariants pass.

**Notes:** Targets: at least 15 per demo aisle and every persona at least 8 times.

---

## NOMI-075: Add about 120 preliminary ingredients
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-034, NOMI-035

**Goal:** Show a labeled preliminary score instead of "not found" for products from aisles we haven't curated.

**Deliverable:** About 120 new files in `pipeline/knowledge/ingredients/` and `pipeline/reports/kb-coverage.md`

**Tasks**
- [ ] Rank missing ingredients by frequency up to about 150 total
- [ ] Draft ratings from mandated warnings, label facts and criteria
- [ ] Mark every new file preliminary, with a citation per value
- [ ] Spot-check 20 values and report coverage before and after

**Done when:** About 150 ingredients pass schema validation, with coverage gain by aisle reported, merged by Nov 16.

**Notes:** Missing evidence is not zero risk. Never write 0 without a source.

---

## NOMI-076: Write the FAERS signal validation note
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-053

**Goal:** Show honestly where our FAERS signals work and where they don't.

**Deliverable:** `pipeline/docs/signals.md`, including the DuckDB queries used

**Tasks**
- [ ] Check known risks: acetaminophen-liver, NSAIDs-GI and kidney, antihistamines-memory 65+
- [ ] Document at least 5 likely false positives
- [ ] Write limitations: no denominator, under-reporting, masking, notoriety bias
- [ ] Plan a post-demo validation with owner and target month

**Done when:** Merged after cofounder review, with numbers for all three known-risk checks.

**Notes:** A signal shows a reporting pattern, not that the drug causes the reaction.

---

## NOMI-077: Write the methodology one-pager
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-049

**Goal:** Explain in plain words how Nomi's scores are made, what is validated and what isn't.

**Deliverable:** `docs/methodology.md` (600-900 words), linked from `docs/demo/script.md` and `README.md`

**Tasks**
- [ ] Cover data sources, risk dimensions and how a score is built
- [ ] State what is validated and what isn't, with linked numbers
- [ ] Add limitations, roadmap and a "not medical advice" line
- [ ] Read it aloud and simplify anything a non-expert stumbles on

**Done when:** Merged after both cofounders review, with no `[TBD]` placeholders left.
