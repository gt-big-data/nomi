# Nomi backlog: sprints to the Nov 20 demo

Every ticket is one deliverable, owned by one person, finishable in one 1-week sprint.
Cofounder tickets are smaller and run alongside each other.

Each ticket starts with `## NOMI-XXX: Title` followed by a metadata line. `create_issues.py`
parses this file, so keep the format when editing. Post-demo epics live in `post-demo.md`.

Dependencies marked `(same sprint)` mean: start against the reference products from NOMI-015 or a
fixture, then integrate when the upstream ticket merges.

---

# Sprint 1: Oct 16 to Oct 22

## NOMI-001: Scaffold the monorepo, CI and contributing guide
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
Fifteen people start writing code on Monday, Oct 19. If each team sets up its own tooling we end up
with conflicting conventions and a week of merge conflicts. The folder layout is already committed;
this ticket makes it buildable, linted and protected.

**Deliverable**
A repo where `pnpm install && uv sync` works on a fresh clone and every PR runs CI.

**Tasks**
- [ ] pnpm workspace for `apps/*` and `packages/*`; uv project in `pipeline/` (Python 3.12)
- [ ] ruff + mypy for Python; eslint + prettier + tsc for TypeScript; pre-commit hooks
- [ ] GitHub Actions: lint, typecheck and tests, path-filtered per package
- [ ] Protect `main`: PR required, 1 approval, CI green; CODEOWNERS per folder
- [ ] `CONTRIBUTING.md`: branch naming `<name>/<issue>-slug`, squash merges, definition of done, onboarding checklist; PR and issue templates

**Acceptance criteria**
- Fresh clone installs on macOS and Linux
- A PR with a lint error is blocked from merging

## NOMI-002: Shared data contracts v0
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

**Context**
Platform produces product data, Data Analysis turns it into scores, and Visualization renders scores
on the phone. Agreeing on these formats now lets all three teams work in parallel instead of waiting
on each other. Every downstream ticket codes against these schemas.

**Deliverable**
JSON Schemas in `packages/schema/` with generated TypeScript types and Pydantic models.

**Tasks**
- [ ] `product`: NDC11, SPL set id and version, brand and generic names, marketing category, OTC category, uses, ingredients (UNII, strength, unit)
- [ ] `ingredient-dimensions`: severity 0-3 per ingredient, risk dimension and persona; condition modifiers; citation on every value
- [ ] `term-tables`: additive points per feature value, hard-stop rules, model version (what the phone evaluates)
- [ ] `score-record`: score per profile, contribution per dimension, benchmark percentile, alternatives, explanation, provenance
- [ ] `signal`: ingredient, dimension, age band, sex, IC, IC025, report count
- [ ] Codegen to `packages/schema/generated/`; CI fails if generated files are stale

**Acceptance criteria**
- Both cofounders approve the schemas
- Generated types compile in the app and the pipeline

## NOMI-003: ADR-0001 architecture and ADR-0002 privacy
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
We decided to compute scores in our pipeline and run the final personalized scoring on the phone, so
no health data ever reaches our servers. Writing this down now stops the team from relitigating it
mid-semester and gives the law clinic something concrete to review.

**Deliverable**
`docs/adr/0001-architecture.md` and `docs/adr/0002-privacy.md`, merged.

**Tasks**
- [ ] ADR-0001: pipeline trains and exports term tables into a versioned SQLite file; the phone sums them for the user's profile; about 15 risk dimensions; rubric v0 now, evidence-synthesis model later; LLMs only in the offline pipeline
- [ ] ADR-0001 rejected options and why: live inference server, classifier trained on FAERS, BioBERT, Redis
- [ ] ADR-0002: profile, conditions, cabinet and scan history stay on the device, encrypted; every user downloads the same dataset; no health data to analytics or crash-reporting SDKs; sync only with end-to-end encryption; no training on user data without opt-in
- [ ] Privacy checklist added to the PR template

**Acceptance criteria**
- Both ADRs merged and linked from the root README

## NOMI-004: Demo script v1
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
The Nov 20 demo is the goal of this whole backlog. Writing the script first means every ticket can be
traced to something the audience will see, and anything that doesn't appear in the script can wait.

**Deliverable**
`docs/demo/script.md`, presented at the Oct 19 kickoff.

**Tasks**
- [ ] Blind scan of a box handed over by someone in the audience, with the phone in airplane mode
- [ ] Profile switch: Benadryl for a 30-year-old vs a 75-year-old
- [ ] Tylenol vs Aleve for a 70-year-old with high blood pressure, showing the tradeoff
- [ ] NyQuil duplicate-acetaminophen warning; homeopathic and not-found states
- [ ] Data story: coverage dashboard and FAERS signal explorer
- [ ] Key dates: feature freeze Nov 12, code freeze Nov 17, blind test Nov 18, rehearsals Nov 18-19

**Acceptance criteria**
- Script shared with every team at kickoff

## NOMI-005: Pharmacy faculty outreach
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
Our scores need clinical validation to be trustworthy, and we can't pay pharmacists. GT has no
pharmacy school, so we offer nearby faculty a research partnership: dataset access, co-authorship and
research projects for their students. This is the critical path for everything clinical.

**Deliverable**
At least one meeting booked with a pharmacy faculty member.

**Tasks**
- [ ] One-page pitch: "Validating a personalized consumer OTC medication-safety score"
- [ ] Identify 10+ faculty in drug information, geriatrics, pediatrics and ambulatory care at Mercer, UGA and PCOM Georgia
- [ ] Personal emails from the cofounders; contact APhA-ASP chapters about Generation Rx
- [ ] Track every contact in a shared sheet

**Acceptance criteria**
- At least 10 emails sent and 1 meeting booked

## NOMI-006: Data source license audit
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
The repo is public and Nomi is meant to become a commercial product. Before any pipeline code depends
on a dataset, we confirm we're allowed to use it commercially. DrugBank is already ruled out because
its academic license forbids commercial use.

**Deliverable**
`docs/data-sources.md` with one row per source.

**Tasks**
- [ ] openFDA NDC directory, FAERS, DailyMed: confirm public domain
- [ ] RxNorm: free UMLS license, use only `SAB=RXNORM` content
- [ ] ACB scale and STOPP/START: attribution and reuse terms
- [ ] AGS Beers Criteria: copyrighted, so request permission or don't use
- [ ] Record the rule that raw data is never committed to git

**Acceptance criteria**
- Each source has URL, license, commercial use allowed, required attribution and refresh cadence

## NOMI-020: Barcode ground-truth collection drive
**Team:** all | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none | **Extra:** good first issue

**Context**
We need real barcodes from real shelves to test identity resolution (NOMI-025) and to rehearse the
demo. Store brands matter most because they are where barcode lookups usually fail. One person owns
the drive; every member spends about two hours scanning.

**Deliverable**
`pipeline/tests/fixtures/barcodes.csv` with at least 300 unique OTC barcodes.

**Tasks**
- [ ] Form: barcode (typed or from any barcode app), product name, store, photo of the Drug Facts panel
- [ ] Assign each member a store (CVS, Walgreens, Target, Kroger, Publix) and aisles: pain/fever, allergy, sleep, cough/cold, digestive, topical, eye/nasal, first aid
- [ ] Everyone scans 25 boxes by Oct 25
- [ ] Clean and commit the CSV; keep photos in the shared drive, not the repo

**Acceptance criteria**
- At least 300 unique barcodes, at least 30% store brands, every aisle represented

## NOMI-007: Barcode to NDC candidate parser
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint) | **Extra:** good first issue

**Context**
Drug barcodes (UPC-A) usually contain the product's 10-digit NDC: a leading `3`, the NDC, then a
check digit. A 10-digit NDC can be split three ways (4-4-2, 5-3-2, 5-4-1), so we generate all three
11-digit versions and let the lookup decide. The same logic runs in the pipeline and on the phone.

**Deliverable**
`pipeline/src/nomi_pipeline/identity/barcode.py` and `apps/mobile/src/lib/barcode.ts` with shared tests.

**Tasks**
- [ ] Validate UPC-A and EAN-13 check digits; normalize EAN-13 codes that start with `0`
- [ ] Number system `3` returns three NDC11 candidates
- [ ] Any other number system returns `no_ndc`
- [ ] Shared test vectors in `packages/schema/fixtures/barcodes.json`

**Acceptance criteria**
- At least 30 test vectors, including invalid check digits, pass in Python and TypeScript

## NOMI-008: Raw data mirror and `pipeline fetch`
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint), NOMI-006 (same sprint)

**Context**
FAERS and the DailyMed label archive are several GB each. Fifteen people downloading them from FDA
servers is slow and gets rate limited. We mirror each source once into Cloudflare R2 (free tier) and
everyone pulls from there.

**Deliverable**
`uv run pipeline fetch <source>` downloading verified raw files into `data/raw/`.

**Tasks**
- [ ] Create the R2 bucket; read-only credentials for the team, write credentials for CI only
- [ ] Mirror: openFDA NDC bulk JSON, DailyMed Human OTC SPL zips, FAERS quarterly files from 2014
- [ ] Checksums and a manifest per source; `data/` stays gitignored

**Acceptance criteria**
- A new member gets all raw data with one command and checksums verify

## NOMI-009: Ingest openFDA NDC directory
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-008 (same sprint)

**Context**
The NDC directory is FDA's list of every marketed drug product and package. It's the first lookup in
the barcode chain and gives us each product's marketing category and label id.

**Deliverable**
`data/bronze/ndc.parquet` produced by `uv run pipeline ingest ndc`.

**Tasks**
- [ ] Keep only `product_type == "HUMAN OTC DRUG"`
- [ ] Normalize package NDCs to 11 digits
- [ ] Keep labeler, brand and generic names, dosage form, route, marketing category, active ingredients, `openfda.rxcui`, `spl_set_id`
- [ ] DuckDB view for exploration

**Acceptance criteria**
- Reproducible output; row counts and null rates logged

## NOMI-010: DailyMed label parser: products and ingredients
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-008 (same sprint)

**Context**
DailyMed has the full FDA label (SPL XML) for every OTC product, including exact ingredient strengths
and inactive ingredients. This ticket extracts the structured product data; the Drug Facts text
sections come in NOMI-023.

**Deliverable**
`data/bronze/spl_products.parquet` and `data/bronze/spl_ingredients.parquet`.

**Tasks**
- [ ] Parse set id, version, marketing category, products and package NDCs
- [ ] Active ingredients with UNII, strength and unit; inactive ingredients with UNII
- [ ] Keep only the latest version of each label; log parse failures with the set id

**Acceptance criteria**
- At least 98% of OTC labels parse without error

## NOMI-011: Expo app scaffold with live barcode scanning
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

**Context**
The product promise is "scan in the aisle, answer instantly." The app opens straight to the camera
with no home screen. Barcode reading happens on the device, so it works with no signal.

**Deliverable**
`apps/mobile` as an Expo dev build installed on real phones.

**Tasks**
- [ ] Expo with TypeScript and expo-router; EAS dev build (vision-camera doesn't run in Expo Go)
- [ ] `react-native-vision-camera` code scanner for UPC-A and EAN-13
- [ ] Haptic feedback on a successful scan; show the raw barcode on a placeholder screen
- [ ] Install on at least one iPhone and one Android phone

**Acceptance criteria**
- A real OTC box scans within about 300 ms of framing on both phones

## NOMI-012: Design tokens and component library in Figma
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
Scores are shown in colors, and about 1 in 12 men is color-blind. The score must never rely on color
alone. This library is the source for the coded components in NOMI-027.

**Deliverable**
A published Figma library.

**Tasks**
- [ ] Color tokens for light and dark mode, including score tiers that remain distinguishable for color-blind users
- [ ] Type scale and spacing
- [ ] Components: score badge, tier label, dimension bar, citation chip, profile chip, warning banner, buttons, cards
- [ ] WCAG AA contrast check on every score state

**Acceptance criteria**
- Library reviewed by the visualization team

## NOMI-013: Wireframes for the demo flows
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-004 (same sprint)

**Context**
Every screen the demo needs should exist as a clickable prototype before anyone builds it. That way
Data Analysis knows exactly which fields the screens consume.

**Deliverable**
A clickable Figma prototype covering the demo script.

**Tasks**
- [ ] Scanner; result screen with score, who it's for, dimension breakdown, benchmark, explanation and disclaimer
- [ ] Alternative and tradeoff comparison
- [ ] Onboarding and profiles: who you're scanning for, age band, conditions, current medication types
- [ ] States: preliminary score, homeopathic, not found, hard stop

**Acceptance criteria**
- Walked through with 3 people outside the team; feedback logged in the issue

## NOMI-014: Score visualization concepts and user test
**Team:** visualization | **Priority:** P1 | **Sprint:** S1 | **Depends on:** none

**Context**
Users need to see at a glance both how risky a product is for them and why. The way we draw the score
and its risk dimensions is the core of the product's design, so we test options before committing.

**Deliverable**
A written decision on the score and breakdown visuals, added to the Figma library.

**Tasks**
- [ ] Three concepts for the score (dial, bar, number with tier word) and for the dimension breakdown
- [ ] Test with 5 people: can they say why a product scored low and who the score is for?
- [ ] Write up the chosen concept and the reasons

**Acceptance criteria**
- Chosen concept merged into the NOMI-012 library

## NOMI-015: Hand-verified reference products
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-002 (same sprint)

**Context**
Every team needs realistic data before the pipeline exists. Five products researched by hand from
their labels become fixtures for the app screens, test cases for the pipeline and the expected
answers for the scoring engine.

**Deliverable**
Five records in `packages/schema/examples/`, validated in CI.

**Tasks**
- [ ] Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil and a store-brand diphenhydramine
- [ ] From DailyMed: NDCs, ingredients and strengths, uses, mandated warnings, maximum daily dose
- [ ] Draft dimension severities and expected scores for 3 profiles: adult, 65+ with high blood pressure, child 6-11

**Acceptance criteria**
- Records validate against NOMI-002; a second person has checked every value against the label

## NOMI-016: Risk-dimension and persona definitions
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
Nomi scores every OTC product, from Tylenol to Aleve to sleep aids, with one framework: each ingredient
gets a severity on the same set of risk dimensions for each kind of person. This document is the
shared vocabulary for the knowledge base, the rubric and the result screen.

**Deliverable**
`docs/scoring/dimensions.md`.

**Tasks**
- [ ] Define about 15 dimensions: liver, GI bleeding, cardiovascular/blood pressure, kidney, anticholinergic/cognitive, sedation/falls, serotonergic and interactions, bleeding with anticoagulants, pediatric-specific, rebound/overuse, pregnancy/lactation, duplicate dosing, excipients, local/skin, efficacy evidence
- [ ] Severity scale 0-3 with criteria for each level
- [ ] Personas: adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding
- [ ] Condition and medication modifiers: hypertension, kidney disease, liver disease, glaucoma, enlarged prostate, anticoagulants, MAOIs/SSRIs and others
- [ ] Which evidence sources may set each dimension

**Acceptance criteria**
- Reviewed by both cofounders and the data analysis team

## NOMI-017: Mandated-warning catalogue and rule spec
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

**Context**
FDA requires standard warning text on OTC labels: every acetaminophen product has a "Liver warning",
every NSAID a "Stomach bleeding warning". Because the wording is standardized, rules can extract it
reliably from every label, and each warning maps directly to a risk dimension.

**Deliverable**
`pipeline/knowledge/mandated_warnings.yaml` plus 50 label snippets as test fixtures.

**Tasks**
- [ ] List the required warnings: Liver, Stomach bleeding, Heart attack and stroke, Reye's syndrome, Allergy alert, Sore throat, alcohol, sodium and magnesium content, phenylketonurics, and any others in the monographs
- [ ] For each: wording variants seen on real labels, triggering ingredients, mapped dimension
- [ ] 50 real snippets in `pipeline/tests/fixtures/warnings/`

**Acceptance criteria**
- Catalogue and fixtures merged; every entry cites its regulation or monograph

## NOMI-018: Digitize STOPP/START and ACB criteria
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-006 (same sprint)

**Context**
STOPP/START (which medicines older adults should avoid) and the ACB scale (anticholinergic burden)
are published expert judgments we can cite. Turned into data, they set severities in the knowledge
base, especially for the 65+ persona.

**Deliverable**
`pipeline/knowledge/criteria/stopp_start.yaml` and `pipeline/knowledge/criteria/acb.yaml`.

**Tasks**
- [ ] STOPP/START criteria relevant to OTC ingredients and classes: ingredient or class, condition, recommendation, citation
- [ ] ACB scores for OTC ingredients with citation
- [ ] Schema validation in CI

**Acceptance criteria**
- Every row cited; a second person spot-checks 20 rows

## NOMI-019: UMLS access and RxNorm to UNII crosswalk
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S1 | **Depends on:** NOMI-006 (same sprint)

**Context**
Labels identify ingredients by UNII, while FAERS reports use free-text drug names. RxNorm connects the
two. This crosswalk is what lets us attach FAERS adverse events to the ingredients we score.

**Deliverable**
`data/silver/ingredient_crosswalk.parquet`.

**Tasks**
- [ ] Apply for a free UMLS license; download the monthly RxNorm RRF files and mirror them to R2
- [ ] Ingredient RxCUI to UNII crosswalk with synonyms for every OTC ingredient

**Acceptance criteria**
- At least 98% of OTC ingredients from NOMI-009 linked; unlinked list exported

---

# Sprint 2: Oct 23 to Oct 29

## NOMI-021: Legal, IP and regulatory intake
**Team:** cofounders | **Priority:** P0 | **Sprint:** S2 | **Depends on:** none

**Context**
A consumer score that recommends alternatives may raise FDA device questions, GT may have claims on
student-built IP, and scoring named brands carries defamation risk. Free legal help exists through
law-school clinics and CREATE-X; we need answers before external users touch the app.

**Deliverable**
A private decision memo and a short summary for the team.

**Tasks**
- [ ] Read GT's IP policy; apply to CREATE-X; check GT Big Data Big Impact spin-out rules
- [ ] Book a free consult with an Atlanta law-school clinic (Emory or Georgia State)
- [ ] Questions: FDA device-software status, pediatric dosing, LLC timing, E&O insurance, defamation exposure, review of ADR-0002
- [ ] Decide who owns the Apple and Google developer accounts

**Acceptance criteria**
- Memo stored privately (not in this public repo); summary shared at the Friday demo

## NOMI-022: User interviews round 1
**Team:** cofounders | **Priority:** P1 | **Sprint:** S2 | **Depends on:** none

**Context**
Explanation wording (NOMI-048) and onboarding (NOMI-028) should use the words real users use. We also
need to know how comfortable people are entering health conditions into an app.

**Deliverable**
`docs/research/interviews-round-1.md` (anonymized synthesis only).

**Tasks**
- [ ] Script: last OTC purchase, how they chose, who they buy for, what they'd trust, comfort sharing health conditions
- [ ] 10 interviews: 5 caregivers of adults 65+, 3 parents of young children, 2 people taking 3+ daily medications
- [ ] Synthesis: pains, trust signals, privacy concerns, vocabulary

**Acceptance criteria**
- Presented at the Friday demo; raw notes kept outside the repo

## NOMI-023: Drug Facts section splitter
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-010

**Context**
Label extraction (NOMI-031, NOMI-032) works on individual Drug Facts sections such as Warnings or
Directions, not whole labels. SPL marks each section with a standard LOINC code, so splitting is
reliable.

**Deliverable**
`data/bronze/spl_sections.parquet` and a coverage report.

**Tasks**
- [ ] Split by LOINC: Active ingredient 55106-9, Purpose 55105-1, Uses 34067-9, Warnings 34071-1, Do not use 50570-1, Ask a doctor 50569-3, Ask a doctor or pharmacist 50568-5, When using 50567-7, Stop use 50566-9, Pregnancy/breastfeeding 53414-9, Directions 34068-7, Inactive ingredients 51727-6
- [ ] Clean text (whitespace, bullets) and keep the original alongside it
- [ ] Report the share of labels that have each section

**Acceptance criteria**
- Sections table written; coverage report committed to `pipeline/reports/`

## NOMI-024: FAERS ingestion and deduplication
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-008

**Context**
FAERS holds FDA's adverse event reports and is our real-world evidence layer. Roughly 30% of raw
reports are duplicates, and the file formats change across quarters, so clean ingestion comes first.

**Deliverable**
Typed, deduplicated FAERS tables in `data/bronze/faers/`.

**Tasks**
- [ ] Load DEMO, DRUG, REAC, OUTC, INDI, THER, RPSR per quarter from 2014; handle format changes
- [ ] Deduplicate the FDA-recommended way: latest `caseversion` per `caseid`
- [ ] Keep drug role codes (PS, SS, C, I), age, sex, indications and other drugs taken

**Acceptance criteria**
- Reproducible per-quarter ingest; dedup stats reported per quarter

## NOMI-025: Identity resolver: barcode to product
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-007, NOMI-009, NOMI-010, NOMI-020

**Context**
This is the one piece the demo cannot work without: scanning a box has to return the right product
and ingredients. The Oct 29 checkpoint decides whether we move people onto identity work.

**Deliverable**
`data/silver/product.parquet` matching the `product` contract, plus a coverage report on real barcodes.

**Tasks**
- [ ] Chain NDC candidates to the NDC directory to the label to ingredients and strengths
- [ ] Choose the right candidate when several match; flag conflicts
- [ ] Coverage report on the NOMI-020 barcodes with every miss categorized

**Acceptance criteria**
- Coverage reported by Oct 29 (target at least 90%)

## NOMI-026: OTC category taxonomy and scope flags
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-009, NOMI-010

**Context**
Benchmarks and alternatives only make sense within a category: a sleep aid is never compared to an
antacid. Some DailyMed "OTC" labels shouldn't be scored at all, such as homeopathics (never evaluated
by FDA) and drug-cosmetics like sunscreen that are out of scope for now.

**Deliverable**
Category and scope columns on the `product` table, with counts.

**Tasks**
- [ ] Assign an OTC category from marketing category, monograph and active ingredients (internal analgesics, antacids, cough-cold, laxatives and so on)
- [ ] `homeopathic` flag: shown as "Not evaluated by FDA for safety or effectiveness", not scored
- [ ] Out-of-scope flag: sunscreen, hand sanitizer, fluoride toothpaste, antiperspirant, dandruff shampoo
- [ ] Counts per category and flag

**Acceptance criteria**
- Every product has a category or a scope flag

## NOMI-027: App theme and core components
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-011, NOMI-012

**Context**
Screens in later sprints are assembled from these components. Building them once, with accessibility
included, keeps the app consistent and saves time in Sprints 3 and 4.

**Deliverable**
Components in `apps/mobile/src/components/` and a gallery screen in the dev build.

**Tasks**
- [ ] Theme tokens for light and dark; typography that scales with Dynamic Type
- [ ] ScoreBadge, TierLabel, DimensionBar, CitationChip, ProfileChip, WarningBanner, Button, Card
- [ ] Screen-reader label on every component

**Acceptance criteria**
- Components match Figma in the gallery screen

## NOMI-028: Onboarding and profile screens
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-013, NOMI-016

**Context**
Scores depend on who the medicine is for. Onboarding collects that in under a minute without requiring
an account. This ticket is UI only; encrypted on-device storage is NOMI-039.

**Deliverable**
Onboarding and profile screens in `apps/mobile/src/app/onboarding/`.

**Tasks**
- [ ] "Who are you scanning for?" (me, a child, an older adult); age band; optional sex, pregnancy or breastfeeding
- [ ] Optional conditions and current medication types from the NOMI-016 lists
- [ ] Skippable, defaulting to adult

**Acceptance criteria**
- 3 people complete onboarding in under 60 seconds

## NOMI-029: Result screen v1
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-015, NOMI-027 (same sprint)

**Context**
The result screen is what users see after every scan. Version 1 renders the hand-made reference
products so the layout is settled before real data arrives in Sprint 3.

**Deliverable**
`apps/mobile/src/app/result/` rendering all five reference records.

**Tasks**
- [ ] Score with tier word and who it's for
- [ ] Product name, ingredients, explanation, hard-stop banner, disclaimer

**Acceptance criteria**
- Matches Figma for all five reference products

## NOMI-030: Scan flow states and navigation
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-011

**Context**
Not every scan ends in a clean score. The app has to handle preliminary scores, homeopathic products,
unknown barcodes and misreads without confusing the user.

**Deliverable**
Navigation from camera to every result state, wired to fixture data.

**Tasks**
- [ ] Camera to haptic to result navigation
- [ ] States: scored, preliminary (ingredients and label warnings only), homeopathic, not found, invalid barcode

**Acceptance criteria**
- Every state reachable in the dev build

## NOMI-031: Rule-based label extractor
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-017, NOMI-023 (same sprint)

**Context**
Rules extract the fields with predictable wording: mandated warnings, age limits and maximum doses.
They also act as an independent second opinion on the LLM extractor in NOMI-032.

**Deliverable**
`pipeline/src/nomi_pipeline/extract/rules.py` with unit tests.

**Tasks**
- [ ] Mandated warnings using the NOMI-017 catalogue
- [ ] Age limits ("children under 12 years: do not use"); maximum daily dose and dosing interval from Directions
- [ ] Allergens and dyes from inactive ingredients

**Acceptance criteria**
- At least 98% mandated-warning recall on the NOMI-017 fixtures

## NOMI-032: LLM label extraction v1
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-002, NOMI-016

**Context**
Some fields, such as conditions to ask a doctor about or interacting drug classes, vary too much for
rules. An LLM extracts them offline into a fixed schema. Its output is never shown to users directly;
it's checked against rules and people first.

**Deliverable**
`pipeline/src/nomi_pipeline/extract/llm.py`, run on 200 labels.

**Tasks**
- [ ] Extraction schema in `packages/schema/`: uses, age limits, max dose, ask-a-doctor conditions, interacting drug classes, do-not-use conditions, pregnancy, allergens, mandated warnings
- [ ] Claude structured output through the Message Batches API; record prompt and model version in provenance
- [ ] Run on 200 labels across categories; measure cost per label

**Acceptance criteria**
- Projected cost for all in-scope labels under $50

## NOMI-033: FAERS drug-name matcher
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S2 | **Depends on:** NOMI-019

**Context**
FAERS drug names are free text full of brand names, salts, dosages and misspellings. Signals are only
as good as the mapping from those strings to ingredients.

**Deliverable**
`pipeline/src/nomi_pipeline/evidence/name_matcher.py` with a labeled evaluation set.

**Tasks**
- [ ] Hand-label 500 FAERS drug-name strings
- [ ] Exact match, then RxNorm synonyms, then rapidfuzz with a threshold tuned on the labeled set
- [ ] Combination names expand to all ingredients

**Acceptance criteria**
- Precision at least 97% on the held-out half of the labeled strings

## NOMI-034: Knowledge base: pain/fever and digestive
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-016, NOMI-018

**Context**
The knowledge base is Nomi's core asset: every ingredient scored on every risk dimension for every
persona, each value cited. These two aisles include the Tylenol vs Aleve demo moment.

**Deliverable**
YAML files in `pipeline/knowledge/ingredients/`.

**Tasks**
- [ ] Ingredients: acetaminophen, ibuprofen, naproxen, aspirin, bismuth subsalicylate, calcium carbonate, magnesium and aluminum antacids, famotidine, omeprazole, loperamide, senna, bisacodyl, polyethylene glycol, docusate, simethicone
- [ ] Severity per dimension and persona; condition modifiers; citation on every value

**Acceptance criteria**
- Every ingredient in these aisles' ground-truth barcodes covered; no uncited values

## NOMI-035: Knowledge base: allergy/sleep and cough/cold
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-016, NOMI-018

**Context**
These aisles hold the most under-communicated risks: first-generation antihistamines in older adults,
decongestants with high blood pressure, and acetaminophen hidden in combination cold products.

**Deliverable**
YAML files in `pipeline/knowledge/ingredients/`.

**Tasks**
- [ ] Ingredients: diphenhydramine, doxylamine, chlorpheniramine, brompheniramine, cetirizine, loratadine, fexofenadine, dextromethorphan, guaifenesin, pseudoephedrine, phenylephrine, oxymetazoline
- [ ] Severity per dimension and persona; condition modifiers; citation on every value

**Acceptance criteria**
- Every ingredient in these aisles' ground-truth barcodes covered; no uncited values

---

# Sprint 3: Oct 30 to Nov 5

## NOMI-036: Faculty partner rubric review session
**Team:** cofounders | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-005, NOMI-049 (same sprint)

**Context**
Clinical feedback is cheapest before the rubric is implemented in Sprint 4. If no faculty partner has
signed on yet, we run an internal review and schedule the clinical review for after the demo.

**Deliverable**
A list of requested rubric changes, each filed as a GitHub issue.

**Tasks**
- [ ] Send NOMI-016 and the NOMI-049 draft ahead of time
- [ ] One-hour review meeting
- [ ] Agree how the partner is credited in the app and in publications

**Acceptance criteria**
- Feedback filed as issues before Sprint 4 planning

## NOMI-037: Identity coverage to 95%
**Team:** platform | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-025

**Context**
The demo opens with a blind scan of a box someone else picked. Every miss in the NOMI-025 report
points to a fixable cause: store-brand labelers, non-standard barcodes, or stale labels.

**Deliverable**
Resolver fixes with a regression fixture for each one.

**Tasks**
- [ ] Fix each category of miss from the NOMI-025 report
- [ ] Handle barcodes that don't start with `3` by matching on labeler and name where possible
- [ ] Add every fixed case to the regression fixtures

**Acceptance criteria**
- At least 95% of ground-truth barcodes resolve to the correct product

## NOMI-038: SQLite dataset builder v1
**Team:** platform | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-002, NOMI-025

**Context**
The app works offline because the whole dataset ships to the phone as one SQLite file. Version 1
contains products, ingredients and label facts; scores are added in NOMI-056.

**Deliverable**
`uv run pipeline build` writing `nomi.sqlite` and a manifest, published to R2.

**Tasks**
- [ ] SQLite schema: products by NDC11, ingredients, label warnings, categories, scope flags
- [ ] Manifest with dataset version, input hashes and code commit
- [ ] Publish to R2 and record the compressed size

**Acceptance criteria**
- Any NDC11 looks up in under 10 ms on a mid-range Android phone

## NOMI-039: Encrypted profiles stored on the device
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-028, NOMI-003

**Context**
Health conditions and medications are sensitive. Keeping them on the phone means we never store
health data, which keeps us clear of the FTC Health Breach Notification Rule and Washington's My
Health My Data Act. See ADR-0002.

**Deliverable**
Encrypted local profile storage with multiple profiles.

**Tasks**
- [ ] Encrypted storage; create, edit and delete profiles; switch the active profile
- [ ] No network request carries profile data
- [ ] "Delete all my data" action

**Acceptance criteria**
- Network inspection during onboarding and scanning shows no profile data leaving the device

## NOMI-040: On-device database and lookup
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-007, NOMI-030, NOMI-038 (same sprint)

**Context**
This is where a scan first returns real data. Start with a fixture database built from the reference
products and switch to the NOMI-038 build when it lands.

**Deliverable**
Scanning a real box shows its real product data, offline.

**Tasks**
- [ ] Bundle the SQLite dataset in the app
- [ ] Look up the NDC candidates from `apps/mobile/src/lib/barcode.ts`
- [ ] Wire results into the scan flow states

**Acceptance criteria**
- Scan to product shown in under 300 ms with the phone in airplane mode

## NOMI-041: Risk-dimension breakdown and citations
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-029, NOMI-014

**Context**
Showing why a product scored the way it did is what separates Nomi from a bare number. Every point
taken off links to its source, which builds trust and is also our main defense if a brand disputes a
score.

**Deliverable**
The breakdown section of the result screen.

**Tasks**
- [ ] Contribution bars per dimension using the NOMI-014 concept
- [ ] Tapping a dimension opens its explanation and citations (label section, STOPP/START, ACB, FAERS)
- [ ] Readable without color

**Acceptance criteria**
- 5 testers can explain why a reference product scored the way it did

## NOMI-042: Coverage dashboard v1
**Team:** visualization | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-025, NOMI-026

**Context**
The team needs a shared view of pipeline health, and the demo needs a data story. This static site is
regenerated from pipeline outputs.

**Deliverable**
`apps/dashboard` published to GitHub Pages.

**Tasks**
- [ ] Barcode coverage by store, brand vs store brand and category
- [ ] Products by category and scope flag; label section coverage

**Acceptance criteria**
- Numbers match the pipeline logs; shown at the Friday demo

## NOMI-043: Pipeline CLI and run manifest
**Team:** platform | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-008

**Context**
Every score must trace back to the exact data and code that produced it. A single command that runs
every stage with a manifest makes that possible and lets anyone rebuild the dataset.

**Deliverable**
`uv run pipeline run`.

**Tasks**
- [ ] Chain fetch, ingest, resolve, extract, signals, score and build
- [ ] Run manifest with input versions, code commit and output hashes
- [ ] Skip stages whose inputs haven't changed

**Acceptance criteria**
- Two runs on the same inputs produce identical outputs

## NOMI-044: FAERS analysis tables
**Team:** platform | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-024

**Context**
Signal detection (NOMI-053) needs one tidy table of drug and reaction pairs per report, split by age
band and sex and grouped into the event types that map to our risk dimensions.

**Deliverable**
`data/silver/faers_pairs.parquet`.

**Tasks**
- [ ] One row per case, drug role and reaction, with age band (0-11, 12-17, 18-64, 65+) and sex
- [ ] Map MedDRA preferred terms to system organ classes and the event groups for each dimension
- [ ] Keep primary and secondary suspect drugs only

**Acceptance criteria**
- Row counts reconcile with the NOMI-024 dedup stats

## NOMI-045: Label extraction: merge, agreement and full run
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-031, NOMI-032

**Context**
Fields where rules and the LLM agree are accepted automatically; disagreements go to a person. This
turns two imperfect extractors into one we can trust and measure.

**Deliverable**
`data/silver/label_facts.parquet` for every in-scope label.

**Tasks**
- [ ] Merge rules and LLM output; auto-accept agreements; list disagreements for review
- [ ] Run on all in-scope labels
- [ ] Hand-check 100 labels; report precision, recall and agreement per field

**Acceptance criteria**
- Mandated-warning recall at least 98% on the 100 hand-checked labels

## NOMI-046: FAERS normalization to ingredients
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-024, NOMI-033

**Context**
Applies the NOMI-033 matcher to every FAERS drug row so adverse events attach to the same ingredients
the knowledge base scores.

**Deliverable**
Ingredient ids on every mappable FAERS drug row.

**Tasks**
- [ ] Run the matcher over all drug rows; expand combination products
- [ ] Manually review the 500 most frequent unmapped strings
- [ ] Spot-check 200 random mappings

**Acceptance criteria**
- At least 90% of OTC drug rows mapped; spot-check at least 97% correct

## NOMI-047: Uses classifier
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-032, NOMI-026

**Context**
Alternatives must match what a product is used for. ZzzQuil's alternative should be another sleep
option, not Claritin. The label's Uses section tells us that.

**Deliverable**
A `uses` field on every in-scope product.

**Tasks**
- [ ] Taxonomy of about 25 uses: pain, fever, nasal allergy, sleep, cough, congestion, heartburn, constipation, diarrhea, nausea/motion sickness, topical pain, eye redness and so on
- [ ] Classify Uses text with the LLM, checked against keyword rules
- [ ] Hand-label 200 products and report macro-F1

**Acceptance criteria**
- Macro-F1 at least 0.9 on the hand-labeled set; every in-scope product has at least one use

## NOMI-048: Explanation templates v0
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-016, NOMI-022

**Context**
Explanations are filled-in templates rather than generated text, so every sentence is predictable,
reviewable and cited. They ship in the dataset and are filled in on the phone.

**Deliverable**
Templates in `pipeline/knowledge/templates/`.

**Tasks**
- [ ] One template per dimension, severity and modifier, at an 8th-grade reading level or below
- [ ] Use vocabulary from the user interviews
- [ ] Citation slot on every sentence; readability check in CI

**Acceptance criteria**
- Templates render for all five reference products

## NOMI-049: Rubric v0 specification
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-034, NOMI-035

**Context**
Rubric v0 is the demo's scoring model: transparent, deterministic and cited. It's written so a
pharmacist can review it, and later the personalized evidence-synthesis model replaces its weights
without changing the app.

**Deliverable**
`docs/rubric/v0.md`.

**Tasks**
- [ ] Points per severity, dimension and persona; condition and medication modifiers
- [ ] How dimensions combine; use dose and duration where the label gives them
- [ ] Hard stops vs graded factors; efficacy dimension; homeopathic policy; tier bands and wording
- [ ] Monotonicity rule: more risk can never raise a score
- [ ] Expected scores for the five reference products

**Acceptance criteria**
- Approved by both cofounders and sent to the faculty partner

---

# Sprint 4: Nov 6 to Nov 12 (feature freeze Nov 12)

## NOMI-050: Demo script v2 and feature freeze
**Team:** cofounders | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-004

**Context**
By now we know what will really ship. Locking the script and announcing the freeze protects the last
week for fixing and rehearsing instead of new features.

**Deliverable**
`docs/demo/script.md` v2 and a freeze announcement.

**Tasks**
- [ ] Update the script to what will ship; choose the demo boxes
- [ ] Decide in advance what gets cut if a ticket slips
- [ ] Announce the feature freeze on Nov 12

**Acceptance criteria**
- Every team confirms its parts of the script

## NOMI-051: Rubric v0 implementation and term-table export
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-049, NOMI-002

**Context**
The rubric runs in Python and exports term tables: the points each feature value adds or removes. The
phone only adds these up, so the model lives in one place and the app needs no modeling logic.

**Deliverable**
`pipeline/src/nomi_pipeline/score/` with term-table export and tests.

**Tasks**
- [ ] Deterministic scoring for an ingredient and a profile
- [ ] Export term tables and hard-stop rules in the `term-tables` format
- [ ] Invariant tests: NSAIDs never green for 65+ with high blood pressure or kidney disease; salicylates a hard stop for children; monotonicity property tests with Hypothesis
- [ ] 30 golden vectors (product, profile, expected score) in `packages/schema/golden/`

**Acceptance criteria**
- All invariants pass; golden vectors reviewed by a cofounder

## NOMI-052: Product aggregation and duplicate detection
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-051 (same sprint)

**Context**
Many top sellers are combination products. NyQuil contains acetaminophen, dextromethorphan and
doxylamine, and taking it with Tylenol doubles the acetaminophen. Agree on the interface with the
NOMI-051 owner on day one.

**Deliverable**
Product-level scores and duplicate detection.

**Tasks**
- [ ] Combine ingredient contributions into product scores (NyQuil, Tylenol PM, Advil PM, Excedrin)
- [ ] Stacking within a product, such as two sedating or anticholinergic ingredients
- [ ] Duplicate-ingredient detection across products, reused by the Medicine Cabinet later

**Acceptance criteria**
- Golden tests for combination products pass

## NOMI-053: FAERS signals mapped to risk dimensions
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-044, NOMI-046

**Context**
FAERS has no denominator, so it can't give risk rates, but it can show which problems are reported
more often than expected. Bayesian shrinkage keeps rare ingredients from producing noisy signals.
This is the evidence layer of the demo's data story.

**Deliverable**
`data/gold/signal.parquet` matching the `signal` contract.

**Tasks**
- [ ] BCPNN information component (IC and IC025) per ingredient and event group
- [ ] Map event groups to dimensions; split by age band and sex
- [ ] Write up limitations: no denominator, masking, notoriety bias

**Acceptance criteria**
- Sanity checks pass: acetaminophen and liver; NSAIDs and GI bleeding and kidney; diphenhydramine and cognition in 65+

## NOMI-054: Category benchmarks
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-047, NOMI-051 (same sprint)

**Context**
"Better than 82% of pain relievers for you" gives a score meaning. Because scores are personalized on
the phone, we export percentile breakpoints rather than fixed percentiles.

**Deliverable**
Benchmark breakpoints per use and persona in the dataset.

**Tasks**
- [ ] Score distribution per use and persona across all in-scope products
- [ ] Export percentile breakpoints for the phone
- [ ] Never compare across different uses

**Acceptance criteria**
- Benchmarks for every use in the demo aisles; 10 spot-checked by hand

## NOMI-055: Safer alternatives with tradeoffs
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-047, NOMI-052 (same sprint)

**Context**
The pipeline precomputes candidate lists; the phone ranks them for the active profile. When no OTC
option is clearly better, the honest answer is "ask your pharmacist."

**Deliverable**
Alternative candidates and tradeoff summaries per product in the dataset.

**Tasks**
- [ ] Candidates share a use; prefer single-ingredient products
- [ ] Tradeoff summary: which dimensions differ between the two products
- [ ] "Ask your pharmacist" fallback

**Acceptance criteria**
- Alternatives for 30 hand-checked products judged sensible; ZzzQuil never suggests Claritin

## NOMI-056: Dataset builder v2: scores, benchmarks, alternatives
**Team:** platform | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-038, NOMI-051 (same sprint)

**Context**
Adds everything the phone needs to score and compare products to the dataset file from NOMI-038.
Rebuilding nightly during the sprint keeps the app team on fresh data.

**Deliverable**
`nomi.sqlite` with the full demo contents.

**Tasks**
- [ ] Add term tables, hard stops, dimension rows, benchmark breakpoints, alternative candidates and templates
- [ ] Stay within 20 MB compressed
- [ ] Nightly rebuild during the sprint

**Acceptance criteria**
- Dataset passes schema validation; size reported in the manifest

## NOMI-057: Golden-vector parity check in CI
**Team:** platform | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-051 (same sprint)

**Context**
The same score is computed in Python (pipeline) and TypeScript (phone). If they ever disagree, a user
sees a different number than the one we checked. This CI job makes that impossible to merge.

**Deliverable**
A CI job running the golden vectors against both implementations.

**Tasks**
- [ ] Load golden vectors from `packages/schema/golden/`
- [ ] Run them through Python scoring and the TypeScript evaluator
- [ ] Clear diff output on mismatch

**Acceptance criteria**
- CI fails on any mismatch

## NOMI-058: Name search index
**Team:** platform | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-038

**Context**
Some boxes won't scan: crumpled packaging, glare, or barcodes we can't resolve. Searching by name,
offline, is the fallback.

**Deliverable**
An SQLite FTS5 index in the dataset.

**Tasks**
- [ ] Index brand, generic and ingredient names
- [ ] Ranking that favors common products

**Acceptance criteria**
- Top-3 results correct for 20 test queries in under 50 ms on a phone

## NOMI-059: Release run and score diff report
**Team:** platform | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-043, NOMI-056 (same sprint)

**Context**
Before any dataset reaches a phone we check what changed. A product whose score moved sharply or
changed tier needs a person to look at it.

**Deliverable**
`uv run pipeline release` producing dataset v0.9 and a diff report.

**Tasks**
- [ ] Full run with invariant tests and coverage thresholds
- [ ] Diff on golden profiles: products added or removed, score moves, tier changes, new hard stops
- [ ] Post the report on the release PR

**Acceptance criteria**
- Dataset v0.9 published with its diff report

## NOMI-060: On-device scoring engine
**Team:** visualization | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-040, NOMI-051 (same sprint)

**Context**
Personalized scoring happens on the phone so the user's health profile never leaves it. The engine
only looks up and adds term-table points; all modeling stays in the pipeline.

**Deliverable**
`apps/mobile/src/scoring/`.

**Tasks**
- [ ] Look up term-table points for the product and the active profile, sum them, apply hard stops
- [ ] Compute the benchmark percentile from the exported breakpoints

**Acceptance criteria**
- Passes every golden vector in NOMI-057; under 20 ms per score on a phone

## NOMI-061: Benchmark and profile switcher on the result screen
**Team:** visualization | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-041, NOMI-060 (same sprint)

**Context**
This is the demo's personalization moment: the same Benadryl box gets a different score for a
30-year-old and a 75-year-old.

**Deliverable**
Benchmark and profile switching on the result screen.

**Tasks**
- [ ] "Better than X% of [use] for you" with a small distribution visual
- [ ] Profile switcher (me, my child, my parent) that rescores instantly
- [ ] Review-status badge: preliminary or verified

**Acceptance criteria**
- The Benadryl 30 vs 75 demo works end to end

## NOMI-062: Alternative and tradeoff comparison view
**Team:** visualization | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-055 (same sprint), NOMI-060 (same sprint)

**Context**
The comparison explains why Tylenol may be the better choice than Aleve for one person and not for
another. It shows tradeoffs across dimensions, not just two numbers.

**Deliverable**
The comparison screen.

**Tasks**
- [ ] Rank alternatives by the active profile's score
- [ ] Side by side: scores, dimension tradeoffs, shared use, one-line reason
- [ ] "Ask your pharmacist" state

**Acceptance criteria**
- Tylenol vs Aleve for a 70-year-old with high blood pressure is understood by a non-expert tester

## NOMI-063: Search and manual-entry fallback
**Team:** visualization | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-058 (same sprint), NOMI-030

**Context**
When the camera can't read a barcode, users need another way to find the product.

**Deliverable**
Manual barcode entry, name search and recent scans.

**Tasks**
- [ ] Type a barcode manually
- [ ] Search by name using the FTS index
- [ ] Recent scans, stored only on the device

**Acceptance criteria**
- A tester finds a product by name in under 10 seconds

---

# Sprint 5: Nov 13 to Nov 19 (code freeze Nov 17, demo Nov 20)

## NOMI-064: Blind test and rehearsals
**Team:** cofounders | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-050

**Context**
A blind test with boxes nobody picked in advance tells us whether the demo will survive a box from
the audience. Rehearsals catch everything else.

**Deliverable**
Recorded blind-test results and two full rehearsals.

**Tasks**
- [ ] Nov 18: scan 20 real boxes nobody pre-selected; record outcomes
- [ ] Two full rehearsals on Nov 18 and 19
- [ ] Fallbacks: a recorded video and spare phones with the build installed

**Acceptance criteria**
- At least 18 of 20 boxes resolved and scored correctly

## NOMI-065: Demo dataset v1.0 release
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-059

**Context**
The demo runs on one frozen, reviewed dataset so nothing changes underneath us in the final days.

**Deliverable**
Dataset v1.0 tagged and bundled into the demo build.

**Tasks**
- [ ] Final release run; both cofounders review the diff report
- [ ] Tag the dataset version and code commit
- [ ] No data changes after Nov 17 without cofounder approval

**Acceptance criteria**
- v1.0 tagged and bundled

## NOMI-066: Blind-test identity fixes
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-037

**Context**
The ground-truth set has been tuned against for weeks. New boxes show how we'll do on a box from the
audience.

**Deliverable**
Fixes and regression fixtures for every miss on 50 new boxes.

**Tasks**
- [ ] Scan 50 boxes that aren't in the ground-truth set
- [ ] Fix each miss and add it to the fixtures
- [ ] Report final coverage

**Acceptance criteria**
- At least 95% correct on the new boxes

## NOMI-067: Dataset size and lookup performance pass
**Team:** platform | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-056

**Context**
Low-end Android phones are where slowness shows. A smaller, better-indexed dataset also means faster
installs and updates.

**Deliverable**
Before and after numbers for size and query time.

**Tasks**
- [ ] Profile lookup and scoring queries on a low-end Android phone
- [ ] Add indexes, prune columns, tune compression

**Acceptance criteria**
- Every lookup under 10 ms; size within budget

## NOMI-068: Demo devices
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-065

**Context**
Demo day should not depend on anyone's personal phone settings or a venue's Wi-Fi.

**Deliverable**
Four phones ready for the demo.

**Tasks**
- [ ] Install the release build on 2 iPhones and 2 Android phones
- [ ] Verify the full script in airplane mode; set up demo profiles
- [ ] Demo-day checklist: charge, brightness, notifications off

**Acceptance criteria**
- The full script runs offline on all four phones

## NOMI-069: Scan-to-result performance pass
**Team:** visualization | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-060

**Context**
"Instant" is the core promise. We measure each step and fix the slowest.

**Deliverable**
Measured and improved timings on every demo phone.

**Tasks**
- [ ] Measure cold start, barcode detection and scan to result
- [ ] Fix the slowest steps: preload the database, warm caches, avoid re-renders

**Acceptance criteria**
- Scan to result under 300 ms on every demo phone in airplane mode

## NOMI-070: Accessibility pass
**Team:** visualization | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-061

**Context**
Our first audience includes older adults and their caregivers. Large text and screen readers have to
work.

**Deliverable**
Accessibility fixes across every demo screen.

**Tasks**
- [ ] VoiceOver and TalkBack labels on every screen
- [ ] Largest Dynamic Type sizes without clipping
- [ ] Nothing communicated by color alone; recheck contrast

**Acceptance criteria**
- The full demo flow completed with VoiceOver on

## NOMI-071: FAERS signal explorer
**Team:** visualization | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-042, NOMI-053

**Context**
The data-story part of the demo shows the real-world evidence behind the scores, with its limitations
stated plainly.

**Deliverable**
A signal explorer page in `apps/dashboard`.

**Tasks**
- [ ] View by ingredient, dimension and age band with IC and intervals
- [ ] Walkthroughs: diphenhydramine in adults 65+, NSAIDs and kidney
- [ ] Limitations stated on the page

**Acceptance criteria**
- Used in rehearsals; numbers match the `signal` table

## NOMI-072: Demo polish and blind-test UI fixes
**Team:** visualization | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-061, NOMI-062

**Context**
Dry runs surface small UI problems that add up. This ticket owns triaging and fixing them before code
freeze.

**Deliverable**
No open P0 UI bugs at code freeze.

**Tasks**
- [ ] Triage UI issues from team dry runs
- [ ] Fix P0 issues by Nov 17
- [ ] Final copy review of every demo screen

**Acceptance criteria**
- Zero open P0 UI bugs on Nov 17

## NOMI-073: Score sanity review of the top 100 products
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-052

**Context**
Invariant tests catch rule violations, not odd results. A human pass over the most common products
catches the scores that would embarrass us in front of an audience or a pharmacist.

**Deliverable**
A review log with every flagged score resolved or documented.

**Tasks**
- [ ] Review the 100 most common products for 3 profiles each
- [ ] Fix problems in the knowledge base or rubric, never by editing one product's score
- [ ] Faculty partner reviews a sample if available

**Acceptance criteria**
- Every flagged issue fixed or documented before code freeze

## NOMI-074: Golden vectors and invariants expansion
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-051

**Context**
Each issue found in review becomes a permanent test, so it can't come back after the demo.

**Deliverable**
100 golden vectors and new invariants.

**Tasks**
- [ ] Grow golden vectors from 30 to 100 across every demo aisle and persona
- [ ] Add an invariant for each issue found in NOMI-073

**Acceptance criteria**
- All pass in Python and TypeScript

## NOMI-075: Knowledge base expansion beyond the demo aisles
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-034, NOMI-035

**Context**
The demo might hit a box from another aisle. Ingredients derived automatically from mandated warnings
and criteria can be shown as preliminary scores instead of "not found".

**Deliverable**
About 150 ingredients covered, with the new ones marked preliminary.

**Tasks**
- [ ] Add the next most frequent ingredients: topical, eye/nasal, first aid and others
- [ ] Derive severities from mandated warnings and criteria; mark them preliminary until verified

**Acceptance criteria**
- Coverage gain on the ground-truth barcodes reported

## NOMI-076: FAERS signal validation note
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-053

**Context**
Faculty and technical audiences will ask what the signals prove. An honest write-up of what they do
and don't show protects our credibility.

**Deliverable**
`pipeline/docs/signals.md`.

**Tasks**
- [ ] Check signals for known risks: acetaminophen and liver, NSAIDs and GI bleeding and kidney, first-generation antihistamines and cognition in older adults
- [ ] Document false positives and limitations
- [ ] Plan the post-demo validation against a reference set

**Acceptance criteria**
- Merged and reviewed by a cofounder

## NOMI-077: Methodology one-pager
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-049

**Context**
The demo audience and faculty partners will want to know how scores are made in plain language,
including what is validated and what isn't yet.

**Deliverable**
`docs/methodology.md`.

**Tasks**
- [ ] Data sources, risk dimensions, how a score is built
- [ ] What's validated and what isn't; limitations
- [ ] Roadmap to the personalized evidence-synthesis model

**Acceptance criteria**
- Reviewed by both cofounders and linked from the demo
