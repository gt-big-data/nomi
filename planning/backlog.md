# Nomi backlog: sprints to the Nov 20 demo

Every ticket is one deliverable, owned by one person, finishable in one 1-week sprint. New to the project? Read `docs/nomi-101.md` first. To write a new ticket, follow `planning/ticket-template.md`.

Each ticket starts with `## NOMI-XXX: Title` followed by a metadata line. `create_issues.py` parses this file, so keep the format when editing. Post-demo epics live in `post-demo.md`.

Dependencies marked `(same sprint)` mean: start against the reference products in `packages/schema/examples/` (NOMI-015) or a fixture, then integrate when the upstream ticket merges.

---

# Sprint 1: Oct 16 to Oct 22

## NOMI-001: Set up repo tooling, CI, branch protection and the contributing guide
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Turn the already-committed folder layout into a repo that installs with one command, lints and type-checks itself, runs CI on every pull request, and blocks merges to `main` that fail CI or lack a review. Every one of the 15 team members uses this from their first day.

### Why this matters
Fifteen people start writing code on Monday, Oct 19. If each team sets up its own tooling, we end up with conflicting conventions and a week of merge conflicts. The folder layout (see "Repository layout" in `README.md`) is already committed; this ticket makes it buildable, linted and protected, so every later ticket can assume `pnpm install && uv sync` works and CI catches mistakes before they reach `main`.

### What you will deliver
- `pnpm-workspace.yaml` covering `apps/*` and `packages/*`, plus a root `package.json` with `lint`, `format`, `typecheck` and `test` scripts and a committed `pnpm-lock.yaml`
- A uv project in `pipeline/` (`pipeline/pyproject.toml`, Python 3.12) and a root `pyproject.toml` that makes `pipeline` a uv workspace member, plus a committed `uv.lock` and `.python-version`
- Python lint and type-check config: ruff and mypy (in `pipeline/pyproject.toml`)
- TypeScript lint and type-check config: eslint, prettier and a base `tsconfig.base.json`
- `.pre-commit-config.yaml` with hooks for ruff, prettier and eslint
- `.github/workflows/ci.yml`: lint, typecheck and tests, path-filtered per package, plus an install check on macOS and Linux
- Branch protection on `main`: PR required, 1 approval, CI green
- `.github/CODEOWNERS` with owners per folder
- `CONTRIBUTING.md`: branch naming, squash merges, definition of done, onboarding checklist
- `.github/pull_request_template.md` and issue templates in `.github/ISSUE_TEMPLATE/`
- An updated "Getting started" section in `README.md`

### Before you start
- **Monorepo**: one git repo holding several projects. Ours holds the phone app (`apps/mobile`), the dashboard (`apps/dashboard`), shared data formats (`packages/schema`) and the Python pipeline (`pipeline/`).
- **pnpm workspace**: lets one `pnpm install` at the root install the JavaScript and TypeScript dependencies for every package listed in `pnpm-workspace.yaml`.
- **uv**: a fast Python package and project manager. `uv sync` creates `.venv/` and installs exactly what `uv.lock` says. A **uv workspace** lets a root `pyproject.toml` include `pipeline/` as a member, so `uv sync` and `uv run pytest pipeline/tests` work from the repo root.
- **ruff**: Python linter and formatter. **mypy**: Python type checker. **eslint**: TypeScript linter. **prettier**: TypeScript/JSON/Markdown formatter. **tsc**: the TypeScript compiler, run with `--noEmit` to type-check.
- **pre-commit**: a tool that runs fast checks (formatting, lint) on your staged files every time you run `git commit`.
- **Path filtering**: CI only runs the Python jobs when Python files change, and the TypeScript jobs when TypeScript files change. This saves time and Actions minutes.
- **Branch protection**: GitHub settings on `main` that block merging until rules are met. **CODEOWNERS**: a file that maps folders to the people or teams who are asked to review changes there.
- The Expo app itself does not exist yet (NOMI-011). There is no `apps/mobile/package.json` yet, so create a minimal `packages/schema/package.json` (name `@nomi/schema`, `"private": true`) with one placeholder file `packages/schema/src/index.ts`, so the TypeScript lint and typecheck jobs have something to run on. Tell the NOMI-002 owner so they build on it.
- You need admin rights on the GitHub repo to set branch protection. The repo is public, so branch protection and GitHub-hosted runners (including macOS) are free.
- Glossary for any other term: `docs/nomi-101.md`.

### Steps
1. Create a branch `<your-name>/<issue-number>-repo-tooling` and open a draft PR linked to this issue.
2. Add `.nvmrc` with the current Node.js LTS major version (check docs.expo.dev for the Node versions Expo supports). Add `"packageManager": "pnpm@<version>"` to the root `package.json` so `corepack enable` installs the same pnpm for everyone.
3. Create `pnpm-workspace.yaml` with `packages: ["apps/*", "packages/*"]`. Create the minimal `packages/schema/package.json` and `packages/schema/src/index.ts` described above.
4. In the root `package.json`, add dev dependencies `typescript`, `eslint`, `typescript-eslint`, `prettier`, and scripts: `"lint": "eslint ."`, `"format": "prettier --write ."`, `"format:check": "prettier --check ."`, `"typecheck": "pnpm -r --if-present typecheck"`, `"test": "pnpm -r --if-present test"`. Run `pnpm install` and commit `pnpm-lock.yaml`.
5. Add `eslint.config.js` (flat config using `typescript-eslint` recommended rules), `.prettierrc` (keep defaults unless the team objects) and `.prettierignore` (ignore `data/`, `packages/schema/generated/`, `pnpm-lock.yaml`). Add `tsconfig.base.json` with `"strict": true`, and a `packages/schema/tsconfig.json` that extends it with a `typecheck` script `tsc --noEmit`.
6. Create `pipeline/pyproject.toml` for the package `nomi-pipeline` with `requires-python = ">=3.12"`, the `src/` layout (code is already in `pipeline/src/nomi_pipeline/`), and dev dependencies `ruff`, `mypy`, `pytest`, `pre-commit`. Add `.python-version` containing `3.12` at the root.
7. Create the root `pyproject.toml` with `[tool.uv.workspace]` and `members = ["pipeline"]`. Run `uv sync` from the root and confirm it installs the pipeline package. If plain `uv sync` does not install the member, use `uv sync --all-packages` and write that in the README instead. Commit `uv.lock`.
8. Configure ruff in `pipeline/pyproject.toml`: `target-version = "py312"`, line length 100, rule sets `E`, `F`, `I`, `UP`, `B`. Configure mypy with `strict = true` for `nomi_pipeline`.
9. Add `pipeline/tests/test_smoke.py` that imports `nomi_pipeline` and asserts true, so `uv run pytest pipeline/tests` has a test to run.
10. Write `.pre-commit-config.yaml`: the official ruff hooks (`ruff` with `--fix`, and `ruff-format`), plus `local` hooks that run `pnpm exec prettier --check` and `pnpm exec eslint` on staged TypeScript, JSON and Markdown files. Keep mypy and tsc out of pre-commit (too slow); they run in CI.
11. Write `.github/workflows/ci.yml` triggered on `pull_request` and on `push` to `main`:
    - A `changes` job using `dorny/paths-filter` to output `python` (true when `pipeline/**`, `pyproject.toml` or `uv.lock` change) and `typescript` (true when `apps/**`, `packages/**`, `package.json`, `pnpm-lock.yaml` or config files change).
    - A `python` job (runs if `python` changed): set up uv, `uv sync --locked`, `uv run ruff check`, `uv run ruff format --check`, `uv run mypy pipeline/src`, `uv run pytest pipeline/tests`.
    - A `typescript` job (runs if `typescript` changed): set up Node from `.nvmrc`, `corepack enable`, `pnpm install --frozen-lockfile`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`.
    - An `install` job with a matrix of `ubuntu-latest` and `macos-latest` that runs `pnpm install --frozen-lockfile && uv sync --locked` on a clean checkout. Run it when lockfiles or `package.json`/`pyproject.toml` files change.
    - A final `ci-ok` job with `needs: [python, typescript, install]` and `if: always()` that fails if any needed job failed or was cancelled, and passes if they passed or were skipped.
12. Make `ci-ok` the only required status check. Reason: if you path-filter whole workflows with `on.pull_request.paths`, a skipped workflow leaves its required check stuck as "pending" and the PR can never merge. One always-running summary job avoids that.
13. Write `.github/CODEOWNERS`. Map `apps/` to Visualization, `pipeline/src/nomi_pipeline/fetch/`, `ingest/`, `identity/`, `build/` to Platform, `pipeline/src/nomi_pipeline/extract/`, `evidence/`, `score/` and `pipeline/knowledge/` to Data Analysis, `packages/schema/` to both Platform and Data Analysis (its README requires both), and `docs/adr/`, `.github/` and `planning/` to the cofounders. Use GitHub team handles (`@org/platform`) if the repo is in an organization; otherwise list usernames.
14. In GitHub, go to Settings, then General, then Pull Requests: allow squash merging only, and turn on "Automatically delete head branches".
15. In Settings, then Branches (or Rules, then Rulesets), protect `main`: require a pull request before merging, require 1 approval, dismiss stale approvals when new commits are pushed, require the `ci-ok` status check to pass, require branches to be up to date, and block force pushes and deletion.
16. Write `.github/pull_request_template.md` with sections: "Closes #", "What changed", "How I tested it", "Done when checklist copied from the issue", and an empty "Privacy checklist" heading with a comment saying NOMI-003 fills it in.
17. Write `.github/ISSUE_TEMPLATE/ticket.md` using the format in `planning/ticket-template.md`, and `.github/ISSUE_TEMPLATE/bug.md` with: what happened, what you expected, steps to reproduce, device or OS, screenshots.
18. Write `CONTRIBUTING.md` with:
    - Branch naming: `<name>/<issue>-slug`, for example `maya/12-barcode-parser`.
    - One PR per issue, linked with `Closes #12`; open it as a draft early.
    - Squash merges only; the squashed commit title is the PR title.
    - Definition of done (from `planning/README.md`): merged with tests, documented in the relevant README, and demoable; every "Done when" box checked.
    - Onboarding checklist: install git, Node (version in `.nvmrc`), `corepack enable`, uv; clone; run `pnpm install && uv sync`; run `uv run pre-commit install`; run the lint and test commands; read `docs/nomi-101.md`; join your team channel; pick a `good first issue`.
    - The rule that raw data and secrets are never committed (`data/` and `.env` are gitignored).
19. Replace the "Getting started" section of `README.md` with the install commands and a link to `CONTRIBUTING.md`.
20. Test on a fresh clone on a Mac and on Linux (CI's `install` job counts for Linux; a teammate's Linux laptop or WSL is a bonus). Fix anything that needs a manual step not written in `CONTRIBUTING.md`.
21. Open a throwaway PR that adds an unused import to `pipeline/tests/test_smoke.py`. Confirm the `python` job fails, `ci-ok` fails and the merge button is blocked. Take a screenshot, add it to your real PR, then close the throwaway PR without merging.
22. Mark your PR ready for review and ask the other cofounder to review.

### Done when
- [ ] `pnpm install && uv sync` (or the `--all-packages` variant, if documented) succeeds on a fresh clone on macOS and on Linux, with no undocumented steps
- [ ] `uv run ruff check`, `uv run mypy pipeline/src`, `uv run pytest pipeline/tests`, `pnpm lint` and `pnpm typecheck` all pass on `main`
- [ ] Pre-commit hooks run on `git commit` after `uv run pre-commit install`
- [ ] CI runs on every PR, and the Python and TypeScript jobs only run when their paths change
- [ ] `main` requires a PR, 1 approval and a green `ci-ok` check; force pushes are blocked; only squash merges are allowed
- [ ] `.github/CODEOWNERS` covers every top-level folder
- [ ] A PR with a lint error is blocked from merging (screenshot in the PR)
- [ ] `CONTRIBUTING.md`, the PR template and both issue templates are merged
- [ ] PR reviewed by the other cofounder

### How to check your work
Ask a teammate who hasn't touched the repo to follow `CONTRIBUTING.md` on their own laptop. They should get from `git clone` to passing `uv run pytest pipeline/tests` and `pnpm lint` without asking you anything. Then open a PR that only edits a Markdown file in `docs/`: the `python` and `typescript` jobs should be skipped and `ci-ok` should still pass, so the PR can merge after one approval.

### Out of scope
- The Expo app and its build setup (NOMI-011)
- JSON Schemas, code generation and the "generated files are stale" CI check (NOMI-002)
- The content of the privacy checklist in the PR template (NOMI-003)
- The `pipeline` command-line tool and `pipeline fetch` (NOMI-008)
- The golden-vector parity job in CI (NOMI-057)

### Resources
- pnpm workspaces: https://pnpm.io/workspaces
- uv workspaces: https://docs.astral.sh/uv/concepts/projects/workspaces/
- ruff: https://docs.astral.sh/ruff/
- mypy: https://mypy.readthedocs.io/
- typescript-eslint: https://typescript-eslint.io/
- pre-commit: https://pre-commit.com/
- GitHub protected branches: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- GitHub CODEOWNERS: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners
- Repo layout: `README.md`; conventions: `planning/README.md`

---

## NOMI-002: Define the shared data contracts v0 as JSON Schemas with generated types
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

### Summary
Write five JSON Schemas in `packages/schema/schemas/` (`product`, `ingredient-dimensions`, `term-tables`, `score-record`, `signal`) and generate TypeScript types and Pydantic models from them, with CI failing whenever the generated files are out of date. Every team codes against these files.

### Why this matters
Platform produces product data, Data Analysis turns it into scores, and Visualization renders scores on the phone. If the three teams agree on these formats now, they can work in parallel instead of waiting for each other. Every downstream ticket reads or writes one of these schemas, so a missing field here becomes a blocked ticket later.

### What you will deliver
- `packages/schema/schemas/common.schema.json` with shared definitions (NDC11, UNII, persona, risk dimension, severity, citation, provenance)
- `packages/schema/schemas/product.schema.json`
- `packages/schema/schemas/ingredient-dimensions.schema.json`
- `packages/schema/schemas/term-tables.schema.json`
- `packages/schema/schemas/score-record.schema.json`
- `packages/schema/schemas/signal.schema.json`
- One small valid sample per schema in `packages/schema/fixtures/schema-samples/`, plus tests that validate them
- Generated TypeScript types in `packages/schema/generated/ts/` and Pydantic models in `packages/schema/generated/python/`
- A `codegen` script and a CI step that fails if the generated files are stale
- An updated `packages/schema/README.md` that describes each schema in a few lines

### Before you start
- **JSON Schema**: a standard way to describe the shape of JSON data (required fields, types, allowed values). Use draft 2020-12. Tools in both Python and TypeScript can validate data against it.
- **Pydantic**: the Python library for typed data models. **Codegen**: generating code (TypeScript types, Pydantic classes) from the schemas so nobody writes them by hand.
- **NDC11**: the 11-digit, no-hyphen National Drug Code we store, e.g. `50580044902`. **UNII**: FDA's 10-character ingredient ID; our main ingredient key.
- **SPL set id and version**: a DailyMed label's stable ID and its version number.
- **Marketing category**: how a product is legally sold (OTC monograph, NDA, unapproved homeopathic and so on). **OTC category**: our grouping such as internal analgesics or antacids (values assigned in NOMI-026).
- **Persona, risk dimension, severity 0-3, condition modifier, hard stop, term tables, rubric, signal, IC/IC025**: see the glossary in `docs/nomi-101.md`. In short: the phone adds up term-table points for a product and a profile to get a score.
- The dimension list comes from NOMI-016 (`docs/scoring/dimensions.md`), written this same sprint. Start with the 15 dimensions listed in NOMI-016's ticket and update the enum when that doc merges.
- NOMI-001 sets up pnpm and uv this sprint. If it hasn't merged, work in `packages/schema/` anyway, run the generators with `npx` and `uvx`, and wire them into CI after NOMI-001 lands.
- These are contracts, not logic. You define field names and shapes; the actual values come from later tickets (rubric numbers in NOMI-049, scores in NOMI-051).

### Steps
1. Create `common.schema.json` with these `$defs`:
    - `ndc11`: string, pattern `^[0-9]{11}$`
    - `unii`: string, pattern `^[A-Z0-9]{10}$`
    - `persona`: enum `adult_18_64`, `adult_65_plus`, `teen_12_17`, `child_6_11`, `child_2_5`, `under_2`, `pregnant`, `breastfeeding`
    - `dimension`: enum of snake_case ids from NOMI-016, e.g. `liver`, `gi_bleeding`, `cardiovascular_bp`, `kidney`, `anticholinergic_cognitive`, `sedation_falls`
    - `severity`: integer 0 to 3
    - `citation`: object with `source` (e.g. `fda_label`, `stopp_start`, `acb`, `faers`), `document_id` (e.g. an SPL set id), `section`, `url`, optional `quote`
    - `provenance`: object with `dataset_version`, `rubric_version`, `code_commit`, `generated_at` (date-time)
2. Write `product.schema.json` with: `ndc11`, `spl_set_id`, `spl_version`, `brand_name`, `generic_name`, `marketing_category`, `otc_category`, `uses` (array of strings), and `ingredients`, an array of objects with `unii`, `name`, `strength` (number), `unit` (e.g. `mg`), and optional `per_amount` and `per_unit` for liquids (e.g. 650 mg per 30 mL).
3. Write `ingredient-dimensions.schema.json`: one document per ingredient with `unii`, `name`, `ratings` (array of `dimension`, `persona`, `severity`, `citations`), and `modifiers` (array of `dimension`, `condition` such as `hypertension` or medication type such as `anticoagulants`, `severity_change` such as `+1`, `citations`). Make `citations` required with `minItems: 1` whenever severity is above 0 (use `if`/`then`).
4. Write `term-tables.schema.json`: `model_version`, `rubric_version`, `base_score` (e.g. 100), `terms` (array of `unii` or ingredient class, `dimension`, `persona`, optional `condition`, `points` as an integer), and `hard_stops` (array of `id`, the matching conditions, the result such as `red`, a `message_template_id` and `citations`). This is what the phone evaluates.
5. Write `score-record.schema.json`: `ndc11`, `profile` (persona plus optional `conditions` and `medication_types` arrays), `score` (integer 0-100), `tier`, `contributions` (array of `dimension`, `points`, `citations`), `hard_stops_triggered`, `benchmark` (`use`, `percentile`), `alternatives` (array of `ndc11`, `score`, `reason`), `explanation` (array of `template_id`, rendered `text`, `citations`), and `provenance`.
6. Write `signal.schema.json`: `unii` (ingredient), `dimension`, `age_band` (enum `0-11`, `12-17`, `18-64`, `65+`), `sex` (enum `F`, `M`, `all`), `ic`, `ic025` (numbers), `report_count` (integer, at least 0), and optional `event_group`.
7. Give every schema a `$id`, a `title`, a `description` on every field, and `"additionalProperties": false` so typos in field names fail validation.
8. Write one valid sample per schema in `packages/schema/fixtures/schema-samples/`, e.g. `product.sample.json` for a single-ingredient acetaminophen 500 mg product. Use realistic but unverified values, and add a one-line `README.md` in that folder saying these are format samples, not verified data (the verified products come in NOMI-015).
9. Add tests that validate each sample: a Python test in `pipeline/tests/schema/test_samples.py` using the `jsonschema` package, and one invalid sample per schema that must fail (for example severity 4, or an NDC with hyphens).
10. Set up codegen. TypeScript: `json-schema-to-typescript` writes `packages/schema/generated/ts/*.ts`. Python: `datamodel-code-generator` with `--output-model-type pydantic_v2.BaseModel` writes `packages/schema/generated/python/nomi_schema/*.py`. Add a small `packages/schema/generated/python/pyproject.toml` (package `nomi-schema`) and add it as a uv workspace member and a dependency of `pipeline`, so the pipeline can `from nomi_schema.product import Product`.
11. Add a `codegen` script in `packages/schema/package.json` that runs both generators, so `pnpm --filter @nomi/schema codegen` regenerates everything. Add a header comment "Generated from packages/schema/schemas. Do not edit." to generated files if the tools support it.
12. Add a CI step (in the workflow from NOMI-001) that runs `codegen` and then `git diff --exit-code packages/schema/generated`. It fails if someone changed a schema without regenerating, or edited a generated file by hand.
13. Prove the types compile: import `Product` in a mypy-checked file in `pipeline/src/nomi_pipeline/` and run `uv run mypy pipeline/src`; import the TypeScript `Product` type in the app (`apps/mobile`, once NOMI-011 lands) and run `tsc --noEmit`. If NOMI-011 hasn't merged by midweek, use `packages/schema/src/index.ts` as a stand-in consumer and add the app import when it lands.
14. Update `packages/schema/README.md` with one short paragraph per schema and the `codegen` command.
15. Walk the Platform, Data Analysis and Visualization leads through the schemas in a 30-minute call. Record requested changes in the PR, apply them, and get approval from both cofounders.

### Done when
- [ ] All five schemas plus `common.schema.json` are merged in `packages/schema/schemas/`
- [ ] Every field listed in steps 2-6 exists in its schema
- [ ] Every non-zero severity and modifier in `ingredient-dimensions` requires at least one citation
- [ ] Each schema has a valid sample that passes and an invalid sample that fails, tested in CI
- [ ] Generated TypeScript and Pydantic files exist in `packages/schema/generated/`
- [ ] CI fails when generated files are stale (shown with a test PR or a screenshot)
- [ ] Generated types compile in the app and the pipeline
- [ ] Both cofounders approve the schemas

### How to check your work
Change one field name in `product.schema.json` without running `codegen` and push to a test branch: CI should fail on the diff check. Then hand `product.schema.json` and `score-record.schema.json` to someone from Visualization and ask them to sketch the result screen's data needs. Every field they ask for should already be in the schema or be a deliberate "later" decision written in the PR.

### Out of scope
- The label extraction schema (NOMI-032)
- The five hand-verified reference products in `packages/schema/examples/` (NOMI-015)
- Golden scoring vectors in `packages/schema/golden/` (NOMI-051, checked in CI by NOMI-057)
- Defining the dimensions and personas themselves (NOMI-016)
- Actual rubric points and hard-stop rules (NOMI-049, NOMI-051)

### Resources
- JSON Schema: https://json-schema.org/
- Pydantic: https://docs.pydantic.dev/
- json-schema-to-typescript: https://github.com/bcherny/json-schema-to-typescript
- datamodel-code-generator: https://github.com/koxudaxi/datamodel-code-generator
- Glossary: `docs/nomi-101.md`; folder guide: `packages/schema/README.md`

---

## NOMI-003: Write ADR-0001 (architecture) and ADR-0002 (privacy)
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Write and merge two architecture decision records: `docs/adr/0001-architecture.md`, which records how scores are computed and why, and `docs/adr/0002-privacy.md`, which records that health data stays on the phone. Add a privacy checklist to the PR template and link both ADRs from the root README.

### Why this matters
We decided to compute scores in our pipeline and run the final personalized scoring on the phone, so no health data ever reaches our servers. Writing this down now stops the team from relitigating it mid-semester, gives new members one place to learn why things are built this way, and gives the law clinic (NOMI-021) something concrete to review.

### What you will deliver
- `docs/adr/0001-architecture.md`
- `docs/adr/0002-privacy.md`
- A "Privacy checklist" section in `.github/pull_request_template.md`
- Links to both ADRs from the root `README.md`, and status updated in `docs/adr/README.md`

### Before you start
- **ADR** (Architecture Decision Record): a short document recording one decision, the options considered and the consequences. Ours use `docs/adr/0000-template.md` (Context, Decision, Alternatives considered, Consequences). An ADR is accepted when it is merged.
- **Term tables**: the scoring model exported as lookup tables ("this ingredient, this dimension, this persona costs N points"). The phone only adds them up.
- **Risk dimension, persona, rubric**: see the glossary in `docs/nomi-101.md`.
- **Evidence-synthesis model**: the planned later model that sets the term-table weights from published evidence instead of hand-written rubric rules. Because it exports the same term tables, the app does not change when it replaces the rubric.
- **Analytics and crash-reporting SDKs**: third-party code libraries (for example usage analytics or crash reporters) that send data from the app to an outside company.
- **End-to-end encryption**: data is encrypted on the device and only the user's own devices can decrypt it; our servers would see only ciphertext.
- `README.md`, `planning/README.md` and `docs/nomi-101.md` already state these decisions briefly. The ADRs are the full, reasoned version.
- If NOMI-001 hasn't merged and `.github/pull_request_template.md` doesn't exist yet, create it with only the privacy checklist; the NOMI-001 owner merges their sections around it.

### Steps
1. Copy `docs/adr/0000-template.md` to `docs/adr/0001-architecture.md` and `docs/adr/0002-privacy.md`. Fill in Status `proposed`, today's date and both cofounders as deciders.
2. In ADR-0001 "Context", describe the problem: score thousands of OTC products for different kinds of people, explain every point, work offline in a store, and run on zero budget.
3. In ADR-0001 "Decision", state each part plainly:
    - The pipeline builds the scoring model and exports it as term tables into a versioned SQLite file.
    - The phone sums term-table points for the user's profile and applies hard stops. No modeling logic in the app.
    - Every ingredient is rated on about 15 risk dimensions (defined in NOMI-016).
    - Rubric v0 (hand-written, transparent rules) for the demo; an evidence-synthesis model later, using the same term-table format.
    - LLMs are used only in the offline pipeline (for example to help read labels), their output is checked, and they never produce scores or user-facing text directly.
4. In ADR-0001 "Alternatives considered", give one short paragraph per rejected option and why:
    - Live inference server: would need the user's health profile sent to a server, needs signal in the store, and costs money to run.
    - Classifier trained on FAERS: FAERS has no denominator and has reporting biases, so it cannot give risk rates, and a trained classifier's output can't be traced to a citation.
    - BioBERT (a biomedical language model): heavy to run, hard to explain, and not needed because labels are already split into standard sections and rules plus an offline LLM cover extraction.
    - Redis (an in-memory server database): there is no server-side hot path to cache; the dataset lives in SQLite on the phone.
5. In ADR-0001 "Consequences", list what gets easier (offline, private, cheap, explainable) and harder (dataset size on the phone, updating the app's data requires a new dataset release, Python and TypeScript must agree, which NOMI-057 checks).
6. In ADR-0002 "Decision", state each rule:
    - The user's profile, conditions, medicine cabinet and scan history stay on the device, encrypted.
    - Every user downloads the same dataset, so downloading it reveals nothing about the user.
    - No health data goes to analytics or crash-reporting SDKs. Any such SDK must be reviewed against this ADR before it is added.
    - Any future sync between a user's devices uses end-to-end encryption only.
    - No training on user data without explicit opt-in.
7. In ADR-0002 "Context" and "Consequences", explain the reasons: health data is sensitive, a server that holds none can't leak it, and keeping it on the phone keeps us clear of rules such as the FTC Health Breach Notification Rule and Washington's My Health My Data Act. Write "to be confirmed by the law clinic (NOMI-021)" next to any legal statement; don't state legal conclusions as fact.
8. Add to `.github/pull_request_template.md` a "Privacy checklist" with checkboxes such as:
    - This PR does not send profile, condition, medication, cabinet or scan-history data off the device.
    - This PR adds no analytics, crash-reporting or other third-party SDK, or it was reviewed against ADR-0002.
    - This PR does not log health data.
    - This PR commits no raw data, secrets or personal information.
9. Add a "Decisions" line to `README.md` linking both ADRs, and update the table in `docs/adr/README.md` if anything changed.
10. Ask one member of each team to read the ADRs and comment on anything unclear. Then change Status to `accepted` and merge after both cofounders approve.

### Done when
- [ ] `docs/adr/0001-architecture.md` covers every item in steps 3 and 4, including all four rejected options with reasons
- [ ] `docs/adr/0002-privacy.md` covers every rule in step 6
- [ ] Legal statements in ADR-0002 are marked as pending law clinic review
- [ ] The PR template contains the privacy checklist
- [ ] Both ADRs are merged with Status `accepted` and linked from the root `README.md`
- [ ] Both cofounders approved the PR

### How to check your work
Give ADR-0001 to a new team member and ask: "Why can't the app just call a server to get the score?" and "Where does the score's math live?" Give ADR-0002 to someone else and ask: "Can we add an analytics SDK that logs which profile was active?" If they answer correctly from the ADRs alone, they are clear enough.

### Out of scope
- Legal review of ADR-0002 and other legal questions (NOMI-021)
- Implementing encrypted profile storage (NOMI-039)
- The SQLite dataset format and build (NOMI-038)
- The rubric itself (NOMI-049)

### Resources
- ADR template: `docs/adr/0000-template.md`
- About ADRs: https://adr.github.io/
- FTC Health Breach Notification Rule: https://www.ftc.gov/legal-library/browse/rules/health-breach-notification-rule
- Product overview: `docs/nomi-101.md`

---

## NOMI-004: Write demo script v1 and present it at the Oct 19 kickoff
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Write `docs/demo/script.md`, the step-by-step script for the Nov 20 demo, with each moment linked to the tickets that make it work, and present it to every team at the Oct 19 kickoff.

### Why this matters
The Nov 20 demo is the goal of this whole backlog. Writing the script first means every ticket can be traced to something the audience will see, and anything that doesn't appear in the script can wait. Teams use it to decide what to build first and what to cut.

### What you will deliver
- `docs/demo/script.md` with every demo beat in order, the key dates, and a ticket map
- A short slide or screen share of the script used at the Oct 19 kickoff (stored in the team shared drive)

### Before you start
- **Demo beat**: one moment in the demo, such as "scan a box from the audience". Each beat has what the presenter does, what the audience sees and why it matters.
- **Airplane mode**: the phone has no network. Nomi works offline because the dataset is on the phone, so scanning in airplane mode proves it.
- **Profile**: who the scan is for (age band, conditions, medication types). Switching profiles rescores the same box.
- **Duplicate-ingredient warning**: alerts when two products contain the same ingredient, such as acetaminophen in both NyQuil and Tylenol.
- **Homeopathic product**: sold as OTC but never evaluated by FDA for safety or effectiveness. Nomi shows a notice instead of a score (NOMI-026).
- **Coverage dashboard and FAERS signal explorer**: internal web pages showing how much of the market we cover and what adverse event reports show (NOMI-042, NOMI-071). FAERS is FDA's adverse event reporting system; see the glossary in `docs/nomi-101.md`.
- Read the ticket list in `planning/backlog.md` so you can map beats to tickets.
- Medical claims in the script must match what the knowledge base will cite. Phrase them as "the label warns" or "published criteria for older adults advise against", not as diagnoses.

### Steps
1. Confirm the demo time slot length and format (stage, table, projector) with the organizers. Write it at the top of `docs/demo/script.md`.
2. Write the beats in order. For each one, add: presenter actions, what is on screen, the box and profile used, the point being made, and the tickets it depends on.
3. Beat: **blind scan**. Someone in the audience hands over a box we didn't choose. The phone is in airplane mode (show this on the projected screen). Scan it and show the score, reasons and safer option. Tickets: NOMI-011, NOMI-025, NOMI-037, NOMI-040, NOMI-060.
4. Beat: **profile switch**. Scan Benadryl (diphenhydramine) for a 30-year-old, then switch to a 75-year-old. The score drops because diphenhydramine is strongly anticholinergic, and published criteria advise older adults to avoid it. Tickets: NOMI-035, NOMI-061.
5. Beat: **tradeoff**. Compare Tylenol and Aleve for a 70-year-old with high blood pressure. Aleve (naproxen, an NSAID) loses points on GI bleeding, blood pressure and kidney; Tylenol (acetaminophen) carries a liver warning at high doses. Show the comparison, not just two numbers. Tickets: NOMI-034, NOMI-055, NOMI-062.
6. Beat: **duplicate acetaminophen**. Show that NyQuil plus Tylenol doubles the acetaminophen. Pick a NyQuil variant that contains acetaminophen and confirm the ingredients on DailyMed. Ticket: NOMI-052.
7. Beat: **edge states**. Scan a homeopathic product (shows "Not evaluated by FDA for safety or effectiveness", no score) and a barcode we can't find (shows the not-found state and search fallback). Tickets: NOMI-026, NOMI-030, NOMI-063.
8. Beat: **data story**. Show the coverage dashboard and the FAERS signal explorer, including the stated limitations. Tickets: NOMI-042, NOMI-071.
9. Add a "Key dates" section: feature freeze Nov 12, code freeze Nov 17, blind test Nov 18, rehearsals Nov 18-19, demo Nov 20.
10. Add a "Ticket map" table: beat, tickets, owning team, sprint. Mark beats that depend on P1 tickets as "can be cut" and say what replaces them.
11. Add a "Disclaimer" line the presenter says or shows: Nomi provides information from public FDA data and published criteria and is not medical advice.
12. Merge the script, then present it at the Oct 19 kickoff and post the link in every team channel.

### Done when
- [ ] `docs/demo/script.md` is merged and includes all six beats in steps 3-8
- [ ] Every beat lists the tickets it depends on
- [ ] Key dates section lists feature freeze Nov 12, code freeze Nov 17, blind test Nov 18 and rehearsals Nov 18-19
- [ ] The script was presented at the Oct 19 kickoff and shared with every team (link posted in each team channel)

### How to check your work
Pick any P0 ticket in `planning/backlog.md` at random and find the beat it supports in the ticket map. If you can't, either the script is missing a beat or the ticket may not belong before the demo; raise it at kickoff. Read the script aloud with a timer and confirm it fits the time slot.

### Out of scope
- Script v2, choosing the final demo boxes and the feature freeze announcement (NOMI-050)
- Wireframes of the demo screens (NOMI-013)
- Blind test and rehearsals (NOMI-064)
- Preparing the demo phones (NOMI-068)

### Resources
- DailyMed, to confirm product ingredients: https://dailymed.nlm.nih.gov/dailymed/
- Backlog: `planning/backlog.md`; sprint plan: `planning/README.md`
- Glossary: `docs/nomi-101.md`

---

## NOMI-005: Contact pharmacy faculty and book a first partnership meeting
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Write a one-page partnership pitch, identify at least 10 pharmacy faculty in Georgia, send personal emails, and book at least one meeting. Track every contact in a shared sheet.

### Why this matters
Our scores need clinical validation to be trustworthy, and we can't pay pharmacists. GT has no pharmacy school, so we offer nearby pharmacy faculty a research partnership: access to the dataset, co-authorship, and research projects for their students. This is the critical path for everything clinical, including the rubric review in NOMI-036.

### What you will deliver
- A one-page pitch titled "Validating a personalized consumer OTC medication-safety score", as a PDF in the team shared drive
- A contact tracking sheet in the team shared drive (not in this public repo) with at least 10 faculty contacts
- At least 10 personal emails sent from the cofounders
- At least 1 meeting booked, with date and attendee recorded in the sheet
- A comment on this issue summarizing outreach status (counts only, no personal contact details)

### Before you start
- **Drug information, geriatrics, pediatrics, ambulatory care**: pharmacy specialties that match our risks: drug information (evaluating evidence), geriatrics (older adults, our 65+ persona), pediatrics (children's dosing), ambulatory care (outpatient medication management).
- **Pharmacy schools near Atlanta**: Mercer University College of Pharmacy (Atlanta), University of Georgia College of Pharmacy (Athens), and PCOM Georgia School of Pharmacy (Suwanee). Faculty directories are on each school's website.
- **APhA-ASP**: the American Pharmacists Association Academy of Student Pharmacists. Each pharmacy school has a student chapter. Generation Rx is a medication-safety education program that student chapters run; confirm the current program details on the chapter or APhA site.
- **STOPP/START, ACB, rubric**: see the glossary in `docs/nomi-101.md`. These are the kinds of materials a partner would review.
- Faculty names and emails are personal information. Keep them in the shared drive sheet, never in this public repo or in public issue comments.
- What we can offer (agree on this before writing): dataset access for research, co-authorship on publications, student research projects, credit in the app. What we must not promise: payment.

### Steps
1. Agree between the cofounders what we offer and what we ask for: for example, a one-hour rubric review in early November (NOMI-036) and ongoing review of scores.
2. Write the one-page pitch: the problem (OTC risks not visible at purchase), what Nomi does (one paragraph and a screenshot or wireframe), why it is a research opportunity (a new consumer-facing scoring method that needs clinical validation), what we offer, what we ask, and both cofounders' contact details. Save it as a PDF in the shared drive.
3. Create the tracking sheet with columns: name, school, department, specialty, email, source page URL, contacted by, date sent, follow-up date, status (`not contacted`, `sent`, `replied`, `meeting booked`, `declined`), notes.
4. Find at least 10 faculty across Mercer, UGA and PCOM Georgia in drug information, geriatrics, pediatrics and ambulatory care. Use each school's public faculty directory and note the page URL.
5. Write a short personal email per person (under 150 words): who we are, why their work is relevant (mention something specific from their profile), the ask (a 30-minute call), and the pitch PDF attached. Send from the cofounders' own accounts, not a mass mailer.
6. Contact the APhA-ASP chapter at each of the three schools about Generation Rx and about student involvement. Log them in the sheet.
7. Send a polite follow-up to anyone who hasn't replied after 4-5 business days.
8. When someone agrees, book a 30-minute meeting, record it in the sheet, and prepare a short agenda: introductions, demo of the wireframes, how a review would work, credit and co-authorship.
9. Post a status comment on this issue: number contacted, replies, meetings booked. No names or emails.

### Done when
- [ ] One-page pitch PDF is in the shared drive
- [ ] Tracking sheet in the shared drive lists at least 10 faculty with every column filled
- [ ] At least 10 emails sent (dates recorded in the sheet)
- [ ] APhA-ASP chapters at Mercer, UGA and PCOM Georgia contacted
- [ ] At least 1 meeting booked, with date recorded in the sheet
- [ ] Status comment (counts only) posted on this issue

### How to check your work
Open the sheet and filter by status: at least 10 rows should be `sent` or later, and at least one should be `meeting booked`. Read your pitch out loud to someone outside the team; they should be able to say in one sentence what we're asking for and what the faculty member gets.

### Out of scope
- The rubric review session itself (NOMI-036)
- Formal agreements on credit and IP (NOMI-021 for legal questions; NOMI-036 for credit)
- User interviews with consumers (NOMI-022)

### Resources
- Mercer University College of Pharmacy: https://pharmacy.mercer.edu/
- UGA College of Pharmacy: https://rx.uga.edu/
- PCOM: https://www.pcom.edu/
- American Pharmacists Association: https://www.pharmacist.com/
- Product overview to adapt for the pitch: `docs/nomi-101.md`

---

## NOMI-006: Audit data source licenses and write `docs/data-sources.md`
**Team:** cofounders | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Check the license and terms of every dataset Nomi plans to use, and record the results in `docs/data-sources.md`, one row per source, so we only build on data we are allowed to use commercially.

### Why this matters
The repo is public and Nomi is meant to become a commercial product. Before any pipeline code depends on a dataset, we confirm we're allowed to use it commercially and know what attribution we owe. DrugBank is already ruled out because its academic license forbids commercial use; finding that kind of problem after the pipeline is built would cost weeks.

### What you will deliver
- `docs/data-sources.md` with a table: one row per source, with URL, license, commercial use allowed (yes / no / with conditions), required attribution, refresh cadence, and notes
- A "Rules" section stating that raw data is never committed to git
- A list of open questions to pass to the law clinic (NOMI-021), if any

### Before you start
- **Public domain**: no copyright restrictions; anyone may use it, including commercially. Most US federal government data is public domain, but confirm each source's own terms page.
- **openFDA NDC directory**: FDA's list of every marketed drug product and package. **FAERS**: FDA's adverse event reports. **DailyMed**: NLM's site with the full label of every drug. See `docs/nomi-101.md`.
- **RxNorm and UMLS**: RxNorm is NLM's drug vocabulary. It is distributed inside the UMLS, which requires a free license. **SAB** is the source column in the RxNorm files; rows with `SAB=RXNORM` are NLM's own content, while other SAB values come from third parties that may have their own restrictions.
- **ACB scale**: Anticholinergic Cognitive Burden scale, rating drugs 0-3. **STOPP/START**: published criteria for medicines older adults should avoid or start. **AGS Beers Criteria**: the American Geriatrics Society's list of potentially inappropriate medicines for older adults; it is copyrighted.
- **MedDRA**: the medical vocabulary FAERS uses for reactions. The FAERS files contain MedDRA terms, and NOMI-044 plans to map them to MedDRA's hierarchy, which may require a MedDRA license. Include it in the audit.
- **Refresh cadence**: how often the source publishes updates (daily, weekly, monthly, quarterly).
- You are recording what each source's terms say, not giving legal opinions. Quote or link the exact terms page, and mark anything unclear as an open question for NOMI-021.

### Steps
1. Create `docs/data-sources.md` with a short intro and a table with columns: Source, What we use it for, URL, License, Commercial use allowed, Required attribution, Refresh cadence, Notes / ticket.
2. openFDA NDC directory: read the openFDA terms page, confirm the data is public domain, record the attribution openFDA asks for (if any) and the update cadence. Note it's used in NOMI-008 and NOMI-009.
3. FAERS: confirm public domain status on FDA's site and the quarterly release cadence. Note in the row that FAERS contains MedDRA terms (see step 6).
4. DailyMed: confirm the terms for SPL label files on DailyMed's site and the release cadence of the full and update files. Note that package images may show brand logos and trademarks; record whether we can display them, or mark it as an open question.
5. RxNorm: record that it needs a free UMLS license and that we use only `SAB=RXNORM` content. Check and record: whether every person who downloads the files needs their own license, and whether mirroring the RRF files to our R2 bucket (NOMI-019) is allowed. Record the monthly release cadence.
6. MedDRA: check the terms on meddra.org for using MedDRA terms and hierarchy in a commercial product. If commercial use requires a paid subscription, flag it to both cofounders and NOMI-044's owner right away.
7. ACB scale: find the original publication and any updated list, record the citation we must give, and the reuse terms. If no reuse terms are stated, mark it as an open question.
8. STOPP/START: find the current published version (confirm which version is latest), record the citation, the article's license (open access license or not), and whether structured reuse in a commercial app is allowed.
9. AGS Beers Criteria: record that it is copyrighted by the American Geriatrics Society. Decide with the other cofounder: request permission from AGS (record the request and date) or don't use it. Write the decision in the row.
10. DrugBank: add a row marked "Rejected: academic license forbids commercial use" so nobody adds it later.
11. Add a "Rules" section: raw and generated data is never committed to git (`data/` is gitignored); every new source needs a row here, reviewed by a cofounder, before code depends on it; attributions listed here must appear in the app's About screen.
12. Add an "Open questions" section listing anything for the law clinic (NOMI-021).
13. Open a PR and ask the other cofounder to review; post the merged link in the Platform and Data Analysis channels, since NOMI-008, NOMI-018 and NOMI-019 depend on it.

### Done when
- [ ] `docs/data-sources.md` is merged
- [ ] Rows exist for openFDA NDC directory, FAERS, DailyMed, RxNorm, ACB scale, STOPP/START, AGS Beers Criteria, MedDRA and DrugBank
- [ ] Each source has URL, license, commercial use allowed, required attribution and refresh cadence filled in (or "open question" with the reason)
- [ ] openFDA NDC directory, FAERS and DailyMed public domain status confirmed with a link to the terms
- [ ] RxNorm row states the UMLS license requirement and `SAB=RXNORM` restriction
- [ ] Beers row records the decision (permission requested, or not used)
- [ ] The rule that raw data is never committed to git is written down
- [ ] Reviewed by the other cofounder

### How to check your work
For each row, click the URL and find the sentence on that page that supports the License and Commercial use columns. If you can't point to a sentence, change the cell to "open question". Then ask a Platform member: "Can you mirror RxNorm files to R2?" They should find the answer in the doc.

### Out of scope
- Legal advice and resolving open questions (NOMI-021)
- Applying for the UMLS license and downloading RxNorm (NOMI-019)
- Digitizing STOPP/START and ACB (NOMI-018)
- Setting up the R2 mirror (NOMI-008)

### Resources
- openFDA terms of service: https://open.fda.gov/terms/
- openFDA downloads: https://open.fda.gov/data/downloads/
- FAERS quarterly data files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/index.html
- UMLS licensing: https://www.nlm.nih.gov/research/umls/index.html
- MedDRA: https://www.meddra.org/
- American Geriatrics Society: https://www.americangeriatrics.org/

---

## NOMI-020: Run the barcode ground-truth collection drive and commit `barcodes.csv`
**Team:** all | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none | **Extra:** good first issue

### Summary
Organize a team-wide drive where every member scans about 25 OTC medicine boxes in assigned stores and aisles, then clean the results into `pipeline/tests/fixtures/barcodes.csv` with at least 300 unique barcodes. One person owns the drive; everyone spends about two hours scanning.

### Why this matters
We need real barcodes from real shelves to test identity resolution (NOMI-025), which turns a barcode into a product, and to rehearse the demo. Store brands matter most, because they are where barcode lookups usually fail. Without this file, we can't measure our coverage target (at least 90% by Oct 29).

### What you will deliver
- A Google Form (or similar free form) for submissions, shared with the team
- A store and aisle assignment sheet in the team shared drive
- `pipeline/tests/fixtures/barcodes.csv` with at least 300 unique OTC barcodes
- Drug Facts photos in a shared drive folder, not in the repo
- A short summary in the PR: total count, store-brand share, count per aisle and per store

### Before you start
- **OTC**: over-the-counter medicine, sold without a prescription. Only scan medicines with a Drug Facts panel, not supplements (which have a Supplement Facts panel) or cosmetics.
- **Barcode**: the 12-digit UPC-A (or 13-digit EAN-13) number under the bars on the box. For drugs it usually contains the NDC, FDA's product code. Any free barcode scanner app shows the digits; you can also type them.
- **NDC**: National Drug Code, often printed on the box as `NDC 12345-678-90`. Record it when you can see it; it lets us check our parser.
- **Drug Facts panel**: the standard label on every OTC box listing active ingredients, uses, warnings and directions. The photo lets us check ingredients later.
- **Store brand**: the retailer's own label, such as CVS Health, Walgreens, up&up (Target), Kroger or Publix brand products. The rest are national brands such as Tylenol.
- **Aisles** to cover: pain/fever, allergy, sleep, cough/cold, digestive, topical, eye/nasal, first aid.
- Spreadsheets drop leading zeros from numbers. Format the barcode column as text everywhere, or barcodes starting with `0` will be corrupted.
- Be respectful in stores: scan without blocking the aisle, don't photograph people, and stop if staff ask you to. Boxes in your own or your family's medicine cabinet also count.

### Steps
1. Create the form with fields: barcode digits (short text), product name as printed, brand type (`national` or `store`), store (CVS, Walgreens, Target, Kroger, Publix, or home), aisle (one of the eight above), NDC printed on the box (optional), photo of the Drug Facts panel (file upload to the shared drive), your name, date.
2. Create the assignment sheet: give each member one store and two aisles so every store and every aisle is covered by at least two people. Post it in the all-team channel with the form link and the Oct 25 deadline.
3. Post a two-minute guide: how to read barcode digits with a free app, how to spot a store brand, what not to scan (supplements, cosmetics, prescription items), and a target of 25 boxes each, with at least 8 store brands.
4. Check submissions every two days. Post progress per aisle and per store, and redirect people to aisles or stores with low counts.
5. After Oct 25, export the responses. Clean them: strip spaces and dashes from barcodes, remove exact duplicates (keep the first, note the duplicate count), remove non-OTC items, and fix obvious aisle or store typos.
6. Write `pipeline/tests/fixtures/barcodes.csv` with columns: `barcode`, `product_name`, `brand_type`, `store`, `aisle`, `ndc_on_box`, `photo_file`, `collected_by`, `collected_on`. Use first names or initials only in `collected_by`. Keep `barcode` as a string.
7. If NOMI-007 has merged, run each barcode through `ndc_candidates` and list the ones with `invalid_check_digit` or `bad_length`. Re-check those against the photos and fix typos. If NOMI-007 hasn't merged, compare a sample of 30 barcodes with their photos by hand.
8. Calculate and write in the PR: total unique barcodes, share of store brands, and counts per aisle and per store.
9. Open a PR adding only the CSV (no photos), and ask a Platform member (ideally the NOMI-025 owner) to review.

### Done when
- [ ] `pipeline/tests/fixtures/barcodes.csv` is merged with the columns in step 6
- [ ] At least 300 unique barcodes
- [ ] At least 30% of rows are store brands
- [ ] Every aisle (pain/fever, allergy, sleep, cough/cold, digestive, topical, eye/nasal, first aid) has at least one row
- [ ] No photos or full names are in the repo; photos are in the shared drive
- [ ] Counts per aisle, store and brand type are posted in the PR

### How to check your work
Open the CSV in DuckDB: `duckdb -c "SELECT aisle, brand_type, count(*) FROM read_csv('pipeline/tests/fixtures/barcodes.csv', all_varchar=true) GROUP BY ALL ORDER BY ALL"`. Every aisle should appear, store-brand rows should be at least 30% of the total, and `SELECT count(DISTINCT barcode)` should be at least 300. Spot-check five random rows against their Drug Facts photos.

### Out of scope
- Resolving barcodes to products and reporting coverage (NOMI-025)
- The barcode parser (NOMI-007)
- Fixing coverage misses (NOMI-037)
- Collecting the 50 new blind-test boxes (NOMI-066)

### Resources
- FDA NDC directory, to look up a printed NDC: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- DuckDB CSV import: https://duckdb.org/docs/data/csv/overview
- Glossary: `docs/nomi-101.md`

---

## NOMI-007: Build the barcode-to-NDC parser in Python and TypeScript
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint) | **Extra:** good first issue

### Summary
Write a small function, in both Python and TypeScript, that takes the digits from a scanned barcode and returns the possible NDC codes for that product. The pipeline uses the Python version and the phone app uses the TypeScript version.

### Why this matters
Every scan starts here. When the camera reads a barcode, we need to turn those digits into an NDC (FDA's product code) so we can look the product up. If this step is wrong, the app shows the wrong product or nothing at all, so it has to be correct and identical on both sides.

### What you will deliver
- `pipeline/src/nomi_pipeline/identity/barcode.py` with a function `ndc_candidates(barcode: str) -> BarcodeResult`
- `apps/mobile/src/lib/barcode.ts` with `ndcCandidates(barcode: string): BarcodeResult`
- `packages/schema/fixtures/barcodes.json` with at least 30 test cases
- Tests in both languages that read the same JSON file

### Before you start
- **NDC** (National Drug Code): FDA's ID for a drug package. On the box it's 10 digits in three segments, for example `50580-0449-02`. The segments can be split 4-4-2, 5-3-2 or 5-4-1, and the hyphens are not in the barcode.
- **NDC11**: the standard 11-digit version we store. You make it by adding a leading zero to whichever segment is short: 4-4-2 becomes 5-4-2 by padding the first segment, 5-3-2 pads the second, 5-4-1 pads the third.
- **UPC-A**: the 12-digit retail barcode. For drugs it's usually `3` + the 10-digit NDC + 1 check digit.
- **EAN-13**: a 13-digit barcode. A UPC-A code sometimes arrives as EAN-13 with an extra leading `0`.
- **Check digit**: the last digit, computed from the others, used to catch misreads. The UPC-A rule: sum the digits in odd positions times 3 plus the digits in even positions; the check digit makes the total a multiple of 10.
- Because the barcode has no hyphens, a 10-digit NDC could be any of the three splits. So we return all three NDC11 candidates and let the database lookup (NOMI-025, NOMI-040) find the one that exists.
- If NOMI-001 hasn't merged, put the files at the paths above anyway and run the tests directly with `pytest` and `npx tsx`.

### Steps
1. Write `packages/schema/fixtures/barcodes.json` first. Each case has `input`, `expected_status` (`ok`, `invalid_check_digit`, `no_ndc`, `bad_length`) and `expected_candidates`. Include real barcodes from boxes at home, at least 5 invalid check digits, EAN-13 inputs with a leading `0`, inputs with spaces or dashes, and non-drug barcodes that don't start with `3`.
2. Implement the Python function: strip non-digits; convert 13 digits starting with `0` to 12 digits; reject other lengths with `bad_length`; validate the check digit; if the first digit isn't `3` return `no_ndc`; otherwise take digits 2 to 11 as the NDC10 and build the three NDC11 candidates.
3. Return a result object with `status`, `ndc10` and `candidates` (list of three 11-digit strings, no hyphens).
4. Write `pipeline/tests/identity/test_barcode.py` that loads the JSON and checks every case.
5. Port the same logic to TypeScript with the same result shape, and write a test that loads the same JSON.
6. Add a short docstring in both files explaining the three NDC splits, with an example.

### Done when
- [ ] At least 30 cases in `barcodes.json`, including every status
- [ ] Python and TypeScript tests pass on the same fixture file
- [ ] Both functions return identical output for every case
- [ ] PR reviewed by one Platform and one Visualization member

### How to check your work
Run `uv run pytest pipeline/tests/identity` and the TypeScript test. Then scan three boxes from home with any barcode app, run the digits through your function, and confirm one of the candidates matches the NDC printed on the box.

### Out of scope
- Looking candidates up in FDA data (NOMI-025 in the pipeline, NOMI-040 in the app)
- Camera code (NOMI-011)

### Resources
- FDA NDC directory overview: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- GS1 check digit calculator: https://www.gs1.org/services/check-digit-calculator

---

## NOMI-008: Mirror raw data to Cloudflare R2 and build `uv run pipeline fetch`
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint), NOMI-006 (same sprint)

### Summary
Copy each raw data source (openFDA NDC directory, DailyMed OTC labels, FAERS quarterly files) once into a Cloudflare R2 bucket, then build the command `uv run pipeline fetch <source>` that downloads those files into `data/raw/` and verifies their checksums. Every pipeline developer uses this command to get data.

### Why this matters
FAERS and the DailyMed label archive are several GB each. Fifteen people downloading them from FDA and NLM servers is slow and gets rate limited, and the files can change underneath us. Mirroring each source once into R2 (free tier) gives everyone the same files, fast, and every later pipeline stage starts from `data/raw/`.

### What you will deliver
- An R2 bucket (for example `nomi-raw`) with one prefix per source: `ndc/`, `dailymed-otc/`, `faers/`
- Two R2 API tokens: read-only for the team, read-write stored only as GitHub Actions secrets
- `pipeline/src/nomi_pipeline/fetch/mirror.py`: copies files from the official source to R2 and writes the manifest (run by CI only)
- `.github/workflows/mirror.yml`: a manually triggered workflow that runs the mirror with the write token
- `pipeline/src/nomi_pipeline/fetch/fetch.py` and a `pipeline` command-line entry point with `pipeline fetch <source>` and `pipeline fetch all`
- A manifest per source in R2 (`<source>/manifest.json`) listing each file's name, size, SHA-256, original URL and download date
- `.env.example` listing the variables needed (no real values)
- A "Getting the data" section in `pipeline/README.md`

### Before you start
- **R2**: Cloudflare's file storage. It speaks the same API as Amazon S3, so you use `boto3` with an R2 endpoint like `https://<account_id>.r2.cloudflarestorage.com`. Check the current free-tier storage limit on Cloudflare's R2 pricing page and keep the mirror under it.
- **Mirror**: our own copy of public files, so the team downloads from us instead of the original site.
- **Checksum (SHA-256)**: a fingerprint of a file. If the downloaded file's SHA-256 matches the manifest, the file is complete and unchanged.
- **Manifest**: a JSON file describing every file in a source: name, size, checksum, where it came from and when.
- **openFDA NDC bulk JSON**: FDA's full NDC directory as one zipped JSON file. The list of all openFDA download files is at `https://api.fda.gov/download.json`.
- **DailyMed Human OTC SPL zips**: DailyMed's full release of every human OTC label in SPL (XML) format, split into several part files. File names are on DailyMed's "download all drug labels" page.
- **FAERS quarterly files**: FDA publishes adverse event reports as one zip per quarter (ASCII and XML versions). We mirror the ASCII files from 2014 Q1 to the latest quarter.
- **Credentials**: the team gets a read-only token in a local `.env` file (gitignored). Only CI holds write credentials, so nobody can accidentally overwrite the mirror.
- Read `docs/data-sources.md` (NOMI-006) first. Only mirror sources marked as allowed. If NOMI-006 hasn't merged, check with its owner that openFDA, DailyMed and FAERS are confirmed public domain before you publish anything.
- If NOMI-001 hasn't merged, create `pipeline/pyproject.toml` yourself with only what you need, and merge with NOMI-001's version when it lands.
- Creating the R2 bucket and tokens needs the cofounder who owns the Cloudflare account. Enabling R2 may ask for a payment method on the account; that is the cofounder's decision, not yours.

### Steps
1. Ask the cofounder who owns the Cloudflare account to create the bucket `nomi-raw` and two API tokens scoped to it: "Object Read" for the team and "Object Read & Write" for CI. Store the write token as GitHub Actions secrets (`R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`). Share the read-only token with the team through a private channel, never in the repo.
2. Add `.env.example` with `R2_ACCOUNT_ID=`, `R2_ACCESS_KEY_ID=`, `R2_SECRET_ACCESS_KEY=`, `R2_BUCKET=nomi-raw`. Confirm `.env` is in `.gitignore` (it already is).
3. Add dependencies `boto3`, `httpx` and `typer` (or `click`) to `pipeline/pyproject.toml`. Add a console script entry point `pipeline = "nomi_pipeline.cli:app"` and create `pipeline/src/nomi_pipeline/cli.py` with a `fetch` subcommand.
4. Write `mirror.py` with one function per source that lists the official files:
    - `ndc`: read `https://api.fda.gov/download.json` and take the NDC download file URLs.
    - `dailymed-otc`: the Human OTC full release part files from the DailyMed downloads page.
    - `faers`: the ASCII quarterly zips from 2014 Q1 to the latest available quarter, from the FAERS quarterly data page.
5. For each file, stream it to a temporary file, compute SHA-256 while streaming, upload it to `s3://nomi-raw/<source>/<filename>`, and add an entry to the manifest: `filename`, `size_bytes`, `sha256`, `source_url`, `downloaded_at`. Skip files whose name and size already match the existing manifest.
6. Write `<source>/manifest.json` to R2 with the entries plus `source`, `mirrored_at` and `total_size_bytes`.
7. Write `.github/workflows/mirror.yml` with `workflow_dispatch` (manual trigger) and a `source` input. It runs `uv run python -m nomi_pipeline.fetch.mirror <source>` using the write secrets. Run it once for each source. If total mirrored size approaches the R2 free-tier storage limit, stop and tell the cofounders before uploading more.
8. Write `fetch.py`: `pipeline fetch <source>` reads the read-only credentials from `.env`, downloads `<source>/manifest.json`, downloads every listed file to `data/raw/<source>/`, verifies each SHA-256, and saves the manifest next to the files. Skip files that already exist with the right checksum. On a checksum mismatch, delete the file and exit with an error that names it.
9. Add `pipeline fetch all`, which runs every source in turn. Add `--quarters 2024q1,2024q2` (or similar) for FAERS, so people who only need a few quarters don't download all of them.
10. Print progress (file name, size, done count) and a final summary: files downloaded, files skipped, total size, all checksums OK.
11. Write tests in `pipeline/tests/fetch/` that mock R2 (for example with `moto`, or a local folder) and check that a corrupted file is caught and that already-downloaded files are skipped.
12. Write "Getting the data" in `pipeline/README.md`: copy `.env.example` to `.env`, paste the read-only token, run `uv run pipeline fetch all`, and expected sizes and time.
13. Ask a teammate who has never run the pipeline to follow the README on a fresh clone and time it.

### Done when
- [ ] R2 bucket has `ndc/`, `dailymed-otc/` and `faers/` (2014 Q1 onward), each with a `manifest.json`
- [ ] Team token is read-only; write credentials exist only as GitHub Actions secrets
- [ ] `uv run pipeline fetch <source>` and `uv run pipeline fetch all` download into `data/raw/` and verify every checksum
- [ ] A corrupted or partial file is detected and reported (covered by a test)
- [ ] No data files or credentials are committed; `data/` stays gitignored
- [ ] A new member got all raw data with one command, following only `pipeline/README.md`
- [ ] PR reviewed by one Platform member

### How to check your work
On a fresh clone, run `uv run pipeline fetch ndc`, then change one byte of the downloaded file and run it again: it should detect the mismatch and download the file again (or exit with a clear error). Run `uv run pipeline fetch all` and check that `data/raw/` contains `ndc/`, `dailymed-otc/` and `faers/` with a manifest in each. Try uploading a file with the read-only token using `boto3`; it should be refused.

### Out of scope
- RxNorm files and the UMLS license (NOMI-019)
- Parsing any of the files (NOMI-009, NOMI-010, NOMI-024)
- The full `pipeline run` command chaining all stages (NOMI-043)
- Publishing the built `nomi.sqlite` dataset to R2 (NOMI-038)

### Resources
- Cloudflare R2 docs: https://developers.cloudflare.com/r2/
- R2 pricing and free tier: https://developers.cloudflare.com/r2/pricing/
- openFDA downloads: https://open.fda.gov/data/downloads/
- DailyMed full label downloads: https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm
- FAERS quarterly data files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- uv project scripts: https://docs.astral.sh/uv/concepts/projects/config/
- Data folder guide: `data/README.md`; license rules: `docs/data-sources.md`

---

## NOMI-009: Ingest the openFDA NDC directory into `data/bronze/ndc.parquet`
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-008 (same sprint)

### Summary
Build `uv run pipeline ingest ndc`, which reads the raw openFDA NDC directory file, keeps only human OTC drugs, normalizes package NDCs to 11 digits, and writes one typed table to `data/bronze/ndc.parquet`, plus a DuckDB view for exploring it.

### Why this matters
The NDC directory is FDA's list of every marketed drug product and package. It is the first lookup in the barcode chain: a scanned barcode gives NDC candidates (NOMI-007), and this table tells us which candidate is a real OTC package, who makes it, how it's marketed, and which DailyMed label it belongs to. Identity resolution (NOMI-025) and categories (NOMI-026) are built on it.

### What you will deliver
- `pipeline/src/nomi_pipeline/ingest/ndc.py`
- An `ingest ndc` subcommand on the `pipeline` command line
- `data/bronze/ndc.parquet` (generated, not committed), one row per package NDC
- A DuckDB view `ndc` over the Parquet file, created by the command
- Logged row counts and null rates per column, also saved to `data/bronze/ndc.stats.json`
- Tests in `pipeline/tests/ingest/test_ndc.py` with a small fixture file

### Before you start
- **NDC**: National Drug Code. A **product NDC** identifies a product (labeler and product, e.g. `50580-449`); a **package NDC** adds the package segment (e.g. `50580-449-02`). Barcodes carry the package NDC.
- **NDC11**: our standard 11-digit form with no hyphens. In the NDC directory, NDCs have hyphens, so the split is known: pad the short segment with a leading zero to make 5-4-2. Examples: `1234-5678-90` (4-4-2) becomes `01234567890`; `12345-678-90` (5-3-2) becomes `12345067890`; `12345-6789-0` (5-4-1) becomes `12345678900`.
- **openFDA NDC file**: one zipped JSON file with a `results` array. Each result is a product with fields such as `product_ndc`, `product_type`, `brand_name`, `generic_name`, `labeler_name`, `dosage_form`, `route`, `marketing_category`, `active_ingredients` (list of `name` and `strength`), `packaging` (list including `package_ndc` and `description`) and an `openfda` block with `rxcui`, `spl_set_id` and other links. Confirm exact field names and nesting in the openFDA NDC documentation.
- **`product_type`**: we keep only `HUMAN OTC DRUG`.
- **Marketing category**: how the product is legally sold, e.g. OTC monograph, NDA, unapproved homeopathic. **RxCUI**: the product's ID in RxNorm, NLM's drug vocabulary. **SPL set id**: the stable ID of the product's DailyMed label, which links this table to NOMI-010.
- **Bronze**: the first data layer: raw data turned into typed tables, minimally changed. **Parquet**: the table file format we use. **Polars**: the Python dataframe library. **DuckDB**: runs SQL over Parquet files. See `docs/nomi-101.md`.
- Input: `data/raw/ndc/` from `uv run pipeline fetch ndc` (NOMI-008). If NOMI-008 hasn't merged, download the NDC JSON zip yourself from the openFDA downloads page into `data/raw/ndc/` and keep going.
- If the `pipeline` command doesn't exist yet (NOMI-008), add the `ingest ndc` subcommand in `pipeline/src/nomi_pipeline/cli.py` yourself and coordinate with the NOMI-008 owner.

### Steps
1. Create a test fixture `pipeline/tests/fixtures/ndc_sample.json` with about 10 products copied from the real file: a few `HUMAN OTC DRUG` products with 4-4-2, 5-3-2 and 5-4-1 NDCs, one `HUMAN PRESCRIPTION DRUG`, one product with no `openfda` block, and one with several packages.
2. Write `ingest/ndc.py`: unzip and load the JSON from `data/raw/ndc/`, keep only results where `product_type == "HUMAN OTC DRUG"`.
3. Explode `packaging` so there is one row per package. Keep these columns: `package_ndc` (original, with hyphens), `package_ndc11`, `product_ndc`, `package_description`, `labeler_name`, `brand_name`, `generic_name`, `dosage_form`, `route` (list), `marketing_category`, `active_ingredients` (list of structs with `name` and `strength`), `rxcui` (list, from `openfda.rxcui`), `spl_set_id` (from the `openfda` block).
4. Write `to_ndc11(ndc: str) -> str` that pads using the hyphen segments, and raise or log any NDC that doesn't have three segments in one of the three allowed splits. Unit-test it with the three examples above.
5. Set explicit Polars types for every column (strings, lists of strings, list of structs). Missing `openfda` blocks become nulls, not errors.
6. Sort rows by `package_ndc11` and write `data/bronze/ndc.parquet`. Sorting and fixed types make the output reproducible: the same input always gives the same file.
7. Log total products read, OTC products kept, package rows written, number of duplicate `package_ndc11` values, and the null rate of every column. Save the same numbers to `data/bronze/ndc.stats.json`.
8. Create a DuckDB database at `data/nomi.duckdb` with `CREATE OR REPLACE VIEW ndc AS SELECT * FROM 'data/bronze/ndc.parquet'`. Add a short "Exploring the data" note with this example to `pipeline/README.md`.
9. Add the `ingest ndc` subcommand so `uv run pipeline ingest ndc` runs steps 2-8.
10. Write `pipeline/tests/ingest/test_ndc.py` that runs the ingest on the fixture and checks: only OTC rows kept, one row per package, NDC11 values correct, and missing `openfda` handled.
11. Run it on the full file and paste the logged counts and null rates into the PR.

### Done when
- [ ] `uv run pipeline ingest ndc` writes `data/bronze/ndc.parquet` from `data/raw/ndc/`
- [ ] Only `HUMAN OTC DRUG` products are kept
- [ ] Every row has an 11-digit `package_ndc11`; malformed NDCs are logged
- [ ] Labeler, brand and generic names, dosage form, route, marketing category, active ingredients, `rxcui` and `spl_set_id` columns are present
- [ ] Running it twice on the same input produces byte-identical Parquet files (or identical row content, checked by a test)
- [ ] Row counts and null rates are logged and saved to `data/bronze/ndc.stats.json`
- [ ] The DuckDB `ndc` view works
- [ ] Tests pass with `uv run pytest pipeline/tests/ingest`
- [ ] PR reviewed by one Platform member

### How to check your work
Run `duckdb data/nomi.duckdb -c "SELECT marketing_category, count(*) FROM ndc GROUP BY 1 ORDER BY 2 DESC"` and check the categories look sensible (OTC monograph categories should dominate). Take three boxes from home, read the NDC printed on each, convert it to NDC11 by hand, and query `SELECT brand_name, labeler_name FROM ndc WHERE package_ndc11 = '...'`. Each should return the right product.

### Out of scope
- DailyMed label parsing (NOMI-010)
- Resolving barcodes to products (NOMI-025)
- Assigning OTC categories and scope flags (NOMI-026)
- Linking RxCUIs to UNIIs (NOMI-019)

### Resources
- openFDA NDC API and fields: https://open.fda.gov/apis/drug/ndc/
- openFDA downloads: https://open.fda.gov/data/downloads/
- FDA NDC directory overview: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- Polars: https://docs.pola.rs/
- DuckDB Parquet: https://duckdb.org/docs/data/parquet/overview
- Pipeline stages: `pipeline/README.md`

---

## NOMI-010: Parse DailyMed OTC labels into product and ingredient tables
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-008 (same sprint)

### Summary
Build `uv run pipeline ingest spl`, which parses every DailyMed human OTC label (SPL XML) and writes two tables: `data/bronze/spl_products.parquet` (labels, products and package NDCs) and `data/bronze/spl_ingredients.parquet` (active ingredients with strengths, and inactive ingredients), keeping only the latest version of each label.

### Why this matters
DailyMed has the full FDA label for every OTC product, including exact ingredient strengths and inactive ingredients that the NDC directory doesn't give reliably. These tables tell us that a box contains, for example, acetaminophen 500 mg per tablet, which the knowledge base and scoring need. This ticket extracts the structured product data; the Drug Facts text sections come in NOMI-023.

### What you will deliver
- `pipeline/src/nomi_pipeline/ingest/spl.py`
- An `ingest spl` subcommand on the `pipeline` command line
- `data/bronze/spl_products.parquet` (generated, not committed)
- `data/bronze/spl_ingredients.parquet` (generated, not committed)
- `data/bronze/spl_parse_failures.parquet` listing each failed label's set id and error
- 3-5 small SPL XML fixtures in `pipeline/tests/fixtures/spl/` and tests in `pipeline/tests/ingest/test_spl.py`
- Parse success rate and counts posted in the PR

### Before you start
- **SPL** (Structured Product Labeling): the XML format of every FDA label on DailyMed. Each label has a **set id** (stable across versions) and a **version number**. The XML uses the HL7 namespace `urn:hl7-org:v3`.
- **DailyMed full release**: zip files containing one inner zip per label; each inner zip holds the label XML plus images. You only need the XML.
- **Where things are in the XML** (confirm against real files and the FDA SPL documentation):
    - Set id: `document/setId/@root`; version: `document/versionNumber/@value`; effective date: `document/effectiveTime/@value`.
    - Products: `manufacturedProduct` elements inside the label's sections. Each has a `code` (the product NDC), a `name`, a `formCode` (dosage form) and the generic name.
    - Ingredients: `ingredient` elements with a `classCode`. Active ingredients use codes such as `ACTIB` or `ACTIM`; inactive ingredients use `IACT`. The ingredient's UNII is in `ingredientSubstance/code/@code`.
    - Strength: `ingredient/quantity` with a `numerator` (value and unit, e.g. 500 mg) and a `denominator` (e.g. 1 tablet, or 15 mL).
    - Package NDCs: nested `asContent/containerPackagedProduct/code` elements under the product.
    - Marketing category: an `approval` element under the product's `subjectOf`, whose `code/@displayName` is e.g. "OTC monograph drug" or "NDA".
- **UNII**: FDA's unique ingredient ID, our main ingredient key. **Marketing category**: see `docs/nomi-101.md`.
- **Kit**: a product made of several parts (e.g. a first aid kit), with ingredients listed per part. Handle these if you can; otherwise log them as unsupported and count them.
- Input: `data/raw/dailymed-otc/` from `uv run pipeline fetch dailymed-otc` (NOMI-008). If NOMI-008 hasn't merged, download one Human OTC part file from DailyMed's downloads page, or download single labels for the five reference products (Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil, a store-brand diphenhydramine) from DailyMed and work from those.
- Use `lxml` for parsing. Process inner zips in parallel (e.g. `concurrent.futures.ProcessPoolExecutor`) so the full run takes minutes, not hours.

### Steps
1. Download the SPL XML for 3-5 labels from DailyMed (include a single-ingredient tablet, a liquid with strength per mL, a combination product such as a NyQuil variant, and a kit if you can find one). Save them in `pipeline/tests/fixtures/spl/` without images.
2. Open one fixture and find each element listed in "Before you start" by hand. Write the XPaths you use in a docstring at the top of `spl.py`.
3. Write `parse_label(xml_bytes) -> ParsedLabel` that returns: set id, version, effective date, document title, and a list of products. Each product has its product NDC, name, generic name, dosage form, marketing category, list of package NDCs with descriptions, and list of ingredients.
4. For each ingredient, return: UNII, name, role (`active` or `inactive`) and the raw `classCode`, numerator value and unit, denominator value and unit. Inactive ingredients usually have no strength; leave those fields null.
5. Write `ingest_spl()` that walks every outer zip in `data/raw/dailymed-otc/`, opens each inner zip, finds the `.xml` file, and calls `parse_label`. Catch any exception per label, record the set id (if readable), the inner zip name and the error message, and keep going.
6. Keep only the latest version of each label: if the same set id appears more than once, keep the row with the highest version number.
7. Write `data/bronze/spl_products.parquet` with one row per package NDC: `set_id`, `version`, `effective_date`, `product_ndc`, `package_ndc`, `package_ndc11` (padded the same way as NOMI-009), `package_description`, `product_name`, `generic_name`, `dosage_form`, `marketing_category`.
8. Write `data/bronze/spl_ingredients.parquet` with one row per ingredient per product: `set_id`, `version`, `product_ndc`, `part_index` (null unless a kit part), `unii`, `ingredient_name`, `role`, `class_code`, `strength_value`, `strength_unit`, `per_value`, `per_unit`.
9. Write `data/bronze/spl_parse_failures.parquet` with `set_id`, `inner_zip`, `error`. Log the totals: labels seen, parsed, failed, duplicates dropped, kits seen, and the success rate.
10. Add the `ingest spl` subcommand so `uv run pipeline ingest spl` runs everything.
11. Write `pipeline/tests/ingest/test_spl.py` checking each fixture: correct set id and version, correct package NDCs, correct active ingredient UNIIs and strengths (compare against the label on DailyMed), and inactive ingredients present.
12. Run on the full OTC release. If the success rate is below 98%, group the failures by error message, fix the top causes, and rerun.
13. Paste the counts, success rate and top three remaining failure causes into the PR.

### Done when
- [ ] `uv run pipeline ingest spl` writes `spl_products.parquet`, `spl_ingredients.parquet` and `spl_parse_failures.parquet` to `data/bronze/`
- [ ] Set id, version, marketing category, products and package NDCs are parsed
- [ ] Active ingredients have UNII, strength and unit; inactive ingredients have UNII
- [ ] Only the latest version of each label is kept
- [ ] Every parse failure is logged with its set id
- [ ] At least 98% of OTC labels parse without error (number in the PR)
- [ ] Fixture tests pass with `uv run pytest pipeline/tests/ingest`
- [ ] PR reviewed by one Platform member

### How to check your work
Look up Tylenol Extra Strength on DailyMed and note its set id. Run `duckdb -c "SELECT ingredient_name, role, strength_value, strength_unit, per_value, per_unit FROM 'data/bronze/spl_ingredients.parquet' WHERE set_id = '<set id>'"`. You should see acetaminophen as active at the strength printed on the label, plus its inactive ingredients. Then check that a few package NDCs from NOMI-009's `ndc.parquet` with the same `spl_set_id` also appear in `spl_products.parquet`.

### Out of scope
- Splitting the Drug Facts text sections such as Warnings and Directions (NOMI-023)
- Joining labels to the NDC directory and to barcodes (NOMI-025)
- OTC categories and homeopathic or out-of-scope flags (NOMI-026)
- Extracting warnings, age limits or doses from label text (NOMI-031, NOMI-032)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- DailyMed full label downloads: https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm
- lxml: https://lxml.de/
- Polars: https://docs.pola.rs/
- Pipeline stages: `pipeline/README.md`; glossary: `docs/nomi-101.md`

---

## NOMI-011: Scaffold the Expo app with live barcode scanning on real phones
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

### Summary
Create the Nomi phone app in `apps/mobile` as an Expo development build that opens straight to the camera, reads UPC-A and EAN-13 barcodes on the device, buzzes on a successful read, and shows the raw barcode digits on a placeholder screen. Install it on at least one iPhone and one Android phone.

### Why this matters
The product promise is "scan in the aisle, answer instantly." Every later app ticket (result screen, scan states, database lookup, scoring) builds on this app and this camera screen. Barcode reading must happen on the phone, not on a server, so it works with no signal in a store and keeps the app offline-first.

### What you will deliver
- An Expo app in `apps/mobile` using TypeScript and expo-router, with screens in `apps/mobile/src/app/`
- `apps/mobile/src/app/index.tsx`: the camera screen (the app's first screen, no home screen)
- `apps/mobile/src/app/scanned.tsx`: a placeholder screen that shows the barcode type and digits
- `apps/mobile/eas.json` with a `development` build profile
- A "Running the app" section in `apps/mobile/README.md` with exact build and install commands for iOS and Android
- The dev build installed on at least one iPhone and one Android phone, with scan timings posted in the PR

### Before you start
- Read `docs/nomi-101.md`, especially "Two rules that shape everything".
- **Expo**: the React Native framework we use. **expo-router**: file-based navigation; each file in `src/app/` is a screen.
- **Dev build (development build)**: a custom build of the app installed on your phone. We need it because `react-native-vision-camera` contains native code that does not run inside the Expo Go app.
- **EAS**: Expo's cloud build service. The free plan has a limited number of builds per month, so build locally when you can.
- **UPC-A / EAN-13**: the two retail barcode formats on drug boxes. UPC-A is 12 digits; EAN-13 is 13 digits. On iOS, a UPC-A barcode may be reported as `ean-13` with an extra leading `0`. Do not fix that here; the parser in NOMI-007 normalizes it.
- **Haptic feedback**: a short vibration that tells the user the scan worked.
- iOS on-device builds: without a paid Apple Developer account you can still install on your own iPhone with Xcode and a free Apple ID (`npx expo run:ios --device`). The app stops opening after about 7 days and must be reinstalled. Who owns the paid developer accounts is decided in NOMI-021.
- If NOMI-001 (monorepo tooling) hasn't merged, create the app in `apps/mobile` anyway and run it with `npx` from that folder. Fix workspace wiring when NOMI-001 lands.

### Steps
1. Create the app: from the repo root run `npx create-expo-app@latest apps/mobile`. Keep TypeScript and expo-router. Run the template's reset script (`npm run reset-project` or the pnpm equivalent) to remove the example screens.
2. Move the router folder so screens live in `apps/mobile/src/app/` (expo-router supports a `src/app` folder). Keep `apps/mobile/README.md` as is and add to it.
3. If you use pnpm and Metro can't resolve packages, follow the Expo monorepo guide (linked below), for example set `node-linker=hoisted` in the root `.npmrc`. Note what you changed in the PR.
4. Install native dependencies: `npx expo install react-native-vision-camera expo-dev-client expo-haptics`.
5. Add the vision-camera config plugin to `app.json` under `plugins`, with a camera permission message such as `"Nomi uses the camera to read the barcode on medicine boxes. Images never leave your phone."`
6. Use Continuous Native Generation: do not commit the generated `ios/` and `android/` folders. Add them to `apps/mobile/.gitignore`.
7. Build `src/app/index.tsx`: request permission with `useCameraPermission()`, pick the back camera with `useCameraDevice('back')`, and render a full-screen `<Camera>` with `isActive` true while the screen is focused. Show a plain message and a "Open settings" button if permission is denied.
8. Add the code scanner: `useCodeScanner({ codeTypes: ['upc-a', 'ean-13'], onCodeScanned })` and pass it to the `<Camera codeScanner={...}>` prop.
9. In `onCodeScanned`, take the first code, ignore any further callbacks until the user comes back to the camera (the callback fires many times per second), call `Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)`, and navigate with `router.push({ pathname: '/scanned', params: { type: code.type, value: code.value } })`.
10. Build `src/app/scanned.tsx`: show the type (`upc-a` or `ean-13`) and the digits in large text, plus a "Scan again" button that goes back to the camera and re-enables scanning.
11. Add `eas.json` with a `development` profile (`developmentClient: true`, `distribution: "internal"`, Android `buildType: "apk"`).
12. Build and install on Android: `npx expo run:android --device` with the phone connected by USB, or `eas build --profile development --platform android` and install the APK.
13. Build and install on iOS: `npx expo run:ios --device` from a Mac with Xcode and the iPhone connected. Use EAS for iOS only if someone has a paid Apple Developer account.
14. Time scans on each phone (see "How to check your work") and post the numbers in the PR.
15. Write the "Running the app" section in `apps/mobile/README.md`: prerequisites (Node, Xcode or Android Studio), the commands from steps 12 and 13, and the 7-day note for free Apple IDs. Also note whether iOS reported UPC-A boxes as `ean-13`.

### Done when
- [ ] `apps/mobile` is a TypeScript Expo app using expo-router with screens in `src/app/`
- [ ] The app opens directly to the camera; there is no home screen
- [ ] UPC-A and EAN-13 barcodes are read on the device with no network request
- [ ] A successful scan triggers a haptic and shows the barcode type and digits on the placeholder screen
- [ ] "Scan again" returns to the camera and scanning works again
- [ ] The dev build is installed on at least one iPhone and one Android phone
- [ ] On both phones, a real OTC box scans within about 300 ms of framing: median of 10 timed scans is 300 ms or less, with all 20 timings in the PR
- [ ] `ios/` and `android/` are not committed; README has working build instructions
- [ ] PR reviewed by one other Visualization member, who installed the app from the README instructions

### How to check your work
Put each phone in airplane mode and scan five different OTC boxes from home; each should buzz and show digits that match the numbers under the barcode. To time scans, record the screen at 60 fps (or film the phone with a second phone's slow-motion camera), hold the box out of frame, then move it into frame. Count frames from the box being steady in frame to the placeholder screen appearing; at 60 fps each frame is about 16.7 ms. Do 10 scans per phone and report the median.

### Out of scope
- Turning barcode digits into NDC candidates (NOMI-007)
- Looking the product up in the on-device database (NOMI-040)
- Real result screen and navigation to every scan state (NOMI-029, NOMI-030)
- Theme and shared components (NOMI-027)
- Performance tuning beyond the 300 ms target (NOMI-069)

### Resources
- Expo development builds: https://docs.expo.dev/develop/development-builds/introduction/
- expo-router: https://docs.expo.dev/router/introduction/
- Expo monorepos: https://docs.expo.dev/guides/monorepos/
- Vision Camera code scanning: https://react-native-vision-camera.com/docs/guides/code-scanning
- expo-haptics: https://docs.expo.dev/versions/latest/sdk/haptics/
- App layout plan: `apps/mobile/README.md`

---

## NOMI-012: Create the Figma design tokens and component library
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Build and publish a Figma library with Nomi's color, type and spacing tokens for light and dark mode, plus the core components the app screens are made from. The score colors must stay distinguishable for color-blind users and pass WCAG AA contrast.

### Why this matters
Every app screen in later sprints is built from these pieces, and NOMI-027 turns this library into code. Scores are shown in colors, and about 1 in 12 men has some form of color blindness, so the score must never rely on color alone. Getting this right once in the library means every screen gets it right.

### What you will deliver
- A published Figma library named "Nomi Library" with pages: Tokens, Components, Accessibility checks
- Color tokens for light and dark mode, including score tier colors
- A type scale and spacing scale
- Components: score badge, tier label, dimension bar, citation chip, profile chip, warning banner, buttons, cards
- A contrast table on the Accessibility checks page showing the ratio for every score state in both modes
- The library link added to the GitHub issue and to `apps/mobile/README.md` under a "Design" heading

### Before you start
- Read `docs/nomi-101.md` for the big picture.
- **Design token**: a named value (for example `color.tier.good.bg`) used instead of a raw hex code, so design and code use the same names.
- **Score tier**: the band a 0-100 score falls in, shown with a word and a color. The final bands and words come in the rubric (NOMI-049). For now assume four tiers, for example 75-100, 50-74, 25-49, 0-24, plus two special states: "hard stop" (red no matter what, because the label says do not use for this person) and "not scored" (for example homeopathic products).
- **Risk dimension**: one kind of risk, such as liver or stomach bleeding. The dimension bar shows how many points one dimension took off. See the glossary.
- **Citation chip**: a small tappable tag naming the source of a fact, such as "FDA label: Warnings".
- **WCAG AA contrast**: text needs a contrast ratio of at least 4.5:1 against its background (3:1 for large text); icons, borders and other non-text UI parts need at least 3:1.
- **Color-blind safe**: tiers must differ by more than hue. Use a tier word, an icon or shape per tier, and clearly different lightness.
- Figma: shared libraries need a Figma plan that supports publishing. Use the free Figma for Education plan (verify with a student email). If it isn't approved yet, build everything in one shared file and publish when it is.

### Steps
1. Create a Figma team file "Nomi Library" with three pages: Tokens, Components, Accessibility checks.
2. Define color tokens as Figma variables with two modes, Light and Dark: background, surface, text primary, text secondary, border, accent, and for each tier (`tier.1` to `tier.4`, `tier.hardstop`, `tier.notscored`) a background, foreground and icon color.
3. Pick a distinct icon or shape for each tier (for example check, dash, triangle, octagon) and a placeholder tier word. Mark the words as placeholders until NOMI-049.
4. Define a type scale (for example 12, 14, 16, 20, 24, 32, 48 for the score number) with line heights, using a free font with good legibility (for example Inter or the platform system font). Note that sizes must also work when the user increases text size.
5. Define a spacing scale (for example 4, 8, 12, 16, 24, 32) and corner radii.
6. Build each component with variants: score badge (each tier, light and dark, small and large), tier label, dimension bar (0 to max points, with a text value), citation chip, profile chip (me, child, older adult), warning banner (info, caution, hard stop), buttons (primary, secondary, text; default, pressed, disabled), cards.
7. Make sure every component that shows a score or tier also shows the tier word or icon, not only color.
8. Check contrast for every score state in both modes with a contrast checker (link below). Record foreground, background and ratio in a table on the Accessibility checks page. Fix any pair under the WCAG AA thresholds.
9. Export a screenshot of the score badges and view it through a color-blindness simulator (for example Chrome DevTools: Rendering, then Emulate vision deficiencies) for protanopia, deuteranopia, tritanopia and achromatopsia. Paste the results on the Accessibility checks page.
10. Publish the library. Add the link to the GitHub issue and to `apps/mobile/README.md` under "Design".
11. Hold a 30-minute review with the Visualization team; log requested changes in the issue and make them.

### Done when
- [ ] Library is published (or shared, if the education plan is still pending) and linked from the issue and `apps/mobile/README.md`
- [ ] Light and dark color tokens exist, including all tier and special-state colors
- [ ] Type scale and spacing scale exist as named styles or variables
- [ ] All 8 component types exist with the variants listed in step 6
- [ ] Every score state passes WCAG AA contrast in both modes, recorded in the contrast table
- [ ] Every tier is distinguishable in all four simulated color-vision views, shown on the Accessibility checks page
- [ ] Library reviewed by the Visualization team, with feedback logged in the issue

### How to check your work
Switch the whole Components page to grayscale (or the achromatopsia simulation). You should still be able to tell every tier apart by its word or icon. Ask someone who hasn't seen the library to name the tier of five random badges in grayscale; they should get all five.

### Out of scope
- Coding the components in the app (NOMI-027)
- Choosing the final score and breakdown visual (NOMI-014)
- Final tier bands and tier words (NOMI-049)
- Full screen layouts (NOMI-013)

### Resources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
- WCAG non-text contrast: https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html
- WebAIM contrast checker: https://webaim.org/resources/contrastchecker/
- Figma for Education: https://www.figma.com/education/
- Glossary: `docs/nomi-101.md`

---

## NOMI-013: Build a clickable Figma prototype of every demo flow
**Team:** visualization | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-004 (same sprint)

### Summary
Make a clickable Figma prototype of every screen and state the Nov 20 demo needs: scanner, result screen, alternative comparison, onboarding and profiles, and the special states. Annotate each screen with the data fields it shows, then walk three people outside the team through it.

### Why this matters
Every screen the demo needs should exist as a prototype before anyone codes it. The prototype settles layout early, and the field annotations tell Data Analysis and Platform exactly which data each screen consumes, so they produce the right fields. It is also the reference for NOMI-028, NOMI-029, NOMI-030, NOMI-041 and NOMI-062.

### What you will deliver
- A Figma file "Nomi Demo Prototype" with a clickable flow that starts at the scanner
- Screens: scanner; result screen; alternative and tradeoff comparison; onboarding and profiles
- States: preliminary score, homeopathic, not found, hard stop
- A field annotation on each screen naming the data fields it uses
- Walkthrough feedback from 3 people outside the team, logged in the GitHub issue
- The prototype link in the issue

### Before you start
- Read `docs/nomi-101.md` and the demo script `docs/demo/script.md` (NOMI-004). If the script hasn't merged, use the NOMI-004 task list in `planning/backlog.md`: blind scan in airplane mode, Benadryl for a 30-year-old vs a 75-year-old, Tylenol vs Aleve for a 70-year-old with high blood pressure, NyQuil duplicate-acetaminophen warning, homeopathic and not-found states.
- **Persona / profile**: who the medicine is for. Persona is the type (adult 18-64, 65+, teen, child, pregnant and so on); profile adds optional conditions and medication types. See the glossary.
- **Risk dimension breakdown**: the list of risks that took points off the score, each with its points and sources.
- **Benchmark**: a rank within products with the same use, for example "Better than 82% of pain relievers for you."
- **Preliminary score**: a score based only on ingredients and label warnings, before full review.
- **Homeopathic**: products FDA has not evaluated for safety or effectiveness. We show "Not evaluated by FDA for safety or effectiveness" and no score.
- **Hard stop**: the product is red no matter what, because the label says do not use for this person (for example a child under the label's age limit).
- **Data contracts**: the field names come from the schemas in `packages/schema/schemas/` (NOMI-002). If they haven't merged, use the field lists in the NOMI-002 ticket in `planning/backlog.md` (`product`, `score-record`).
- Use components from the NOMI-012 library if ready; otherwise use grayscale boxes. Use the reference products in `packages/schema/examples/` (NOMI-015) for content, or realistic placeholder text marked "example".

### Steps
1. List every screen and state the demo script touches, in order, as a checklist in the issue.
2. Draw the scanner: full-screen camera, a framing guide, a "Search by name" link for later, and the active profile chip.
3. Draw the result screen with: product name and image area, score with tier word, who the score is for (profile chip), dimension breakdown, benchmark line, explanation sentences with citation chips, "safer option" card, and the disclaimer "Nomi provides information from public FDA data and published criteria. It is not medical advice."
4. Draw the alternative and tradeoff comparison: two products side by side, both scores, which dimensions are better or worse, the shared use, a one-line reason, and an "Ask your pharmacist" state for when no option is clearly better.
5. Draw onboarding and profiles: "Who are you scanning for?" (me, a child, an older adult), age band, optional conditions (for example high blood pressure, kidney disease), optional current medication types (for example blood thinners), a skip option that defaults to adult, and a profile switcher.
6. Draw the four states: preliminary score (with a "preliminary" badge), homeopathic (no score, the FDA message), not found (barcode shown, search and manual entry options), hard stop (warning banner quoting the label line).
7. Draw the NyQuil duplicate-acetaminophen warning as it appears on the result screen.
8. Wire the prototype so a viewer can click through the full demo script from the scanner, including the Benadryl profile switch and the Tylenol vs Aleve comparison.
9. Add a field annotation next to each screen listing every data field shown, using contract names, for example `product.brand_name`, `score_record.score`, `score_record.contributions[].dimension`, `score_record.benchmark_percentile`, `score_record.alternatives[]`. Mark any field that doesn't exist in the contracts yet and tell the NOMI-002 owner.
10. Run 3 walkthroughs with people outside the team. Give each the demo task ("You're buying a pain reliever for your 70-year-old dad who has high blood pressure"), let them click without help, and note where they hesitate or misread.
11. Log feedback from all three in the issue, grouped by screen. Fix the problems you agree with and note which you didn't fix and why.

### Done when
- [ ] Every screen and state in step 1's checklist exists and is reachable by clicking from the scanner
- [ ] Result screen shows score, who it's for, dimension breakdown, benchmark, explanation and disclaimer
- [ ] Comparison, onboarding and profiles, and all four states (preliminary, homeopathic, not found, hard stop) are drawn
- [ ] Every screen has a field annotation; missing contract fields were reported to the NOMI-002 owner
- [ ] Walked through with 3 people outside the team; feedback logged in the issue
- [ ] Prototype link posted in the issue

### How to check your work
Open the prototype in presentation mode and read the demo script aloud. Every line of the script should match a click in the prototype with nothing missing. Then give the field annotations to a Data Analysis member and ask whether they could produce each field; anything they can't is a contract gap to raise.

### Out of scope
- Final score and breakdown visual style (NOMI-014)
- Coding any screen (NOMI-028, NOMI-029, NOMI-030, NOMI-041, NOMI-062, NOMI-063)
- Explanation wording (NOMI-048)
- The demo script itself (NOMI-004)

### Resources
- Demo script: `docs/demo/script.md`
- Data contract field lists: NOMI-002 in `planning/backlog.md`
- Glossary: `docs/nomi-101.md`

---

## NOMI-014: Test three score visualization concepts and record the choice
**Team:** visualization | **Priority:** P1 | **Sprint:** S1 | **Depends on:** none

### Summary
Design three ways to show the score and three ways to show the risk-dimension breakdown, test them with 5 people, and write down which one we use and why. The chosen design goes into the NOMI-012 Figma library.

### Why this matters
Users need to see at a glance how risky a product is for them and why. How we draw the score and its risk dimensions is the core of Nomi's design, and changing it after screens are coded is expensive. A small test now tells us which design people actually understand.

### What you will deliver
- A Figma page "Score concepts" with three score concepts and three breakdown concepts, all showing the same example data
- Test notes for 5 participants in the GitHub issue (no names, no personal health details)
- A decision write-up in `docs/design/score-visualization.md`
- The chosen score and breakdown components added to the NOMI-012 library

### Before you start
- Read `docs/nomi-101.md`.
- **Score**: 0 to 100, personalized to a profile. **Tier**: the band it falls in, with a word and color. Final bands come in NOMI-049; use placeholders.
- **Risk dimension breakdown**: the risks that took points off, such as stomach bleeding, blood pressure or kidney, each with its points and a source.
- The three score concepts to test: a dial (gauge), a horizontal bar, and a number with a tier word.
- Breakdown concepts to test, for example: stacked bar of points lost, a ranked list with small bars, and a list of icons with severity words. You can swap one if you have a better idea.
- Rules from NOMI-012: never rely on color alone; every tier has a word or icon.
- Example data: use Tylenol Extra Strength vs Aleve for a 70-year-old with high blood pressure. Aleve should lose points on stomach bleeding, blood pressure and kidney; Tylenol mainly on liver at high doses. Use made-up scores clearly marked "example" until real ones exist (NOMI-015).
- Privacy: do not ask participants about their own health conditions or record names. Record only age range and whether they buy medicine for someone else.

### Steps
1. Build the three score concepts with the same example data, for both products, in the same frame size as a phone result screen.
2. Build the three breakdown concepts with the same example data.
3. Pair them into three full result-screen mockups (each mockup uses one score and one breakdown concept) so participants see them in context.
4. Write a test script: (a) "Who is this score for?" (b) "Why did this product score low?" (c) "Which of these two would you pick for a 70-year-old with high blood pressure, and why?" (d) "Which version was easiest to understand?"
5. Recruit 5 people outside the Visualization team, ideally including someone 60 or older and someone who buys medicine for a parent or child.
6. Run each session for about 15 minutes. Show the mockups in a different order for each person so order doesn't bias the result. Record for each mockup whether they answered (a) and (b) correctly.
7. Post anonymized notes for all 5 in the issue: answers per question per mockup, quotes, and confusion points.
8. Count correct answers per concept and pick the winner. If two are close, pick the one that works better in grayscale.
9. Write `docs/design/score-visualization.md`: the concepts tested, results table, the choice, the reasons, and open questions.
10. Add the chosen score and breakdown designs as components in the NOMI-012 library, with light and dark variants, and link the doc from the library's Components page.

### Done when
- [ ] Three score concepts and three breakdown concepts exist in Figma with the same example data
- [ ] 5 people tested; anonymized notes for each in the issue
- [ ] Results table shows correct answers to "who is it for" and "why did it score low" per concept
- [ ] `docs/design/score-visualization.md` merged with the choice and reasons
- [ ] Chosen concept merged into the NOMI-012 library

### How to check your work
Show the chosen design in grayscale to one new person and ask questions (a) and (b) from step 4. They should answer both correctly within about 10 seconds. If not, revisit the choice before merging.

### Out of scope
- The base token and component library (NOMI-012)
- Coding the breakdown in the app (NOMI-041)
- Benchmark visual and profile switcher (NOMI-061)
- Final tier bands and words (NOMI-049)

### Resources
- Why 5 test users: https://www.nngroup.com/articles/why-you-only-need-to-test-with-5-users/
- Glossary: `docs/nomi-101.md`

---

## NOMI-015: Research five reference products by hand and add them as validated examples
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-002 (same sprint)

### Summary
Research five real OTC products from their FDA labels and write each one as example records in `packages/schema/examples/`: product data, draft risk-dimension severities, and expected scores for three profiles. The records are validated against the shared schemas in CI.

### Why this matters
Every team needs realistic data before the pipeline exists. These five products become fixtures for the app screens (NOMI-029), test cases for the pipeline, and the expected answers for the scoring engine. Many tickets say "start from the reference products if your dependency isn't ready," so these need to exist early and be correct.

### What you will deliver
- One folder per product in `packages/schema/examples/`: `tylenol-extra-strength/`, `aleve/`, `zzzquil/`, `nyquil/`, `store-brand-diphenhydramine/`
- In each folder: `product.json` (matches the `product` schema), `ingredient-dimensions.json` (draft severities, matches `ingredient-dimensions`), `expected-scores.json` (one `score-record` per profile)
- A test that validates every example file against its schema, running in CI
- A verification table in the PR showing a second person checked every value against the label

### Before you start
- Read `docs/nomi-101.md`, especially the glossary entries for NDC, SPL, UNII, Drug Facts panel, mandated warning, persona and severity.
- **NDC11**: the 11-digit National Drug Code we store, without hyphens. The box shows a 10-digit NDC; NOMI-007 explains the conversion (pad the short segment with a leading zero).
- **SPL set id and version**: the label's stable id on DailyMed and its version number. Both are shown on the DailyMed label page.
- **UNII**: FDA's ingredient id. DailyMed lists it next to each ingredient.
- **Marketing category**: shown on the DailyMed label page (for example "OTC monograph" or "NDA"). Aleve and ZzzQuil labels will show which applies; don't assume.
- **Mandated warning**: FDA-required warning text, such as the "Liver warning" on acetaminophen products.
- **Severity 0-3** and **risk dimensions**: defined in `docs/scoring/dimensions.md` (NOMI-016). If it hasn't merged, use the dimension list in the NOMI-016 ticket in `planning/backlog.md` and update when it lands.
- The three profiles: adult 18-64 with no conditions; 65+ with high blood pressure; child 6-11.
- Schemas live in `packages/schema/schemas/` (NOMI-002). If they haven't merged, write the JSON using the field lists in the NOMI-002 ticket and agree field names with the NOMI-002 owner on day one. Convert when the schemas merge.
- Expected scores are hand-drafted targets, not rubric output. The rubric (NOMI-049) is written later and checked against them.

### Steps
1. Pick the exact product for each, and write the choice in the PR: Tylenol Extra Strength (choose one form, for example caplets), Aleve (naproxen sodium tablets or caplets), ZzzQuil (one form), NyQuil (the Cold & Flu version, one form), and one store-brand diphenhydramine sleep aid or allergy product (for example CVS or Walgreens).
2. Find each product's current label on DailyMed. Record the set id, version, and every package NDC listed.
3. Convert each NDC to NDC11 (no hyphens) and note the original 10-digit form next to it.
4. From the label, record brand name, generic name, marketing category, and each active ingredient with UNII, strength and unit (for example acetaminophen, 500 mg per caplet; confirm on the label).
5. From the Drug Facts panel, record the Uses, every mandated warning by heading (for example "Liver warning", "Stomach bleeding warning"), the "Do not use", "Ask a doctor before use if you have" and "Stop use" items, and the maximum daily dose from Directions, quoted exactly.
6. Set the OTC category (for example internal analgesic, sleep aid, cough-cold) using your judgment; NOMI-026 will formalize categories later.
7. Write `product.json` for each product.
8. For each active ingredient, draft a severity (0-3) on every dimension for the three profiles, with a citation for every non-zero value (label set id and section). Write 0 explicitly where you considered a dimension and found no risk. Save as `ingredient-dimensions.json`.
9. Draft an expected score (0-100) and tier for each product and profile, with one sentence of reasoning and the main dimensions that cost points. If the label says do not use for a profile (for example "children under 12 years: do not use"), record a hard stop for that profile. Use the provenance field to mark them as hand-drafted in NOMI-015. Save as `expected-scores.json`.
10. Add a test that loads every file in `packages/schema/examples/*/` and validates it against the matching schema, for example `pipeline/tests/schema/test_examples.py` using the `jsonschema` package. Make sure CI runs it.
11. Ask a second Data Analysis member to check every value against the label. Put the results in a table in the PR: product, field, value, checked (yes/no), notes. Fix anything they flag.

### Done when
- [ ] Five product folders exist with `product.json`, `ingredient-dimensions.json` and `expected-scores.json`
- [ ] Every example validates against its NOMI-002 schema in CI
- [ ] Each product has NDC11s, set id and version, ingredients with UNII and strength, uses, mandated warnings and maximum daily dose
- [ ] Draft severities cover every dimension for the three profiles; every non-zero value is cited
- [ ] Expected scores exist for adult, 65+ with high blood pressure, and child 6-11 for all five products
- [ ] A second person checked every value against the label; the table is in the PR

### How to check your work
Run `uv run pytest pipeline/tests/schema`. Then sanity-check the expected scores: the store-brand diphenhydramine should score worse for 65+ than for the adult (diphenhydramine is strongly anticholinergic), and Aleve should score worse for 65+ with high blood pressure than for the adult. If not, revisit your severities.

### Out of scope
- Writing the schemas (NOMI-002)
- Defining dimensions and personas (NOMI-016)
- The full knowledge base (NOMI-034, NOMI-035)
- The scoring rubric and its computed scores (NOMI-049, NOMI-051)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- openFDA NDC API (to cross-check NDCs): https://open.fda.gov/apis/drug/ndc/
- JSON Schema: https://json-schema.org/
- Glossary: `docs/nomi-101.md`

---

## NOMI-016: Write the risk-dimension, severity and persona definitions
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Write `docs/scoring/dimensions.md`: the list of about 15 risk dimensions every ingredient is rated on, the 0-3 severity scale with criteria, the personas, the condition and medication modifiers, and which evidence sources may set each dimension. Every id in the doc is stable and used by code.

### Why this matters
Nomi scores every OTC product, from Tylenol to Aleve to sleep aids, with one framework: each ingredient gets a severity on the same risk dimensions for each kind of person. This document is the shared vocabulary for the knowledge base (NOMI-034, NOMI-035), the rubric (NOMI-049), onboarding (NOMI-028) and the result screen. If teams use different names or scales, nothing fits together.

### What you will deliver
- `docs/scoring/dimensions.md` with five sections: Dimensions, Severity scale, Personas, Modifiers, Evidence sources per dimension
- A stable snake_case id for every dimension, persona and modifier (for example `gi_bleeding`, `older_65_plus`, `hypertension`)

### Before you start
- Read `docs/nomi-101.md`, especially the glossary entries for risk dimension, severity, persona, profile, hard stop, mandated warning, STOPP/START, ACB and FAERS.
- **Risk dimension**: one kind of harm, rated separately so the app can explain "why" (for example liver damage, stomach bleeding).
- **Severity**: 0 to 3 for one ingredient, one dimension and one persona.
- **Modifier**: a condition or medication that raises severity, for example "naproxen, kidney dimension, +1 if the user has kidney disease."
- **Evidence sources** we use: FDA label text (mandated warnings and Drug Facts sections), OTC monographs, STOPP/START, the ACB scale, and FAERS signals. FAERS shows what gets reported but has no denominator, so it should support a severity, not set it alone; write that rule explicitly.
- The best way to find real examples is to read the Drug Facts panels of a few common products on DailyMed (Tylenol, Advil, Aleve, Benadryl, Sudafed, NyQuil, Afrin).
- The schemas (NOMI-002) and knowledge base will use your ids, so tell the NOMI-002 owner your ids as soon as the draft exists.

### Steps
1. Create `docs/scoring/dimensions.md` with the five sections listed above.
2. Write the Dimensions table with columns: id, name, plain-language label for users, what it covers, example ingredients, example label wording. Start from this list and adjust only with a reason noted in the PR: `liver`, `gi_bleeding`, `cardiovascular` (including blood pressure), `kidney`, `anticholinergic_cognitive`, `sedation_falls`, `serotonergic_interactions`, `anticoagulant_bleeding`, `pediatric`, `rebound_overuse`, `pregnancy_lactation`, `duplicate_dosing`, `excipients`, `local_skin`, `efficacy_evidence`.
3. Give a real example for each, checked on a DailyMed label. Examples to verify: acetaminophen "Liver warning" for `liver`; NSAID "Stomach bleeding warning" for `gi_bleeding`; "Do not use with any other drug containing acetaminophen" for `duplicate_dosing`; dextromethorphan's MAOI warning for `serotonergic_interactions`; nasal decongestant spray overuse warnings (for example oxymetazoline) for `rebound_overuse`; dyes, alcohol, sodium or phenylalanine in inactive ingredients for `excipients`. For `efficacy_evidence`, an example is oral phenylephrine, which an FDA advisory committee found ineffective as a nasal decongestant in 2023; confirm FDA's current status before citing.
4. Write the Severity scale with criteria for each level that someone else could apply the same way. Starting draft to refine: 0 = no meaningful risk for this persona in our sources; 1 = minor or uncommon risk, general caution; 2 = meaningful risk, for example a label "Ask a doctor" item that applies to this persona or an ACB score of 2; 3 = serious risk, for example a label "Do not use" for this persona, a mandated warning about serious harm, an ACB score of 3, or a STOPP "avoid" criterion. Give one worked example per level.
5. Write the Personas table with ids and exact age ranges: `adult_18_64`, `older_65_plus`, `teen_12_17`, `child_6_11`, `child_2_5`, `infant_under_2`, `pregnant`, `breastfeeding`. Note how age-banded label directions (for example "children under 12 years") map onto these bands.
6. Write the Modifiers table with id, user-facing name, type (condition or medication), and the dimensions it affects. Include at least: `hypertension`, `kidney_disease`, `liver_disease`, `glaucoma`, `enlarged_prostate`, `anticoagulants`, `maoi`, `ssri`. Add others you find in "Ask a doctor before use if you have" sections (for example heart disease, thyroid disease, diabetes, asthma or breathing problems, history of stomach ulcers or bleeding), each with the label you found it on.
7. Write the Evidence sources table: for each dimension, which sources may set it (label, monograph, STOPP/START, ACB, FAERS) and any limits, such as "FAERS can support but not set a severity."
8. Add a short "How to use this doc" paragraph at the top and a change log at the bottom: ids never get renamed, only deprecated.
9. Share the ids with the NOMI-002, NOMI-015 and NOMI-028 owners.
10. Get reviews from both cofounders and at least two Data Analysis members on the PR. Resolve every comment.

### Done when
- [ ] `docs/scoring/dimensions.md` merged with all five sections
- [ ] About 15 dimensions, each with an id, plain-language label and a real label example checked on DailyMed
- [ ] Severity scale has written criteria and a worked example for each of 0, 1, 2 and 3
- [ ] All 8 personas with ids and age ranges
- [ ] At least the 8 modifiers listed in step 6, each mapped to dimensions
- [ ] Evidence sources listed for every dimension, including the FAERS limit
- [ ] Approved on the PR by both cofounders and the Data Analysis team

### How to check your work
Give the doc to a teammate who hasn't seen it, with the Aleve label from DailyMed. Ask them to rate naproxen for `older_65_plus` on `gi_bleeding`, `kidney` and `cardiovascular`. If their ratings match yours or differ by at most 1, the criteria are clear enough. If they differ by 2 or more, tighten the wording.

### Out of scope
- Rating ingredients (NOMI-034, NOMI-035)
- Points per severity and how dimensions combine into a score (NOMI-049)
- The mandated-warning catalogue (NOMI-017)
- Onboarding screens that use these lists (NOMI-028)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Glossary: `docs/nomi-101.md`

---

## NOMI-017: Catalogue FDA-mandated OTC warnings and collect 50 label test snippets
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** none

### Summary
Build `pipeline/knowledge/mandated_warnings.yaml`, a catalogue of every FDA-required OTC warning with its wording variants, triggering ingredients, mapped risk dimension and regulatory citation. Collect 50 real label snippets as test fixtures for the rule-based extractor.

### Why this matters
FDA requires standard warning text on many OTC labels: every acetaminophen product has a "Liver warning" and every NSAID a "Stomach bleeding warning." Because the wording is standardized, rules can find it reliably on every label, and each warning maps straight to a risk dimension. The rule extractor (NOMI-031) uses this catalogue, and the knowledge base (NOMI-034, NOMI-035) uses it to set severities.

### What you will deliver
- `pipeline/knowledge/mandated_warnings.yaml` with one entry per warning
- 50 real label snippets in `pipeline/tests/fixtures/warnings/`, one file each, with the expected warnings labeled
- A test in `pipeline/tests/knowledge/test_mandated_warnings.py` that checks the YAML structure and that every fixture names only warnings in the catalogue

### Before you start
- Read `docs/nomi-101.md`, especially mandated warning, monograph, SPL, LOINC section code and Drug Facts panel.
- **Monograph**: FDA's rulebook for a category of OTC drugs, listing allowed ingredients and required warnings. Since the 2020 CARES Act, monographs are issued as final administrative orders on FDA's OTC Monographs@FDA portal. Some required warnings are also in the Code of Federal Regulations, 21 CFR part 201.
- **Regulation citation**: for each warning cite the CFR section or monograph order that requires it. Confirm each one on eCFR or OTC Monographs@FDA; don't guess a section number.
- **LOINC section code**: the code that marks each section in an SPL label, for example `34071-1` Warnings, `50570-1` Do not use, `50569-3` Ask a doctor, `50566-9` Stop use, `51727-6` Inactive ingredients. The full list is in NOMI-023 in `planning/backlog.md`.
- **Wording variant**: the same required warning can differ slightly by product (for example "this product" vs the product name, or "3 or more" vs "three or more").
- **Dimension ids** come from `docs/scoring/dimensions.md` (NOMI-016). If it hasn't merged, use the ids in the NOMI-016 ticket (for example `liver`, `gi_bleeding`, `cardiovascular`, `excipients`) and update later.
- **UNII**: FDA's ingredient id, shown next to each ingredient on DailyMed.

### Steps
1. Start the list with the warnings named in this ticket: Liver warning, Stomach bleeding warning, Heart attack and stroke warning, Reye's syndrome warning, Allergy alert, Sore throat warning, alcohol warnings, sodium content, magnesium content, and phenylketonurics (phenylalanine from aspartame).
2. Find any others by reading Warnings sections across product types on DailyMed (pain relievers, antihistamines, decongestants, cough products, antacids, laxatives, antidiarrheals, nasal sprays) and checking the related monographs. Add each required one.
3. For each warning, find the regulation or monograph that requires it. Record the citation and URL, for example a 21 CFR part 201 section confirmed on eCFR.
4. Define the YAML structure and use it for every entry:
   ```yaml
   - id: liver_warning
     heading: "Liver warning"
     loinc_sections: ["34071-1"]
     variants:
       - "Liver warning: This product contains acetaminophen. Severe liver damage may occur if ..."
     triggering_ingredients:
       - name: acetaminophen
         unii: "<copy from DailyMed>"
     dimension: liver
     citation:
       source: "<CFR section or monograph order id>"
       url: "<eCFR or OTC Monographs@FDA link>"
   ```
5. For each warning, collect wording variants from at least three different labels (include store brands and combination products), copying text exactly.
6. Collect 50 snippets in `pipeline/tests/fixtures/warnings/`, named `snippet_001.yaml` to `snippet_050.yaml`, each with: `set_id`, `product_name`, `loinc_section`, `text` (exact), `expected_warnings` (list of catalogue ids, empty if none). Cover every catalogue entry at least twice and include at least 5 snippets with no mandated warning, so the extractor's false positives can be tested.
7. Write `pipeline/tests/knowledge/test_mandated_warnings.py` that loads the YAML, checks every entry has all fields and a non-empty citation, and checks every `expected_warnings` id in the fixtures exists in the catalogue.
8. Run `uv run pytest pipeline/tests/knowledge` and fix errors.
9. Ask another Data Analysis member to check five citations and five snippets against their sources; note the result in the PR.

### Done when
- [ ] `pipeline/knowledge/mandated_warnings.yaml` merged with at least the 10 warnings in step 1 plus any others found
- [ ] Every entry has heading, LOINC sections, variants, triggering ingredients with UNII, dimension and a citation to its regulation or monograph
- [ ] 50 snippet files in `pipeline/tests/fixtures/warnings/`, every catalogue entry covered at least twice, at least 5 negatives
- [ ] `uv run pytest pipeline/tests/knowledge` passes
- [ ] Spot check of five citations and five snippets recorded in the PR

### How to check your work
Pick three labels you did not use for fixtures (for example a store-brand ibuprofen, a store-brand acetaminophen PM, and an antacid). Read their Warnings sections and list the mandated warnings by hand using only your catalogue. If you find a required warning that isn't in the catalogue, add it.

### Out of scope
- Writing the extractor code (NOMI-031)
- Splitting labels into sections (NOMI-023)
- Setting ingredient severities (NOMI-034, NOMI-035)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- 21 CFR part 201 on eCFR: https://www.ecfr.gov/current/title-21/chapter-I/subchapter-C/part-201
- Glossary: `docs/nomi-101.md`

---

## NOMI-018: Digitize STOPP/START and ACB criteria as cited YAML
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-006 (same sprint)

### Summary
Turn the parts of STOPP/START and the ACB scale that apply to OTC ingredients into two structured, cited YAML files: `pipeline/knowledge/criteria/stopp_start.yaml` and `pipeline/knowledge/criteria/acb.yaml`. Add schema validation that runs in CI.

### Why this matters
STOPP/START (medicines older adults should avoid in certain situations) and the ACB scale (how strongly a drug causes anticholinergic effects like confusion) are published expert judgments we can cite. As data, they set severities in the knowledge base, especially for the 65+ persona. For example, they are why diphenhydramine scores worse for a 75-year-old than for a 30-year-old.

### What you will deliver
- `pipeline/knowledge/criteria/stopp_start.yaml`: one row per STOPP or START criterion relevant to OTC ingredients or classes
- `pipeline/knowledge/criteria/acb.yaml`: one row per OTC ingredient that appears on the ACB scale
- `pipeline/tests/knowledge/test_criteria.py`: Pydantic models for both files and a test that validates them, run in CI
- A spot check of 20 rows by a second person, recorded in the PR

### Before you start
- Read `docs/nomi-101.md`, especially STOPP/START, ACB scale, anticholinergic, NSAID, persona and UNII.
- **STOPP**: criteria for medicines to stop or avoid in older adults in specific situations (for example NSAIDs with certain kidney function). **START**: criteria for medicines that should be started; few will apply to OTC products, but include any that do.
- Use the latest published version of STOPP/START (version 3, published in 2023 in European Geriatric Medicine; confirm the citation in PubMed).
- **ACB scale**: rates drugs 1 to 3 for anticholinergic effect (3 is strongest). Use the most recent published ACB list and record which version and year you used.
- **Persona**: we score for adult 18-64, 65+ and others. These criteria are mainly about the 65+ persona.
- **Licensing**: NOMI-006 records how we may reuse these sources. Until it merges, do not copy criterion text word for word. Write a short paraphrase and cite the criterion number and source. Ask the NOMI-006 owner before relying on anything else.
- OTC ingredients to check against: the lists in NOMI-034 and NOMI-035 in `planning/backlog.md` (acetaminophen, ibuprofen, naproxen, aspirin, diphenhydramine, doxylamine, chlorpheniramine, omeprazole, loperamide and so on), plus their classes (NSAIDs, first-generation antihistamines, proton pump inhibitors, H2 blockers, laxatives, decongestants).
- Dimension ids come from `docs/scoring/dimensions.md` (NOMI-016). If it hasn't merged, use the ids in the NOMI-016 ticket.

### Steps
1. Get the full text of STOPP/START version 3 and the latest ACB list. Save the citations (authors, title, journal, year, DOI or URL) in the PR description.
2. Go through every STOPP/START criterion and keep each one that names an OTC ingredient or a class containing one. List the ones you skipped and why in the PR.
3. Write each kept criterion as a row in `stopp_start.yaml`:
   ```yaml
   - id: stopp_v3_<section>_<number>
     type: stopp            # or start
     criterion_ref: "<section and number as printed>"
     ingredients: [naproxen, ibuprofen]   # explicit ingredients
     classes: [nsaid]                       # class names
     condition: "<the situation, e.g. reduced kidney function with the threshold as printed>"
     recommendation: "<short paraphrase>"
     persona: older_65_plus
     dimensions: [kidney]
     citation:
       source: "STOPP/START version 3"
       year: 2023
       url: "<DOI link>"
   ```
4. Add a `classes` lookup at the top of the file mapping each class to its OTC ingredients (for example `nsaid: [ibuprofen, naproxen, aspirin]`), so rows can be applied to ingredients.
5. Write each OTC ingredient on the ACB list as a row in `acb.yaml`: `ingredient`, `unii` (from DailyMed), `acb_score` (1, 2 or 3), `dimensions: [anticholinergic_cognitive]`, and `citation` (source, version, year, url). Do not add ingredients that aren't on the list; absence is not a score of 0.
6. Write Pydantic models for both files in `pipeline/tests/knowledge/test_criteria.py`. Check required fields, allowed values (`type` is `stopp` or `start`, `acb_score` is 1-3), that every class used in a row exists in the `classes` lookup, and that every row has a citation.
7. Run `uv run pytest pipeline/tests/knowledge` and fix errors. Confirm the test runs in CI.
8. Ask a second Data Analysis member to check 20 random rows (at least 5 from each file) against the source. Record each row id and result in a table in the PR and fix any errors.

### Done when
- [ ] `stopp_start.yaml` and `acb.yaml` merged under `pipeline/knowledge/criteria/`
- [ ] Every row has a citation with source, version or year, and URL
- [ ] Skipped STOPP/START criteria and reasons listed in the PR
- [ ] `uv run pytest pipeline/tests/knowledge` passes locally and in CI
- [ ] 20 rows spot-checked by a second person, results in the PR
- [ ] No criterion text copied word for word unless NOMI-006 says reuse is allowed

### How to check your work
Using only your two files, answer: which criteria apply to naproxen for a 70-year-old, and what is diphenhydramine's ACB score? You should find at least one NSAID STOPP criterion and an ACB score of 3 for diphenhydramine. If either lookup is awkward, fix the structure now, because NOMI-034 and NOMI-035 will do this for every ingredient.

### Out of scope
- AGS Beers Criteria (copyrighted; permission is handled in NOMI-006)
- Setting knowledge-base severities from these criteria (NOMI-034, NOMI-035)
- The license audit itself (NOMI-006)

### Resources
- PubMed (search "STOPP/START version 3" and "Anticholinergic Cognitive Burden"): https://pubmed.ncbi.nlm.nih.gov/
- Pydantic: https://docs.pydantic.dev/
- DailyMed (for UNIIs): https://dailymed.nlm.nih.gov/dailymed/
- Glossary: `docs/nomi-101.md`

---

## NOMI-019: Get UMLS access and build the RxNorm-to-UNII ingredient crosswalk
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S1 | **Depends on:** NOMI-006 (same sprint)

### Summary
Apply for a free UMLS license, download the monthly RxNorm files and mirror them to our private R2 bucket, then build `data/silver/ingredient_crosswalk.parquet`: one row per OTC ingredient linking its UNII to its RxNorm ids and all its name synonyms. Export the list of ingredients that couldn't be linked.

### Why this matters
FDA labels identify ingredients by UNII, while FAERS adverse event reports use free-text drug names like "ADVIL PM" or "naproxen sod." RxNorm connects the two. This crosswalk is what lets the FAERS name matcher (NOMI-033) attach adverse events to the same ingredients the knowledge base scores. Without it, the evidence layer can't be built.

### What you will deliver
- An approved UMLS account (note the approval date in the issue, never the credentials)
- RxNorm full monthly release files mirrored to R2, fetchable with `uv run pipeline fetch rxnorm`
- `pipeline/src/nomi_pipeline/ingest/rxnorm.py`: loads the RxNorm RRF files to `data/bronze/rxnorm/`
- `pipeline/src/nomi_pipeline/identity/ingredient_crosswalk.py`: builds `data/silver/ingredient_crosswalk.parquet`
- `pipeline/reports/crosswalk_unlinked.csv`: OTC ingredients that couldn't be linked, with a reason
- Tests in `pipeline/tests/identity/test_ingredient_crosswalk.py`

### Before you start
- Read `docs/nomi-101.md`, especially UNII, RxNorm / RxCUI, UMLS, FAERS, NDC directory and bronze/silver/gold.
- **UMLS license**: free from the National Library of Medicine; required to download RxNorm files. Approval can take several business days, so apply on day 1.
- **RxCUI**: RxNorm's id for a concept. Term types (TTY) that matter here: `IN` (ingredient, for example naproxen), `PIN` (precise ingredient, a salt form such as naproxen sodium), `BN` (brand name, such as Aleve), `SY`/`TMSY` (synonyms).
- **RRF files**: RxNorm's pipe-delimited files with no header row. `RXNCONSO.RRF` has names and ids, `RXNREL.RRF` relationships (for example PIN to IN, BN to IN), `RXNSAT.RRF` attributes. Column lists are in the RxNorm technical documentation.
- **Where UNIIs are in RxNorm**: they come from FDA's SPL source (`SAB=MTHSPL`) and may also appear as an attribute in `RXNSAT`. Confirm in the RxNorm technical documentation.
- **License rule from NOMI-006**: use only `SAB=RXNORM` content. MTHSPL is FDA data, but confirm with the NOMI-006 owner that using its UNII codes is allowed. If not, get UNIIs from openFDA's NDC data (`openfda.unii`, `openfda.rxcui`) or the DailyMed ingredients table from NOMI-010 instead.
- **Sharing**: confirm in the UMLS license terms whether teammates may download RxNorm from our private R2 bucket or each need their own UMLS account. Never make the RxNorm files public.
- **OTC ingredient list (denominator)**: distinct active ingredients in `data/bronze/ndc.parquet` from NOMI-009. If NOMI-009 hasn't merged, start with the ingredients in `packages/schema/examples/` (NOMI-015) plus the ingredient lists in NOMI-034 and NOMI-035, and rerun on the full list when it lands.
- If the `pipeline fetch` command (NOMI-008) isn't ready, download the zip by hand to `data/raw/rxnorm/` and add the fetch source when NOMI-008 merges.

### Steps
1. Apply for a UMLS license on day 1. Post in the issue when you applied and when it was approved.
2. Check the NOMI-006 doc (or ask its owner) about MTHSPL use and team sharing. Record the answer in the issue.
3. Download the RxNorm Full Monthly Release zip. Record the release date.
4. Add an `rxnorm` source to the NOMI-008 fetch tooling: upload the zip to the private R2 bucket with a checksum in the manifest, so `uv run pipeline fetch rxnorm` downloads and verifies it into `data/raw/rxnorm/`.
5. Write `ingest/rxnorm.py` to read `RXNCONSO.RRF`, `RXNREL.RRF` and `RXNSAT.RRF` with Polars (`separator="|"`, no header, drop the empty last column, set column names from the docs) and write Parquet to `data/bronze/rxnorm/`. Expose it as `uv run pipeline ingest rxnorm`.
6. Build the OTC ingredient list: distinct active ingredient names (and UNIIs where present) from `data/bronze/ndc.parquet`, normalized to uppercase with extra spaces removed.
7. In `identity/ingredient_crosswalk.py`, link each OTC ingredient to its RxNorm `IN` concept. Match by UNII first; fall back to exact normalized name against `IN` and `PIN` names. Map `PIN` to its `IN` through `RXNREL`.
8. Collect synonyms for each `IN`: all names of the `IN` itself, its `PIN`s, and the `BN`s that contain it, from `SAB=RXNORM` rows. Deduplicate case-insensitively.
9. Write `data/silver/ingredient_crosswalk.parquet` with columns: `unii`, `ingredient_name`, `rxcui_in`, `rxcui_pin` (nullable), `synonyms` (list of strings), `match_method` (`unii` or `name`), `rxnorm_release`.
10. Write `pipeline/reports/crosswalk_unlinked.csv` with columns `ingredient_name`, `unii`, `product_count`, `reason`. Look at the top 20 unlinked by product count and fix any that are naming problems.
11. Write tests: acetaminophen, naproxen and diphenhydramine link correctly; naproxen sodium resolves to naproxen; "Aleve" appears in naproxen's synonyms; no row has an empty `rxcui_in`.
12. Log the linked share and the row count when the build runs.

### Done when
- [ ] UMLS license approved; RxNorm release mirrored to R2 and fetchable with checksum verification
- [ ] Decisions on MTHSPL use and team sharing recorded in the issue
- [ ] `data/silver/ingredient_crosswalk.parquet` builds from one command with the columns in step 9
- [ ] At least 98% of OTC ingredients from NOMI-009 linked (share printed by the build)
- [ ] `pipeline/reports/crosswalk_unlinked.csv` exported and committed
- [ ] `uv run pytest pipeline/tests/identity` passes

### How to check your work
Open the output in DuckDB: `duckdb -c "SELECT ingredient_name, rxcui_in, len(synonyms) FROM 'data/silver/ingredient_crosswalk.parquet' WHERE ingredient_name IN ('ACETAMINOPHEN','NAPROXEN SODIUM','DIPHENHYDRAMINE HYDROCHLORIDE')"`. Each should have an `rxcui_in` and several synonyms. Then pick five unlinked rows and confirm they really don't exist in RxNorm under another spelling.

### Out of scope
- Matching free-text FAERS drug names (NOMI-033)
- Applying the matcher to all FAERS rows (NOMI-046)
- Ingesting the NDC directory (NOMI-009) or DailyMed labels (NOMI-010)
- The data source license audit (NOMI-006)

### Resources
- UMLS: https://www.nlm.nih.gov/research/umls/index.html
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/index.html
- RxNorm technical documentation: https://www.nlm.nih.gov/research/umls/rxnorm/docs/techdoc.html
- openFDA NDC API: https://open.fda.gov/apis/drug/ndc/
- Polars: https://docs.pola.rs/
- DuckDB: https://duckdb.org/
- Glossary: `docs/nomi-101.md`

---

# Sprint 2: Oct 23 to Oct 29

## NOMI-021: Complete legal, IP and regulatory intake and write the decision memo
**Team:** cofounders | **Priority:** P0 | **Sprint:** S2 | **Depends on:** none

### Summary
Get free legal advice on Nomi's main legal, IP and regulatory risks, then write a private decision memo for the cofounders and a short summary for the team. The summary is presented at the Sprint 2 Friday demo.

### Why this matters
Nomi gives people a safety score for named brands and suggests alternatives. That raises three open questions: whether FDA could treat the app as medical device software, whether Georgia Tech has a claim on IP built by students, and whether scoring named brands exposes us to defamation claims. We need answers before any external user touches the app, and we can't pay for lawyers, so we use free law-school clinics and GT programs.

### What you will deliver
- A private decision memo (Google Doc in the cofounders' shared drive, NOT in this public repo) with one section per question below: the question, the advice received, who gave it, the decision, and open follow-ups
- A one-page team summary with no sensitive detail, posted in the team channel and presented at the Friday demo
- A submitted CREATE-X application (or a written note in the memo explaining why we didn't apply)
- A decision, recorded in the memo, on who owns the Apple and Google developer accounts

### Before you start
- **CREATE-X**: Georgia Tech's student startup program. It offers mentoring and access to legal resources.
- **GT IP policy**: Georgia Tech's rules on who owns inventions and software made by students, staff and faculty, especially when university resources or funding are used. Find it in GT's official policy library.
- **GT Big Data Big Impact**: the GT program Nomi is built under. Check whether it has its own rules on spinning a project out into a company.
- **FDA device-software status**: FDA regulates some software as a medical device. Some health software is excluded or falls under lower-risk policies (for example clinical decision support and general wellness guidance). Whether a consumer OTC safety score qualifies is a legal question for the clinic, not something to decide ourselves.
- **E&O insurance**: errors and omissions insurance, which covers claims that our information caused harm.
- **Defamation exposure**: the risk that a brand claims our score is false and damaging. Our main defense is that every point is cited (see ADR-0002 and the rubric).
- **LLC**: limited liability company. The question is when to form one, which affects who signs agreements and who can own developer accounts.
- ADR-0002 (`docs/adr/0002-privacy.md`, NOMI-003) describes how health data stays on the phone. If it hasn't merged, send the clinic the current draft from the NOMI-003 PR.
- Glossary and product overview: `docs/nomi-101.md`.

### Steps
1. Read GT's IP policy. Write down in the memo, in your own words, what it says about student-created software and when GT can claim ownership. Note any form we would need to file.
2. Check the GT Big Data Big Impact program rules on spin-outs. Email the program contact if the rules aren't written down, and paste their reply into the memo.
3. Apply to CREATE-X through its official application page. Save the confirmation email in the shared drive.
4. Find the intake page for a free entrepreneurship or small-business legal clinic at Emory Law or Georgia State Law. Request a consult and book the earliest slot.
5. Before the consult, send the clinic a one-page brief: what Nomi does (use `docs/nomi-101.md`), that we're students, our timeline (demo Nov 20), and the questions below.
6. Ask these questions in the consult and record each answer in the memo:
   - FDA device-software status of a consumer OTC safety score that recommends alternatives
   - Pediatric dosing: is showing scores and label limits for children a different risk level?
   - LLC timing: when to form one and in which state
   - E&O insurance: do we need it before external users, and at what stage
   - Defamation exposure from scoring named brands, and what wording or disclaimers reduce it
   - Review of ADR-0002: does the on-device privacy design hold up legally?
7. Decide who owns the Apple Developer Program account (annual fee) and the Google Play Console account (one-time fee). Note in the memo that Apple's organization enrollment needs a D-U-N-S number, so it depends on the LLC decision. Record the owner, the account type (individual or organization) and how the fee is paid.
8. Write the decision memo. For each question: advice received, our decision, open follow-ups with an owner and date.
9. Write the one-page team summary. Include only decisions and rules the team must follow (for example "no public claims about safety until X"). Leave out legal reasoning and anything sensitive.
10. Present the summary at the Friday demo.

### Done when
- [ ] GT IP policy and Big Data Big Impact spin-out rules summarized in the memo
- [ ] CREATE-X application submitted, or the reason for not applying recorded in the memo
- [ ] At least one law-school clinic consult held, with answers to all six questions in the memo
- [ ] Apple and Google developer account owner decided and recorded
- [ ] Memo stored privately in the cofounders' shared drive, not in this repo
- [ ] Team summary shared at the Friday demo

### How to check your work
Search the repo (`git grep -i "memo"`) and confirm no memo content was committed. Ask a teammate to read the one-page summary and tell you, without other context, what they are and aren't allowed to say publicly about Nomi. If they can't, rewrite it.

### Out of scope
- Data source licensing (NOMI-006)
- Writing the privacy ADR itself (NOMI-003)
- Implementing on-device encrypted storage (NOMI-039)
- Faculty partnership agreements (NOMI-005, NOMI-036)

### Resources
- FDA Digital Health Center of Excellence: https://www.fda.gov/medical-devices/digital-health-center-excellence
- FDA guidance search (look up "Clinical Decision Support Software" and "General Wellness"): https://www.fda.gov/regulatory-information/search-fda-guidance-documents
- Privacy design: `docs/adr/0002-privacy.md`
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-022: Run 10 user interviews and write the round 1 synthesis
**Team:** cofounders | **Priority:** P1 | **Sprint:** S2 | **Depends on:** none

### Summary
Interview 10 people who buy OTC medicine for themselves or others, then write an anonymized synthesis in `docs/research/interviews-round-1.md`. The Data Analysis and Visualization teams use it to word explanations and onboarding.

### Why this matters
Explanation templates (NOMI-048) and onboarding screens (NOMI-028) should use the words real users use, not our internal terms like "anticholinergic" or "persona". We also need to know how comfortable people are entering health conditions into an app, because the score depends on that information.

### What you will deliver
- `docs/research/interviews-round-1.md`: an anonymized synthesis with four sections: pains, trust signals, privacy concerns, vocabulary
- An interview script, included at the end of the synthesis file
- Raw notes stored privately in the cofounders' shared drive, NOT in the repo

### Before you start
- **OTC**: over-the-counter medicine, sold without a prescription. See `docs/nomi-101.md`.
- **Caregiver**: someone who buys or manages medicine for another person, such as an adult child helping a parent over 65.
- **Anonymized**: no names, employers, exact ages, locations or any detail that could identify a person. Use labels like "P3, caregiver for parent in their 80s".
- **Synthesis**: patterns across interviews, with short supporting quotes, not a transcript.
- Target mix: 5 caregivers of adults 65+, 3 parents of young children, 2 people taking 3 or more daily medications.
- If any findings might be published later with a faculty partner, ask the partner (NOMI-005) whether ethics review is needed before you start, and note the answer in the PR.

### Steps
1. Write the interview script (30 minutes). Cover, in this order: their last OTC purchase; how they chose it; who they buy for; what information they would trust and why; how comfortable they would be entering health conditions and medications into an app. Add a short consent line at the top: what the interview is for, that notes are anonymized, and that they can stop at any time.
2. Recruit 10 people through personal networks, GT groups and family contacts, matching the target mix. Track recruits in a private sheet in the shared drive.
3. Run the interviews in person or by video. Ask for consent before taking notes or recording. Don't record if they decline.
4. Write notes within 24 hours of each interview, in the private shared drive. Capture exact phrases people use for risks and conditions (for example "makes me groggy", "bad for my stomach").
5. After all 10, group the notes into the four themes: pains, trust signals, privacy concerns, vocabulary.
6. Write `docs/research/interviews-round-1.md`. For each theme, list 3-6 findings, each with how many participants said it (for example "7 of 10") and one anonymized quote.
7. In the vocabulary section, add a table with two columns: "our term" and "what people said" (for example "sedation" -> "drowsy", "hypertension" -> "high blood pressure").
8. Add a short "Implications" section: three to five concrete suggestions for NOMI-028 (onboarding) and NOMI-048 (explanation templates).
9. Re-read the file and remove anything that could identify a participant. Open a PR.
10. Present the findings at the Friday demo.

### Done when
- [ ] 10 interviews completed, matching the 5 / 3 / 2 mix (or the actual mix stated in the file if recruiting fell short)
- [ ] `docs/research/interviews-round-1.md` merged with the four themes, vocabulary table and implications
- [ ] No names or identifying details in the repo
- [ ] Raw notes stored only in the private shared drive
- [ ] Presented at the Friday demo

### How to check your work
Give the synthesis to the NOMI-028 and NOMI-048 owners. Each should be able to name at least two changes they will make because of it. Search the file for any first names, workplaces or cities and remove them.

### Out of scope
- Writing explanation templates (NOMI-048)
- Building onboarding screens (NOMI-028)
- Usability testing of screens (NOMI-013, NOMI-014)

### Resources
- Product overview and glossary: `docs/nomi-101.md`
- Demo script for context on who we serve: `docs/demo/script.md` (NOMI-004)

---

## NOMI-023: Split DailyMed labels into Drug Facts sections
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-010

### Summary
Parse every OTC label from DailyMed into its individual Drug Facts sections (Warnings, Directions, Uses and so on) and write them to `data/bronze/spl_sections.parquet`, with a committed coverage report. The label extractors in NOMI-031 and NOMI-032 read this table.

### Why this matters
Label extraction works on one section at a time. For example, the rules look for age limits only in Directions, and mandated warnings only in Warnings. Feeding whole labels to the extractors would be slower, costlier for the LLM, and less accurate. SPL files tag each section with a standard code, so splitting can be exact.

### What you will deliver
- `pipeline/src/nomi_pipeline/ingest/sections.py`, run with `uv run pipeline ingest sections`
- `data/bronze/spl_sections.parquet` with one row per section per label (not committed; `data/` is gitignored)
- `pipeline/reports/spl-section-coverage.md`: the share of labels that have each section (committed)
- Tests in `pipeline/tests/ingest/test_sections.py`

### Before you start
- **DailyMed / SPL**: DailyMed publishes every drug label as SPL (Structured Product Labeling) XML. Each label has a **set id** (stable across versions) and a **version** number. See `docs/nomi-101.md`.
- **Drug Facts panel**: the standard OTC label layout: Active ingredient, Purpose, Uses, Warnings, Directions, Inactive ingredients.
- **LOINC section code**: a code on each `<section>` element in SPL that says what the section is. In the XML it looks like `<code code="34071-1" codeSystem="2.16.840.1.113883.6.1" .../>`.
- The codes to split on:

| Section | LOINC |
|---|---|
| Active ingredient | 55106-9 |
| Purpose | 55105-1 |
| Uses | 34067-9 |
| Warnings | 34071-1 |
| Do not use | 50570-1 |
| Ask a doctor | 50569-3 |
| Ask a doctor or pharmacist | 50568-5 |
| When using | 50567-7 |
| Stop use | 50566-9 |
| Pregnancy/breastfeeding | 53414-9 |
| Directions | 34068-7 |
| Inactive ingredients | 51727-6 |

- Sections can be nested. "Do not use", "Ask a doctor", "When using" and "Stop use" usually sit inside Warnings as child sections. Keep both the parent and the children.
- SPL uses the XML namespace `urn:hl7-org:v3`. With lxml, pass it in every XPath query.
- Input: the DailyMed Human OTC SPL zips in `data/raw/` (from NOMI-008) and the label list in `data/bronze/spl_products.parquet` (NOMI-010), which already keeps only the latest version of each label.
- If NOMI-010 hasn't merged, read the zips directly and keep the highest version per set id yourself. If NOMI-008 hasn't merged either, download a few labels by hand from DailyMed (including the five reference products: Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil, store-brand diphenhydramine) and build against those.

### Steps
1. Download 5 small SPL XML files from DailyMed, including Tylenol Extra Strength and NyQuil. Save them under `pipeline/tests/fixtures/spl/` as test fixtures (keep each under 100 KB).
2. Write a function `split_sections(xml_bytes: bytes) -> list[Section]` in `sections.py`. Walk every `<section>` element, read its `<code code=...>`, `<title>` and `<text>`, and record the parent section's code if it's nested.
3. Keep only sections whose code is in the table above. Ignore others (such as "Package label").
4. For each section store: `set_id`, `version`, `loinc_code`, `section_name` (from the table), `parent_loinc` (null if top level), `order` (position in the label), `title` (as printed), `text_raw` (all text inside the section, including child sections, as extracted) and `text_clean`.
5. Build `text_clean` from `text_raw`: collapse runs of whitespace to one space, turn list items into lines starting with "- ", strip bullet characters (such as the solid round bullet and square bullet), and trim. Keep `text_raw` unchanged so extractors can fall back to it.
6. Write unit tests on the 5 fixtures. Assert, for example, that Tylenol has a Warnings section whose clean text contains "Liver warning", and that a "Do not use" section has `parent_loinc == "34071-1"`.
7. Add the CLI command `uv run pipeline ingest sections`. Loop over every latest-version OTC label, call `split_sections`, and write `data/bronze/spl_sections.parquet` with Polars.
8. Log every label that fails to parse with its set id to `data/bronze/spl_sections_errors.csv`. Don't stop the run on one bad file.
9. Write the coverage report generator. For each of the 12 sections, report the count and percent of labels that contain it. Also report the total labels processed and parse failures.
10. Write `pipeline/reports/spl-section-coverage.md` and commit it. Add two sentences explaining any section under 80% coverage (for example "Pregnancy/breastfeeding is often written inside Warnings without its own code").

### Done when
- [ ] `uv run pipeline ingest sections` writes `data/bronze/spl_sections.parquet` with the columns in step 4
- [ ] All 12 LOINC codes are handled, including nested sections with `parent_loinc`
- [ ] Both `text_raw` and `text_clean` are present for every row
- [ ] Unit tests on at least 5 fixture labels pass with `uv run pytest pipeline/tests/ingest`
- [ ] `pipeline/reports/spl-section-coverage.md` committed with per-section share, total labels and failure count

### How to check your work
Open the table in DuckDB: `duckdb -c "SELECT section_name, count(*) FROM 'data/bronze/spl_sections.parquet' GROUP BY 1 ORDER BY 2 DESC"`. Warnings, Directions and Active ingredient should be present on nearly every label. Then pick three products from home, find them in the table by set id, and compare the Warnings text with the box.

### Out of scope
- Parsing products, ingredients and package NDCs (NOMI-010)
- Extracting facts such as warnings, age limits and doses from the sections (NOMI-031, NOMI-032)
- Merging extractor output (NOMI-045)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- DailyMed SPL resources and downloads: https://dailymed.nlm.nih.gov/dailymed/spl-resources.cfm
- FDA SPL overview: https://www.fda.gov/industry/fda-data-standards-advisory-board/structured-product-labeling-resources
- Polars: https://docs.pola.rs
- DuckDB: https://duckdb.org

---

## NOMI-024: Ingest and deduplicate FAERS quarterly files from 2014
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-008

### Summary
Load every FAERS quarterly file from 2014 onward into typed Parquet tables in `data/bronze/faers/`, removing duplicate reports the way FDA recommends. Data Analysis uses these tables to find adverse event signals.

### Why this matters
FAERS (FDA's adverse event reports) is our real-world evidence: it shows which problems people report with which drugs. Roughly 30% of raw reports are duplicates (the same case submitted again with updates), and the file formats change across quarters. If duplicates stay in, signals look stronger than they are. Every later FAERS ticket (NOMI-044, NOMI-046, NOMI-053) builds on these tables.

### What you will deliver
- `pipeline/src/nomi_pipeline/ingest/faers.py`, run with `uv run pipeline ingest faers`
- Typed, deduplicated tables in `data/bronze/faers/`: `demo.parquet`, `drug.parquet`, `reac.parquet`, `outc.parquet`, `indi.parquet`, `ther.parquet`, `rpsr.parquet` (not committed)
- `pipeline/reports/faers-dedup.md`: dedup stats per quarter (committed)
- Tests in `pipeline/tests/ingest/test_faers.py`

### Before you start
- **FAERS**: FDA Adverse Event Reporting System. Released as quarterly ZIP files of `$`-delimited text tables. See `docs/nomi-101.md`.
- The seven tables, joined on `primaryid`:
  - DEMO: one row per report version: `primaryid`, `caseid`, `caseversion`, `fda_dt`, age, age unit, sex, country
  - DRUG: drugs in the report, with `drug_seq`, `role_cod`, `drugname`
  - REAC: reactions, as MedDRA preferred terms (`pt`)
  - OUTC: outcomes (death, hospitalization and so on)
  - INDI: what each drug was taken for (indications)
  - THER: therapy start and end dates
  - RPSR: who reported it
- **caseid / caseversion / primaryid**: a case is one patient event (`caseid`). Each update creates a new version (`caseversion`), and each version has its own `primaryid`.
- **Deduplication rule** (FDA recommended): keep only the latest `caseversion` per `caseid`. If two rows tie, keep the higher `primaryid`. Dedup must be global across all quarters, because an update to a 2015 case can arrive in 2018. Confirm the exact rule in the README inside each quarterly ZIP.
- **Drug role codes** (`role_cod`): PS primary suspect, SS secondary suspect, C concomitant (taken but not suspected), I interacting. Keep all four.
- **Age**: stored as a number plus a unit code (for example years, months, weeks, days, decades). Convert to years in a new `age_years` column and keep the originals.
- **Format changes**: columns were added and renamed over the years, and some files have stray line breaks or a trailing `$`. Check each quarter's README and header row.
- Input: FAERS quarterly files in `data/raw/faers/` from `uv run pipeline fetch faers` (NOMI-008). If NOMI-008 hasn't merged, download two quarters directly from the FAERS quarterly data page and build against those.
- The full dataset is large. Use Polars lazy scans (`pl.scan_csv`) and write one quarter at a time.

### Steps
1. Download or fetch two quarters (for example 2014Q1 and 2023Q4). Read each README and header row. Write down every column difference in a dict `COLUMN_MAP` in `faers.py` that maps each quarter's column names to one standard set (lowercase).
2. Write `read_quarter(path, table) -> pl.LazyFrame` that reads one table from one quarter with `separator="$"`, handles the trailing delimiter and bad lines, renames columns via `COLUMN_MAP`, and casts types (ids as Int64, dates as Date, age as Float64).
3. Add `quarter` (for example `"2014Q1"`) to every row.
4. Add `age_years` to DEMO by converting age and unit. Leave it null if the unit is missing or unknown.
5. Load all seven tables for every quarter from 2014Q1 to the latest available.
6. Deduplicate: from the combined DEMO table, keep the latest `caseversion` per `caseid`, tie-broken by highest `primaryid`. Collect the kept `primaryid` set.
7. If the quarterly ZIPs include a list of deleted cases, remove those `caseid`s too. Note in the report whether you found one.
8. Filter the other six tables to the kept `primaryid`s.
9. Write each table to `data/bronze/faers/<table>.parquet`.
10. Compute per-quarter stats: raw DEMO rows, rows kept after dedup, rows removed, and percent removed. Write them to `pipeline/reports/faers-dedup.md` as a table, plus the overall totals.
11. Write tests with a tiny hand-made fixture (5 cases, some with two or three versions across two quarters) in `pipeline/tests/fixtures/faers/`. Assert the right versions survive and that DRUG rows for removed versions are dropped.

### Done when
- [ ] `uv run pipeline ingest faers` loads all seven tables for every quarter from 2014Q1 onward
- [ ] Running it twice on the same inputs produces identical files (compare checksums)
- [ ] Only the latest `caseversion` per `caseid` remains in DEMO, and the other tables contain only kept `primaryid`s
- [ ] `role_cod` (PS, SS, C, I), age, `age_years`, sex, indications and all drugs per report are kept
- [ ] `pipeline/reports/faers-dedup.md` committed with per-quarter dedup stats
- [ ] Fixture tests pass with `uv run pytest pipeline/tests/ingest`

### How to check your work
Run `duckdb -c "SELECT count(*), count(DISTINCT caseid) FROM 'data/bronze/faers/demo.parquet'"`. The two numbers must be equal. The overall share removed should be in the range of the roughly 30% duplicates we expect; if it's far off, recheck the dedup. Then look up a few famous drug names in DRUG (`WHERE drugname ILIKE '%TYLENOL%'`) and confirm rows exist across many quarters.

### Out of scope
- Mapping drug names to ingredients (NOMI-033, NOMI-046)
- Building drug and reaction pair tables and age bands (NOMI-044)
- Computing signals (NOMI-053)

### Resources
- FAERS quarterly data files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- FAERS overview: https://www.fda.gov/drugs/surveillance/fdas-adverse-event-reporting-system-faers
- Polars lazy API: https://docs.pola.rs
- DuckDB: https://duckdb.org

---

## NOMI-025: Build the barcode-to-product resolver and report coverage on real barcodes
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-007, NOMI-009, NOMI-010, NOMI-020

### Summary
Write the resolver that turns a scanned barcode into the exact product with its ingredients and strengths, output `data/silver/product.parquet` in the `product` contract format, and report coverage on the real barcodes from the collection drive by Oct 29.

### Why this matters
This is the one piece the demo cannot work without. If scanning a box doesn't return the right product and ingredients, nothing else matters. The coverage number reported on Oct 29 is a checkpoint: if it's well below target, the cofounders move more people onto identity work in Sprint 3.

### What you will deliver
- `pipeline/src/nomi_pipeline/identity/resolve.py`, run with `uv run pipeline resolve`
- `data/silver/product.parquet` matching the `product` schema in `packages/schema/schemas/` (not committed)
- `pipeline/reports/identity-coverage.md`: coverage on the NOMI-020 barcodes with every miss categorized (committed by Oct 29)
- Tests in `pipeline/tests/identity/test_resolve.py`

### Before you start
- **NDC / NDC11**: FDA's product and package code. Barcodes contain a 10-digit NDC with no hyphens, which can be split three ways, so `ndc_candidates()` (NOMI-007) returns three 11-digit candidates. See `docs/nomi-101.md`.
- **NDC directory**: FDA's list of marketed drug packages, in `data/bronze/ndc.parquet` (NOMI-009). Each package NDC11 links to an `spl_set_id`.
- **SPL set id**: the label's stable id. Ingredients, strengths and units come from `data/bronze/spl_products.parquet` and `data/bronze/spl_ingredients.parquet` (NOMI-010). SPL package NDCs are a second place to find a match.
- **UNII**: FDA's ingredient id, our main ingredient key.
- **Ground-truth barcodes**: `pipeline/tests/fixtures/barcodes.csv` (NOMI-020), real barcodes with product name, store and aisle.
- **`product` contract** (NOMI-002): NDC11, SPL set id and version, brand and generic names, marketing category, OTC category, uses, ingredients (UNII, strength, unit). OTC category is filled by NOMI-026 and uses by NOMI-047; leave them null here.
- If a dependency hasn't merged: copy the barcode parser from the NOMI-007 PR branch; for NOMI-009/010, use their PR branches or build a small fixture of the five reference products from `packages/schema/examples/`; for NOMI-020, use whatever rows are in the collection form so far.

### Steps
1. Write `resolve_barcode(barcode: str) -> Resolution`. It calls `ndc_candidates()`, looks up each candidate in the NDC directory package NDC11 column, and also in SPL package NDCs.
2. For each matching candidate, follow `spl_set_id` to the latest label version and pull active ingredients (UNII, strength, unit), brand name, generic name and marketing category.
3. Choose one candidate when several match. Rules, in order: prefer a candidate found in both the NDC directory and SPL; then prefer one with active ingredients present; if more than one still remains, return status `conflict` with all matches listed.
4. Give every result a `status`: `resolved`, `conflict`, or a miss reason: `invalid_barcode` (bad check digit or length), `no_ndc` (barcode doesn't start with `3`), `ndc_not_found` (no candidate in either source), `no_label` (NDC found but no SPL label), `no_ingredients` (label found but no active ingredients parsed).
5. Build `data/silver/product.parquet`: one row per package NDC11 that links to a label, with the `product` contract fields. Validate a sample of rows against the schema with the generated Pydantic model.
6. Run `resolve_barcode` over every row in `barcodes.csv`.
7. Check correctness, not just a match: compare the resolved brand name to the product name in the CSV. Flag mismatches as `wrong_product`. Hand-check every flagged row and 20 random `resolved` rows.
8. Write `pipeline/reports/identity-coverage.md` with: total barcodes, percent correctly resolved, a table of counts per status, coverage split by store brand vs national brand and by aisle, and 3 example barcodes per miss category.
9. Write tests using the five reference products: each one's barcode resolves to the right NDC11 and ingredients.
10. Post the coverage number in the team channel by Oct 29.

### Done when
- [ ] `uv run pipeline resolve` writes `data/silver/product.parquet` and it validates against the `product` schema
- [ ] Multiple matching candidates are handled by the rules in step 3, and conflicts are flagged
- [ ] `pipeline/reports/identity-coverage.md` committed by Oct 29, with every miss assigned a category
- [ ] Coverage reported by Oct 29 (target at least 90% of ground-truth barcodes correctly resolved)
- [ ] Reference product tests pass with `uv run pytest pipeline/tests/identity`

### How to check your work
Take five boxes from home, type their barcodes into `uv run python -c "from nomi_pipeline.identity.resolve import resolve_barcode; print(resolve_barcode('<digits>'))"` and compare the result to the box: brand, ingredients and strengths should match the Drug Facts panel. In the report, the status counts should add up to the total number of barcodes.

### Out of scope
- Fixing the misses to reach 95% (NOMI-037)
- OTC category and scope flags (NOMI-026)
- Uses classification (NOMI-047)
- Lookup on the phone (NOMI-040)

### Resources
- FDA NDC directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- openFDA NDC API reference: https://open.fda.gov/apis/drug/ndc/
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Glossary: `docs/nomi-101.md`

---

## NOMI-026: Add OTC category and scope flags to every product
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-009, NOMI-010

### Summary
Give every product an OTC category (such as internal analgesics or antacids) or a scope flag (homeopathic or out of scope), add these as columns on the `product` table, and report counts per category and flag.

### Why this matters
Benchmarks ("better than 82% of pain relievers") and alternatives only make sense within a category: a sleep aid is never compared to an antacid. Some labels DailyMed lists as OTC shouldn't be scored at all. Homeopathic products were never evaluated by FDA, and drug-cosmetics like sunscreen are out of scope for now. Without these flags the app would score things it shouldn't.

### What you will deliver
- `pipeline/knowledge/otc_categories.yaml`: the category list with matching rules
- `pipeline/src/nomi_pipeline/identity/category.py` with `assign_category(products: pl.DataFrame) -> pl.DataFrame`
- Two new columns on `data/silver/product.parquet`: `otc_category` and `scope_flag` (`in_scope`, `homeopathic`, `out_of_scope`)
- `pipeline/reports/category-counts.md` with counts per category and per flag (committed)
- Tests in `pipeline/tests/identity/test_category.py`

### Before you start
- **Marketing category**: how a product is legally sold. Values include OTC monograph, NDA (a prescription drug switched to OTC, like Claritin) and unapproved homeopathic. It's a column in `data/bronze/ndc.parquet` (NOMI-009) and `spl_products.parquet` (NOMI-010).
- **Monograph**: FDA's rulebook for a category of OTC drugs: allowed ingredients, doses and required warnings. The NDC directory records which monograph a product follows in its application number field; confirm the exact field and value format in the data.
- **Homeopathic**: marketed as unapproved homeopathic. The app shows these as "Not evaluated by FDA for safety or effectiveness" and doesn't score them.
- **Out of scope for now**: sunscreen, hand sanitizer, fluoride toothpaste, antiperspirant, dandruff shampoo.
- The `product` table is written by NOMI-025 (same sprint, not a dependency). If it isn't ready, run `assign_category` on `ndc.parquet` joined to `spl_ingredients.parquet` and agree with the NOMI-025 owner to call your function inside the resolver.
- If NOMI-009 or NOMI-010 hasn't merged, build against their PR branches or a fixture of 30 products you pick by hand from DailyMed, covering every category and flag.

### Steps
1. Draft the category list in `pipeline/knowledge/otc_categories.yaml`. Start with: internal analgesics, antacids, acid reducers, antidiarrheals, laxatives, antiemetics, cough-cold, antihistamines and allergy, nighttime sleep aids, nasal products, ophthalmic, topical analgesics, topical antifungals, first aid antiseptics and antibiotics, smoking cessation, other. Add categories you find in the data.
2. For each category, write matching rules in the YAML in priority order: monograph (from the application number field), then active ingredient UNIIs, then dosage form and route. Example: ingredients acetaminophen, ibuprofen, naproxen or aspirin with route oral map to internal analgesics.
3. Write the homeopathic rule: marketing category contains "HOMEOPATHIC" sets `scope_flag = homeopathic`.
4. Write out-of-scope rules for the five product types. Use monograph where possible, then ingredient plus dosage form (for example sodium fluoride in a toothpaste or dentifrice form). Be careful with ingredients used in more than one product type, such as zinc oxide (sunscreen and diaper rash cream) and salicylic acid (acne and dandruff).
5. Implement `assign_category`. Every product gets either an `otc_category` with `scope_flag = in_scope`, or a scope flag of `homeopathic` or `out_of_scope`. Products no rule matches get `otc_category = other` and are listed in the report.
6. Write tests with at least one product per category and per flag, including the five reference products in `packages/schema/examples/`.
7. Run over all products and write `pipeline/reports/category-counts.md`: counts per category, counts per flag, and the 20 most common products in `other` so the rules can be improved.
8. Spot-check 30 random products against their DailyMed labels and fix any rule that's wrong. Note the spot-check result in the report.

### Done when
- [ ] Every product in `product.parquet` has an `otc_category` or a `homeopathic` / `out_of_scope` scope flag (no nulls)
- [ ] Homeopathic products are flagged and not marked in scope
- [ ] Sunscreen, hand sanitizer, fluoride toothpaste, antiperspirant and dandruff shampoo are flagged out of scope
- [ ] `pipeline/reports/category-counts.md` committed with counts per category and flag
- [ ] 30-product spot check done, with result in the report
- [ ] Tests pass with `uv run pytest pipeline/tests/identity`

### How to check your work
Run `duckdb -c "SELECT otc_category, scope_flag, count(*) FROM 'data/silver/product.parquet' GROUP BY ALL ORDER BY 3 DESC"`. There should be no null rows. Look up Tylenol, Aleve, ZzzQuil and NyQuil and confirm they land in internal analgesics, internal analgesics, nighttime sleep aids and cough-cold. Search for an Arnica product and confirm it's homeopathic.

### Out of scope
- Uses classification, such as pain vs fever vs sleep (NOMI-047)
- Benchmarks within a category (NOMI-054)
- Showing the homeopathic state in the app (NOMI-030)

### Resources
- FDA OTC monographs: https://www.fda.gov/drugs/over-counter-otc-nonprescription-drugs/otc-monographsfda
- FDA NDC directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/

---

## NOMI-027: Build the app theme and core UI components with a gallery screen
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-011, NOMI-012

### Summary
Code the app's theme (colors, type, spacing) and eight core components from the Figma library, each with a screen-reader label, and add a gallery screen in the dev build that shows every component in every state.

### Why this matters
Every screen in Sprints 3 and 4 is assembled from these components. Building them once, with accessibility included, keeps the app consistent and saves rework. Our first users include older adults, so large text and screen readers must work from the start.

### What you will deliver
- `apps/mobile/src/theme/` with light and dark color tokens, type scale and spacing, matching the NOMI-012 Figma library
- Components in `apps/mobile/src/components/`: `ScoreBadge`, `TierLabel`, `DimensionBar`, `CitationChip`, `ProfileChip`, `WarningBanner`, `Button`, `Card`
- A gallery screen at `apps/mobile/src/app/dev/gallery.tsx`, reachable in the dev build
- Screenshots of the gallery in light and dark mode attached to the PR

### Before you start
- **Design tokens**: named values (like `color.tier.good` or `space.md`) that the code reads instead of hard-coded colors and sizes. They come from the NOMI-012 Figma library.
- **Tier**: the word and color band for a score range (for example "Lower risk"). Names come from NOMI-012 and NOMI-014. Tiers must be distinguishable without color, using the word and an icon or pattern.
- **Dynamic Type**: the iOS setting for larger text. Android has an equivalent font scale. React Native `Text` scales with it by default; your job is to make layouts not break when it does.
- **Screen reader**: VoiceOver (iOS) and TalkBack (Android) read out `accessibilityLabel` and `accessibilityRole`.
- **Risk dimension / citation / profile**: see the glossary in `docs/nomi-101.md`.
- The app lives in `apps/mobile` (NOMI-011). If NOMI-011 hasn't merged, branch from its PR. If NOMI-012 isn't published, ask its owner for the current Figma file and mark any guessed values with `// TODO(NOMI-012)`.

### Steps
1. Create `apps/mobile/src/theme/tokens.ts` with color, type and spacing tokens copied from Figma, for light and dark. Export a `useTheme()` hook that picks the set from `useColorScheme()`.
2. Define a type scale (for example `title`, `body`, `caption`) as text styles with no fixed heights, so text can grow.
3. Build `ScoreBadge`: props `score: number | null` and `tier`. Show the number, the tier word and the tier icon. `null` shows a dash with the label "No score".
4. Build `TierLabel`: tier word plus icon, never color alone.
5. Build `DimensionBar`: props `label`, `points` (points taken off), `max`. Show the label and a numeric value next to the bar.
6. Build `CitationChip`: props `source` (for example "FDA label: Warnings") and `onPress`.
7. Build `ProfileChip`: props `label` (for example "Me, 30") and `selected`.
8. Build `WarningBanner`: props `title`, `body` and `variant` (`hardStop`, `info`). It must have an icon and a heading, not just a color.
9. Build `Button` (primary, secondary) and `Card`.
10. Give every component an `accessibilityLabel` that reads naturally, for example ScoreBadge reads "Safety score 42 out of 100, higher risk". Set `accessibilityRole` on interactive ones.
11. Create the gallery screen showing every component in every state (each tier, null score, long text, both banner variants, selected and unselected chips).
12. Test the gallery at the largest system text size on one iPhone and one Android phone. Fix any clipped or overlapping text.
13. Compare the gallery side by side with Figma and fix differences. Attach light and dark screenshots to the PR.

### Done when
- [ ] Theme tokens for light and dark exist and no component uses a hard-coded color
- [ ] All eight components exist in `apps/mobile/src/components/`
- [ ] Every component has a screen-reader label, checked with VoiceOver or TalkBack
- [ ] Gallery screen shows every component in every state and matches Figma (reviewed by the NOMI-012 owner)
- [ ] No clipped text at the largest system text size on iOS and Android
- [ ] Light and dark screenshots attached to the PR

### How to check your work
Open the gallery in the dev build. Turn on VoiceOver or TalkBack and swipe through: every element should be read out with a meaningful label. Switch the phone to grayscale (in accessibility settings): you should still be able to tell every tier apart.

### Out of scope
- The result screen layout (NOMI-029)
- The breakdown section with tappable citations (NOMI-041)
- The full accessibility pass across every screen (NOMI-070)

### Resources
- Expo docs: https://docs.expo.dev
- React Native accessibility: https://reactnative.dev/docs/accessibility
- WCAG contrast guidance: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html
- Figma library from NOMI-012 (link in that issue)

---

## NOMI-028: Build the onboarding and profile screens
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-013, NOMI-016

### Summary
Build the onboarding flow that asks who the user is scanning for, their age band and optional health details, in `apps/mobile/src/app/onboarding/`. It must take under a minute, need no account, and be skippable.

### Why this matters
The same medicine can be fine for a 30-year-old and risky for a 75-year-old, so scores depend on who the medicine is for. Onboarding is how we learn that. If it's slow or feels invasive, people skip it and get generic scores. This ticket is UI only: saving profiles securely on the device is NOMI-039.

### What you will deliver
- Screens in `apps/mobile/src/app/onboarding/`: who you're scanning for, age band, optional sex and pregnancy or breastfeeding, optional conditions, optional medication types, and a done screen
- A `Profile` TypeScript type in `apps/mobile/src/storage/profile.ts` and an in-memory store holding the result for this session
- A short test log in the PR: 3 people, their completion times

### Before you start
- **Persona**: a type of person we score for: adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding. Defined in `docs/scoring/dimensions.md` (NOMI-016).
- **Profile**: one person's details on the phone: persona plus optional conditions (for example high blood pressure) and medication types (for example blood thinners).
- **Condition and medication modifiers**: the lists of conditions (hypertension, kidney disease, liver disease, glaucoma, enlarged prostate and others) and medication types (anticoagulants, MAOIs/SSRIs and others) from NOMI-016. Show them in plain words, for example "High blood pressure", not "hypertension". Use vocabulary from NOMI-022 if it's available.
- Privacy rule: profile data never leaves the phone (ADR-0002). Don't add any analytics or logging of answers.
- Use the components from NOMI-027 if merged; otherwise use plain React Native components and leave `// TODO(NOMI-027)`.
- Follow the NOMI-013 wireframes. If NOMI-016 hasn't merged, use the lists above and mark them `// TODO(NOMI-016)`.

### Steps
1. Define `Profile` in `apps/mobile/src/storage/profile.ts`: `{ relation: "me" | "child" | "olderAdult"; ageBand; sex?: "female" | "male"; pregnant?: boolean; breastfeeding?: boolean; conditions: string[]; medicationTypes: string[] }`. Use ids from NOMI-016 for conditions and medication types.
2. Build screen 1, "Who are you scanning for?": me, a child, an older adult. Include a "Skip" button.
3. Build screen 2, age band. Show only bands that fit the relation (a child shows under 2, 2-5, 6-11, 12-17).
4. Build screen 3 (optional): sex, and pregnancy or breastfeeding only when relevant. Every question has a "Prefer not to say" choice.
5. Build screen 4 (optional): conditions as a multi-select list in plain words.
6. Build screen 5 (optional): current medication types as a multi-select list in plain words.
7. Build the done screen with a one-line summary of the profile and a button that opens the camera.
8. Make "Skip" on any screen finish onboarding with the default profile: adult 18-64, no conditions, no medications.
9. Save the result in an in-memory store (for example a React context) so the result screen can read it this session.
10. Add a one-line note on the first screen saying details stay on this phone.
11. Time 3 people outside the Visualization team going through onboarding from start to done. Record the times in the PR.

### Done when
- [ ] All five question screens plus the done screen exist in `apps/mobile/src/app/onboarding/`
- [ ] Every screen can be skipped, and skipping defaults to adult 18-64
- [ ] Conditions and medication types come from the NOMI-016 lists
- [ ] No network request is made during onboarding (checked in the dev tools network tab)
- [ ] 3 people complete onboarding in under 60 seconds each, with times in the PR

### How to check your work
Go through onboarding three ways: skip on screen 1, choose "a child, 6-11" with nothing else, and choose "an older adult, 65+" with high blood pressure and blood thinners. Log the resulting `Profile` object each time and check it matches what you chose.

### Out of scope
- Encrypted storage, multiple saved profiles and "delete all my data" (NOMI-039)
- Profile switcher on the result screen (NOMI-061)
- Scoring for the profile (NOMI-060)

### Resources
- Expo Router: https://docs.expo.dev/router/introduction/
- Wireframes from NOMI-013 (link in that issue)
- Personas and modifiers: `docs/scoring/dimensions.md`

---

## NOMI-029: Build result screen v1 from the reference products
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-015, NOMI-027 (same sprint)

### Summary
Build the first version of the result screen in `apps/mobile/src/app/result/`, rendering all five hand-made reference products: score with tier word and who it's for, product name, ingredients, explanation, hard-stop banner and disclaimer.

### Why this matters
The result screen is what users see after every scan, and it's the center of the demo. Building it now against hand-verified data settles the layout before real data arrives in Sprint 3, so later tickets only add sections instead of redesigning.

### What you will deliver
- A result screen in `apps/mobile/src/app/result/` that takes a product id and renders it
- A loader `apps/mobile/src/lib/examples.ts` that reads the five reference records from `packages/schema/examples/`
- Screenshots of all five products in the PR, next to the Figma frames

### Before you start
- **Reference products** (NOMI-015): Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil and a store-brand diphenhydramine, hand-researched and stored in `packages/schema/examples/`. They include ingredients, mandated warnings and draft expected scores for three profiles.
- **Tier word**: the label for a score range (from NOMI-012/NOMI-014). The score must never rely on color alone.
- **Hard stop**: a rule that makes a product red no matter what, for example the label says "do not use" for this persona. Shown as a banner above the score.
- **Disclaimer**: use the text from the root README: "Nomi provides information from public FDA data and published criteria. It is not medical advice."
- Components come from NOMI-027 (same sprint). Until they merge, use simple placeholders with the same props and swap them in when ready.
- If NOMI-015 hasn't merged, use its PR branch.

### Steps
1. Write `apps/mobile/src/lib/examples.ts` that imports the five JSON files and returns them typed with the generated `product` / `score-record` types from `packages/schema/generated/`.
2. Create the route `apps/mobile/src/app/result/[id].tsx`.
3. Add the top section: `ScoreBadge` with the tier word, and a line saying who it's for (for example "For: adult 18-64"). Read the profile from the onboarding store (NOMI-028) if available; otherwise default to adult.
4. Add the product section: brand name, generic name, and each active ingredient with strength and unit (for example "Acetaminophen 500 mg").
5. Add the explanation: the explanation text from the record.
6. Add `WarningBanner` (hard stop) above the score when the record has a hard stop for the current profile. Example: a sleep aid for a child 6-11.
7. Add the disclaimer at the bottom of the screen.
8. Add a temporary dev menu entry listing the five products so each can be opened without scanning.
9. Compare each product's screen against the Figma frame and fix differences.
10. Check at the largest text size and with VoiceOver or TalkBack that the score, tier and who-it's-for are read out in order.

### Done when
- [ ] All five reference products render on the result screen without errors
- [ ] Each shows score with tier word, who it's for, product name, ingredients with strengths, explanation and disclaimer
- [ ] The hard-stop banner shows for at least one product and profile combination
- [ ] Screens match Figma for all five products, with screenshots in the PR, reviewed by a Visualization teammate

### How to check your work
Open each product from the dev menu. Compare the ingredients and strengths with the JSON file in `packages/schema/examples/`. Switch the default profile to child 6-11 in code and confirm the hard-stop banner appears on the products whose labels say not to use them for that age.

### Out of scope
- Risk-dimension breakdown and citations (NOMI-041)
- Benchmark and profile switcher (NOMI-061)
- Alternatives and comparison (NOMI-062)
- Preliminary, homeopathic and not-found states (NOMI-030)
- Real product data from the database (NOMI-040)

### Resources
- Expo Router dynamic routes: https://docs.expo.dev/router/introduction/
- Reference products: `packages/schema/examples/`
- Figma frames from NOMI-013 (link in that issue)

---

## NOMI-030: Wire scan navigation and every result state to fixture data
**Team:** visualization | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-011

### Summary
Connect the camera to the result screen and build every outcome a scan can have: scored, preliminary, homeopathic, not found and invalid barcode. Use fixture data so each state can be reached in the dev build.

### Why this matters
Not every scan ends in a clean score. Some barcodes aren't in our data, some products are homeopathic, some ingredients only have preliminary ratings, and sometimes the camera misreads. If the app shows a blank screen or a wrong score in these cases, people stop trusting it. The demo also shows the homeopathic and not-found states on purpose.

### What you will deliver
- Navigation from camera to haptic to result in `apps/mobile/src/app/`
- A screen or variant for each state: scored, preliminary, homeopathic, not found, invalid barcode
- `apps/mobile/src/fixtures/scanFixtures.ts` mapping test barcodes to each state
- A dev menu entry that opens each state without scanning

### Before you start
- **Scored**: a full score is available. Uses the result screen from NOMI-029.
- **Preliminary**: we know the product's ingredients and label warnings, but not all of its ingredients have reviewed ratings. Show what we know, clearly labeled "Preliminary".
- **Homeopathic**: the product is marketed as unapproved homeopathic. Show "Not evaluated by FDA for safety or effectiveness" and no score (rule from NOMI-026).
- **Not found**: the barcode is valid but isn't in our data, or isn't a drug barcode.
- **Invalid barcode**: the check digit or length is wrong, which usually means a misread. Offer to scan again.
- The barcode parser `apps/mobile/src/lib/barcode.ts` (NOMI-007) returns statuses `ok`, `invalid_check_digit`, `bad_length` and `no_ndc`. If it hasn't merged, write a stub with the same signature that returns fixture results.
- The camera scanner is from NOMI-011.

### Steps
1. Define a `ScanOutcome` type: `{ state: "scored" | "preliminary" | "homeopathic" | "notFound" | "invalidBarcode"; productId?: string; barcode: string }`.
2. Write `resolveScan(barcode: string): ScanOutcome`. Call `ndcCandidates()`. Map `invalid_check_digit` and `bad_length` to `invalidBarcode`, `no_ndc` to `notFound`, and `ok` to a fixture lookup.
3. Create `scanFixtures.ts` with at least one barcode per state. Use real barcodes for the five reference products (scored) and make up clearly fake ones for the other states.
4. On a successful camera read: trigger a haptic, pause the camera so it doesn't read again, and navigate to the result route with the outcome.
5. Build the preliminary variant of the result screen: a "Preliminary" label, the ingredient list and label warnings, and a sentence explaining that the full score isn't ready.
6. Build the homeopathic screen: product name, the "Not evaluated by FDA for safety or effectiveness" message, and no score.
7. Build the not-found screen: the barcode digits, a "We don't have this product yet" message, and buttons to scan again or search (the search button can be disabled until NOMI-063).
8. Build the invalid-barcode screen: "We couldn't read that barcode" and a scan-again button.
9. Make back navigation from any state return to a live camera.
10. Add a dev menu listing every fixture so each state opens without scanning.
11. Test the flow on one iPhone and one Android phone.

### Done when
- [ ] Camera to haptic to result navigation works on iPhone and Android
- [ ] All five states have screens and are reachable in the dev build, both by scanning a fixture barcode and from the dev menu
- [ ] Homeopathic and not-found states never show a score
- [ ] Going back from any state returns to a working camera
- [ ] PR includes a screenshot of each state

### How to check your work
Scan a reference product box: you should feel the haptic and see its result. Print a barcode with a wrong last digit (or type one through the dev menu): you should see the invalid-barcode screen. Scan a non-drug barcode such as a cereal box: you should see not found.

### Out of scope
- Real database lookup (NOMI-040)
- Manual barcode entry and name search (NOMI-063)
- Result screen content for scored products (NOMI-029)

### Resources
- VisionCamera code scanning: https://react-native-vision-camera.com/docs/guides/code-scanning
- Expo Haptics: https://docs.expo.dev/versions/latest/sdk/haptics/
- Expo Router: https://docs.expo.dev/router/introduction/

---

## NOMI-031: Build the rule-based label extractor
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-017, NOMI-023 (same sprint)

### Summary
Write `pipeline/src/nomi_pipeline/extract/rules.py`, which uses rules and text patterns to pull mandated warnings, age limits, maximum daily dose, dosing interval, and allergens and dyes from each label's Drug Facts sections, with unit tests.

### Why this matters
Many label facts use predictable, FDA-required wording, so rules can extract them cheaply and exactly. The rules also act as an independent second opinion on the LLM extractor (NOMI-032): where both agree, we accept the value automatically in NOMI-045. Missing a mandated warning could mean missing a real risk, so recall must be very high.

### What you will deliver
- `pipeline/src/nomi_pipeline/extract/rules.py` with `extract_rules(sections: list[Section]) -> RuleExtraction`
- Unit tests in `pipeline/tests/extract/test_rules.py`, including a recall test on the NOMI-017 fixtures
- A recall figure for mandated warnings in the PR description

### Before you start
- **Mandated warning**: warning text FDA requires on certain OTC products, such as "Liver warning" on acetaminophen and "Stomach bleeding warning" on NSAIDs. The full list, wording variants and mapped risk dimensions are in `pipeline/knowledge/mandated_warnings.yaml` (NOMI-017).
- **Recall**: of all mandated warnings actually present, the share we found. At least 98% on 50 fixtures means at most one miss.
- **Drug Facts sections**: the label split into Warnings, Directions, Inactive ingredients and so on, in `data/bronze/spl_sections.parquet` (NOMI-023, same sprint). Until it merges, run against the 50 snippets in `pipeline/tests/fixtures/warnings/` (NOMI-017) and the five reference labels from DailyMed.
- **Age limit**: text like "children under 12 years: do not use" or "ask a doctor" for an age band.
- **Maximum daily dose**: text like "do not take more than 6 caplets in 24 hours". **Dosing interval**: text like "every 4 to 6 hours".
- **Allergens and dyes**: inactive ingredients relevant to allergies, such as FD&C Yellow No. 5 (tartrazine) and other FD&C and D&C color additives. Agree the full list with the Data Analysis lead and keep it in `pipeline/knowledge/allergens.yaml`.
- Output field names should match the label extraction schema being written in NOMI-032 (`packages/schema/schemas/`). Agree the names with the NOMI-032 owner on day one so NOMI-045 can merge the two.

### Steps
1. Define `RuleExtraction` as a Pydantic model: `mandated_warnings: list[str]` (catalogue ids), `age_limits: list[AgeLimit]` (`min_age_years`, `max_age_years`, `action` such as `do_not_use` or `ask_doctor`), `max_daily_dose: Dose | None` (`amount`, `unit`, `per_hours`), `dosing_interval_hours: tuple[float, float] | None`, `allergens: list[str]`, `dyes: list[str]`, and `evidence` (the matched text for every field).
2. Load `mandated_warnings.yaml`. For each warning, compile case-insensitive patterns from its wording variants. Search Warnings and its child sections.
3. Write the recall test: run on all 50 fixtures in `pipeline/tests/fixtures/warnings/` and compare with the expected warning ids. Print every miss.
4. Fix patterns until recall is at least 98%. Add a short note in the PR for any fixture that can't be matched by a rule.
5. Write age-limit patterns over Directions and Warnings: "children under N years", "adults and children N years and over", "do not use", "ask a doctor". Normalize to years.
6. Write maximum daily dose patterns over Directions: "do not take more than N <unit> in 24 hours", "do not exceed N doses in 24 hours". Capture amount, unit and the hour window.
7. Write dosing interval patterns: "every N hours", "every N to M hours".
8. Match inactive ingredients against `pipeline/knowledge/allergens.yaml` for allergens and dyes.
9. Store the matched text for every extracted value in `evidence`, so a reviewer can see why.
10. Add unit tests for each field with at least 5 real examples per field, including tricky ones (doses written as words, ranges, multiple age bands).
11. Run on all labels in `spl_sections.parquet` (once available) and note in the PR how many labels have each field found.

### Done when
- [ ] `extract_rules` returns all five field groups with evidence text
- [ ] Mandated-warning recall at least 98% on the NOMI-017 fixtures, shown by a passing test
- [ ] At least 5 unit test cases each for age limits, max daily dose, dosing interval, and allergens and dyes
- [ ] Field names agreed with the NOMI-032 owner
- [ ] Tests pass with `uv run pytest pipeline/tests/extract`

### How to check your work
Run the extractor on Tylenol Extra Strength. You should get the Liver warning, an adult maximum daily dose matching the label, a dosing interval, and an age limit for children under 12. Run it on Aleve: you should get the Stomach bleeding warning and the Heart attack and stroke warning. Compare both against the reference records in `packages/schema/examples/`.

### Out of scope
- LLM extraction of free-form fields such as ask-a-doctor conditions (NOMI-032)
- Merging rules and LLM output, and the full run (NOMI-045)
- Splitting labels into sections (NOMI-023)

### Resources
- Mandated warning catalogue: `pipeline/knowledge/mandated_warnings.yaml`
- FDA OTC monographs: https://www.fda.gov/drugs/over-counter-otc-nonprescription-drugs/otc-monographsfda
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Pydantic: https://docs.pydantic.dev

---

## NOMI-032: Build LLM label extraction v1 and run it on 200 labels
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-002, NOMI-016

### Summary
Write `pipeline/src/nomi_pipeline/extract/llm.py`, which sends label text to Claude and gets back structured fields in a fixed schema. Define that schema in `packages/schema/`, run it on 200 labels across categories, and measure cost per label.

### Why this matters
Some label facts, such as which conditions to ask a doctor about or which drug classes interact, are worded too differently across labels for rules. An LLM can read them reliably into a fixed format. This runs offline only. Its output is never shown to users directly: it's checked against the rules (NOMI-031) and by people (NOMI-045) first. We have no budget, so cost must be measured and kept low.

### What you will deliver
- A label extraction JSON Schema in `packages/schema/schemas/` with generated types
- `pipeline/src/nomi_pipeline/extract/llm.py`, run with `uv run pipeline extract llm --limit 200`
- Output for 200 labels in `data/silver/llm_extractions.parquet` (not committed)
- A short cost report in the PR: tokens and cost per label, and projected cost for all in-scope labels

### Before you start
- **Extraction schema fields**: uses, age limits, max dose, ask-a-doctor conditions, interacting drug classes, do-not-use conditions, pregnancy, allergens, mandated warnings.
- **Ask-a-doctor conditions**: the "Ask a doctor before use if you have..." list, such as high blood pressure or glaucoma. Map them to the condition ids in `docs/scoring/dimensions.md` (NOMI-016).
- **Interacting drug classes**: for example "Ask a doctor or pharmacist before use if you are taking a blood thinner". Map to the medication-type ids in NOMI-016.
- **Structured output**: making the model return JSON that matches a schema. With Claude, give it a tool whose input schema is your extraction schema and require the tool call, or use the structured outputs feature if the chosen model supports it. Check docs.anthropic.com.
- **Message Batches API**: Anthropic's API for sending many requests at once at a lower price, with results returned within 24 hours.
- **Provenance**: a record of how each output was made: model id, prompt version (a hash of the prompt text), and date. Required by the "every number must be explainable" rule in `docs/nomi-101.md`.
- Input text: Drug Facts sections from `data/bronze/spl_sections.parquet` (NOMI-023). If it isn't ready, download the 200 labels from DailyMed and send the Drug Facts text directly.
- If NOMI-002 hasn't merged, add the extraction schema in your PR alongside the others. If NOMI-016 hasn't merged, use its draft lists.
- API key: get it from a cofounder and keep it in the `ANTHROPIC_API_KEY` environment variable. Never commit it.

### Steps
1. Write the extraction schema in `packages/schema/schemas/`. Each field is a list or nullable value. Each extracted item carries `evidence`: the exact label sentence it came from. Agree field names with the NOMI-031 owner.
2. Run codegen so the Pydantic model and TypeScript type exist in `packages/schema/generated/`.
3. Write the prompt in `pipeline/src/nomi_pipeline/extract/prompts/label_v1.md`. Tell the model to extract only what the label says, to quote evidence, and to return empty lists when a field isn't on the label. Include the allowed condition and medication-type ids.
4. Pick 200 labels across categories: at least 20 each from pain/fever, allergy, sleep, cough/cold and digestive, and the rest from other categories. Save the list of set ids to `pipeline/tests/fixtures/llm_sample_200.csv`.
5. Pilot on 10 labels with single requests. Read every output against its label and fix the prompt.
6. Implement the batch run: build one request per label, submit through the Message Batches API, poll until done, and parse the results.
7. Validate every response with the Pydantic model. Store failures with the set id and error, don't drop them silently.
8. Write `data/silver/llm_extractions.parquet` with `set_id`, `version`, the extracted fields, `model`, `prompt_hash`, `run_at`, `input_tokens`, `output_tokens`.
9. Compute cost per label from token counts and the published batch price for the model used.
10. Project the cost for all in-scope labels: count in-scope labels from NOMI-026 (or all OTC labels if it's not ready) times cost per label. Write the numbers in the PR.
11. If the projection is over $50, try a smaller model or shorter input (only the needed sections) and report both options.

### Done when
- [ ] Extraction schema with all nine fields merged in `packages/schema/schemas/`, with generated types
- [ ] 200 labels extracted across categories, with model id and prompt hash recorded on every row
- [ ] Validation failure count reported in the PR
- [ ] Cost per label and projected cost for all in-scope labels reported in the PR
- [ ] Projected cost for all in-scope labels under $50
- [ ] No API key in the repo (`git grep -i "sk-ant"` returns nothing)

### How to check your work
Pick NyQuil and Aleve from the 200. Compare the extracted ask-a-doctor conditions and interacting drug classes to the labels on DailyMed line by line. Every extracted item should have evidence text that appears word for word in the label. Then check that a label with no pregnancy section has an empty pregnancy field, not invented text.

### Out of scope
- Rule-based extraction (NOMI-031)
- Merging with rules, human review and running on every label (NOMI-045)
- Classifying uses into the uses taxonomy (NOMI-047)

### Resources
- Anthropic API docs (tool use, structured outputs, Message Batches): https://docs.anthropic.com
- JSON Schema: https://json-schema.org
- Pydantic: https://docs.pydantic.dev
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/

---

## NOMI-033: Build the FAERS drug-name matcher with a labeled evaluation set
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S2 | **Depends on:** NOMI-019

### Summary
Write `pipeline/src/nomi_pipeline/evidence/name_matcher.py`, which maps free-text FAERS drug names to our ingredients, and hand-label 500 real FAERS drug-name strings to measure it. Precision must be at least 97% on the held-out half.

### Why this matters
FAERS (FDA's adverse event reports) records drug names as typed by reporters: brand names, salts, doses and misspellings, such as "TYLENOL EXTRA STR 500MG" or "DIPHENHYDRAMIN HCL". Signals are only as good as the mapping from those strings to ingredients. A wrong match attaches someone else's adverse events to our ingredient, so we care most about precision.

### What you will deliver
- `pipeline/src/nomi_pipeline/evidence/name_matcher.py` with `match(name: str) -> MatchResult`
- `pipeline/tests/fixtures/faers_names_labeled.csv`: 500 hand-labeled strings, split into tuning and held-out halves
- `pipeline/tests/evidence/test_name_matcher.py` with an evaluation test
- Precision and recall on the held-out half in the PR

### Before you start
- **FAERS**: FDA Adverse Event Reporting System. Drug names are in the DRUG table's `drugname` column (and sometimes an active ingredient column). See `docs/nomi-101.md`.
- **RxNorm / RxCUI**: NLM's drug vocabulary and its ids. It lists brand names, synonyms and the ingredients they contain.
- **UNII**: FDA's ingredient id, our main ingredient key.
- **Crosswalk**: `data/silver/ingredient_crosswalk.parquet` (NOMI-019) links ingredient RxCUI to UNII, with synonyms. If NOMI-019 hasn't merged, build a small crosswalk by hand for the 30 ingredients in NOMI-034 and NOMI-035 and use that.
- **Precision**: of the strings we matched, the share matched correctly. **Recall**: of the strings that should match, the share we matched.
- **rapidfuzz**: a Python library for fast fuzzy string matching (handles misspellings).
- **Held-out half**: labeled strings you never look at while tuning, used only for the final score, so the number isn't inflated.
- **Combination names**: one string naming a product with several ingredients, such as "NYQUIL" (acetaminophen, dextromethorphan, doxylamine). It must map to all of them.
- FAERS strings: from `data/bronze/faers/drug.parquet` (NOMI-024, same sprint, not a dependency). If it isn't ready, fetch one quarter with `uv run pipeline fetch faers` or download it from the FAERS page and read the DRUG file directly.
- Salts: decide with the NOMI-019 owner whether salts like "diphenhydramine hydrochloride" map to the base ingredient. Use the same rule as the crosswalk.

### Steps
1. Sample 500 distinct `drugname` strings: 250 from the most frequent strings that look OTC-related, and 250 at random from the rest, so both easy and messy strings are included.
2. Hand-label each one in `faers_names_labeled.csv` with columns: `drugname`, `expected_uniis` (semicolon-separated, empty if not an OTC ingredient we track), `notes`, `split`. Ask a teammate to label 50 of the same strings and resolve any disagreements.
3. Assign `split` randomly with a fixed seed: 250 `tune`, 250 `holdout`. Don't look at holdout results until step 9.
4. Write a `normalize(name)` function: uppercase, strip doses (for example `500MG`, `10 MG/ML`), dosage forms ("TABLET", "CAPLET"), punctuation and extra spaces.
5. Implement stage 1, exact match: the normalized string equals an ingredient name or synonym in the crosswalk.
6. Implement stage 2, RxNorm synonyms: brand names and synonyms from RxNorm that map to one or more ingredients. Combination brands expand to all ingredients.
7. Implement stage 3, fuzzy match with rapidfuzz against the synonym list, only if stages 1 and 2 fail. Accept only above a score threshold.
8. Tune the threshold on the `tune` half: pick the lowest threshold that keeps precision at or above 97%. Record the value in the code with a comment.
9. Run on the `holdout` half once. Report precision and recall overall and per stage in the PR.
10. Return `MatchResult(uniis: list[str], method: "exact" | "synonym" | "fuzzy" | "none", score: float | None)`.
11. Write the evaluation as a test that fails if holdout precision drops below 97%.

### Done when
- [ ] 500 strings hand-labeled, with 50 double-labeled and disagreements resolved
- [ ] Matcher runs exact, then RxNorm synonyms, then rapidfuzz, in that order
- [ ] Combination names expand to all their ingredients (tested with at least 5 combination products)
- [ ] Fuzzy threshold tuned on the `tune` half only
- [ ] Precision at least 97% on the held-out half, enforced by a test
- [ ] Precision and recall per stage reported in the PR

### How to check your work
Run `match("TYLENOL PM")` and confirm it returns acetaminophen and diphenhydramine. Run `match("IBUPROFIN 200MG")` and confirm ibuprofen via fuzzy match. Run `match("LISINOPRIL")` and confirm it returns no OTC ingredient. Then read 20 holdout false positives or misses and note the patterns in the PR.

### Out of scope
- Running the matcher over all FAERS rows (NOMI-046)
- Building the RxNorm to UNII crosswalk (NOMI-019)
- Signal detection (NOMI-053)

### Resources
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/index.html
- FAERS quarterly data files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- RapidFuzz: https://github.com/rapidfuzz/RapidFuzz
- Glossary: `docs/nomi-101.md`

---

## NOMI-034: Rate pain/fever and digestive ingredients in the knowledge base
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-016, NOMI-018

### Summary
Create one YAML file per ingredient for the pain/fever and digestive aisles, rating each ingredient's severity on every risk dimension for every persona, with a citation for every value.

### Why this matters
These ratings are what the score is built from. When the app tells a 70-year-old with high blood pressure that Aleve scores low and Tylenol scores high, it's because of the values in these files. The Tylenol vs Aleve comparison is also one of the key demo moments, so these two aisles go first.

### What you will deliver
- One file per ingredient in `pipeline/knowledge/ingredients/`, named by ingredient, e.g. `acetaminophen.yaml`, `naproxen.yaml`
- Files for: acetaminophen, ibuprofen, naproxen, aspirin, bismuth subsalicylate, calcium carbonate, magnesium hydroxide, aluminum hydroxide, famotidine, omeprazole, loperamide, senna, bisacodyl, polyethylene glycol 3350, docusate, simethicone
- A coverage note in the PR listing any ingredient from these aisles' barcodes (NOMI-020) that you didn't cover and why

### Before you start
- Read `docs/scoring/dimensions.md` (NOMI-016): it defines the risk dimensions, the 0-3 severity scale and the personas you'll rate.
- **Severity 0-3**: 0 means no meaningful risk on that dimension for that persona; 3 means serious risk. The criteria for each level are in the dimensions doc.
- **Persona**: adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding.
- **Condition modifier**: a rule like "naproxen, kidney dimension, +1 severity if the user has kidney disease."
- **Sources you may cite**: the product's FDA label (mandated warnings and Drug Facts sections), STOPP/START and ACB in `pipeline/knowledge/criteria/` (NOMI-018). Get label text from DailyMed.
- The file format is the `ingredient-dimensions` schema in `packages/schema/schemas/` (NOMI-002). If it hasn't merged, follow the example in `packages/schema/examples/`.

### Steps
1. For each ingredient, open two or three of its OTC labels on DailyMed and note every mandated warning, "Do not use", "Ask a doctor before use if you have" and "Stop use" item.
2. Map each warning to a risk dimension using `pipeline/knowledge/mandated_warnings.yaml` (NOMI-017). Example: "Stomach bleeding warning" maps to GI bleeding.
3. Check `pipeline/knowledge/criteria/` for STOPP/START and ACB entries that apply, mainly for the 65+ persona.
4. Set a severity for every dimension and persona. Write 0 explicitly where there's no risk, so we know it was considered.
5. Add condition modifiers where the label or criteria call them out (e.g. NSAIDs with high blood pressure, kidney disease, blood thinners).
6. Attach a citation to every non-zero value: source name, document or label set id, section, and URL.
7. Run the schema validation (`uv run pytest pipeline/tests/knowledge`) and fix any errors.
8. Ask a second Data Analysis member to check five random values against their sources.

### Done when
- [ ] All 16 ingredient files exist and pass schema validation
- [ ] Every non-zero severity and every modifier has a citation
- [ ] Second-person spot check of five values done, with results in the PR
- [ ] Coverage note added to the PR

### How to check your work
Pick Tylenol and Aleve. Using only your files, write down which dimensions each would lose points on for a 70-year-old with high blood pressure. Aleve should show GI bleeding, blood pressure and kidney; Tylenol should show liver (at high doses). If not, recheck your values.

### Out of scope
- Allergy, sleep, cough and cold ingredients (NOMI-035)
- Turning severities into points or scores (NOMI-049, NOMI-051)
- FAERS signals (NOMI-053)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-035: Rate allergy/sleep and cough/cold ingredients in the knowledge base
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-016, NOMI-018

### Summary
Create one YAML file per ingredient for the allergy, sleep and cough/cold aisles, rating each ingredient's severity on every risk dimension for every persona, with a citation for every value.

### Why this matters
These aisles hold the risks people know least about: first-generation antihistamines (like diphenhydramine in Benadryl and most "PM" sleep aids) in older adults, decongestants for people with high blood pressure, and acetaminophen hidden in combination cold products. Two demo moments come from here: Benadryl for a 30-year-old vs a 75-year-old, and the NyQuil duplicate-acetaminophen warning.

### What you will deliver
- One file per ingredient in `pipeline/knowledge/ingredients/`, named by ingredient, e.g. `diphenhydramine.yaml`, `pseudoephedrine.yaml`
- Files for: diphenhydramine, doxylamine, chlorpheniramine, brompheniramine, cetirizine, loratadine, fexofenadine, dextromethorphan, guaifenesin, pseudoephedrine, phenylephrine, oxymetazoline
- A coverage note in the PR listing any ingredient from these aisles' barcodes (NOMI-020) that you didn't cover and why

### Before you start
- Read `docs/scoring/dimensions.md` (NOMI-016): it defines the risk dimensions, the 0-3 severity scale and the personas you'll rate.
- **Severity 0-3**: 0 means no meaningful risk on that dimension for that persona; 3 means serious risk. The criteria for each level are in the dimensions doc.
- **Persona**: adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding.
- **Condition modifier**: a rule like "pseudoephedrine, blood pressure dimension, +1 severity if the user has high blood pressure."
- **First-generation antihistamine**: older antihistamines (diphenhydramine, doxylamine, chlorpheniramine, brompheniramine) that cause drowsiness and are anticholinergic. Second-generation ones (cetirizine, loratadine, fexofenadine) are much less sedating.
- **Anticholinergic / ACB scale**: drugs that block acetylcholine can cause confusion and memory problems, especially in older adults. The ACB scale rates drugs 0 to 3. Use the ACB values in `pipeline/knowledge/criteria/acb.yaml` (NOMI-018), not your own memory.
- **Decongestant**: shrinks swollen nasal blood vessels. Pseudoephedrine and phenylephrine are taken by mouth; oxymetazoline is a nasal spray, and its label limits use to a few days because of rebound congestion (map this to the rebound/overuse dimension).
- **Sources you may cite**: the product's FDA label (mandated warnings and Drug Facts sections), STOPP/START and ACB in `pipeline/knowledge/criteria/` (NOMI-018), and FDA announcements on fda.gov. Get label text from DailyMed. Don't use the AGS Beers Criteria; they're excluded by the license audit (NOMI-006).
- Phenylephrine efficacy: FDA has proposed removing oral phenylephrine as a nasal decongestant because evidence shows it doesn't work. Check the current status on fda.gov and cite the FDA page for the efficacy dimension.
- The file format is the `ingredient-dimensions` schema in `packages/schema/schemas/` (NOMI-002). If it hasn't merged, follow the example in `packages/schema/examples/` and the files already written for NOMI-034.

### Steps
1. For each ingredient, open two or three of its OTC labels on DailyMed (include at least one single-ingredient product and one combination product) and note every mandated warning, "Do not use", "Ask a doctor before use if you have", "When using this product" and "Stop use" item.
2. Map each warning to a risk dimension using `pipeline/knowledge/mandated_warnings.yaml` (NOMI-017). Examples: "marked drowsiness may occur" maps to sedation/falls; "do not use if you are now taking a prescription monoamine oxidase inhibitor (MAOI)" on dextromethorphan and decongestant labels maps to interactions.
3. Check `pipeline/knowledge/criteria/` for STOPP/START and ACB entries that apply, mainly for the 65+ persona. Expect entries for the first-generation antihistamines.
4. Check the pediatric directions on each label. Note where labels say "do not use" or "ask a doctor" for children under a given age, and set the child personas accordingly. Cough and cold product labels often restrict use in young children; use what the label says.
5. Set a severity for every dimension and persona. Write 0 explicitly where there's no risk, so we know it was considered.
6. Add condition modifiers where the label or criteria call them out. Examples: first-generation antihistamines with glaucoma or trouble urinating due to an enlarged prostate; decongestants with high blood pressure, heart disease, thyroid disease, diabetes or enlarged prostate; dextromethorphan and decongestants with MAOIs.
7. Attach a citation to every non-zero value: source name, document or label set id, section, and URL.
8. Run the schema validation (`uv run pytest pipeline/tests/knowledge`) and fix any errors.
9. Compare your files to the NOMI-034 files for consistency in how you apply the severity scale. Coordinate with the NOMI-034 owner on any differences.
10. Ask a second Data Analysis member to check five random values against their sources.

### Done when
- [ ] All 12 ingredient files exist and pass schema validation
- [ ] Every non-zero severity and every modifier has a citation
- [ ] Every ingredient in the allergy, sleep and cough/cold ground-truth barcodes (NOMI-020) is covered, or listed in the coverage note with a reason
- [ ] Second-person spot check of five values done, with results in the PR
- [ ] Coverage note added to the PR

### How to check your work
Pick Benadryl (diphenhydramine). Using only your file, write down which dimensions would lose points for a 30-year-old and for a 75-year-old. The 75-year-old should show higher severity on memory/thinking and sedation/falls. Then pick Sudafed (pseudoephedrine) for a 70-year-old with high blood pressure: the blood pressure dimension should go up through the condition modifier. If not, recheck your values.

### Out of scope
- Pain/fever and digestive ingredients, including acetaminophen in combination products (NOMI-034)
- Detecting duplicate ingredients across products, such as NyQuil plus Tylenol (NOMI-052)
- Turning severities into points or scores (NOMI-049, NOMI-051)
- FAERS signals (NOMI-053)
- Ingredients outside the demo aisles (NOMI-075)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- FDA OTC drug information: https://www.fda.gov/drugs/over-counter-otc-nonprescription-drugs
- Criteria data: `pipeline/knowledge/criteria/`
- Glossary and big picture: `docs/nomi-101.md`

---

# Sprint 3: Oct 30 to Nov 5

## NOMI-036: Run the rubric review session with our faculty partner and file the feedback as issues
**Team:** cofounders | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-005, NOMI-049 (same sprint)

### Summary
Hold a one-hour review of the draft scoring rubric with our pharmacy faculty partner (or, if no partner has signed on yet, with an internal panel), and turn every change they ask for into its own GitHub issue. The Data Analysis team uses these issues when it implements the rubric in Sprint 4.

### Why this matters
The rubric (`docs/rubric/v0.md`, NOMI-049) decides how many points each risk costs and so decides every score in the app. Changing it is cheap now, while it is still a document, and expensive after NOMI-051 turns it into code and test vectors in Sprint 4. A pharmacist's review is also what makes our scores credible to the demo audience and to future partners.

### What you will deliver
- A review packet sent to the reviewer at least 48 hours before the meeting: `docs/scoring/dimensions.md` (NOMI-016), the draft `docs/rubric/v0.md` (NOMI-049), and a one-page cover note with the questions you want answered
- One GitHub issue per requested change, labeled `rubric-review` and `team:data-analysis`, filed before Sprint 4 planning (Sprint 4 starts Nov 6)
- One tracking issue titled "Rubric v0 review feedback" that links every `rubric-review` issue, lists who attended, and states whether the review was clinical or internal
- A written credit agreement with the faculty partner (an email they have replied to agreeing to it), summarized in the tracking issue

### Before you start
- **Rubric**: the written rules that turn ingredient ratings into points and a 0-100 score. See the glossary in `docs/nomi-101.md`.
- **Risk dimension**, **persona**, **severity**, **hard stop**: see the glossary in `docs/nomi-101.md`. The reviewer needs `docs/scoring/dimensions.md` to understand them.
- **Faculty partner**: the pharmacy faculty member recruited in NOMI-005 (Mercer, UGA or PCOM Georgia). Check the NOMI-005 contact sheet for who said yes.
- NOMI-049 is in the same sprint. Agree a date with its owner on day one: you need a complete draft at least 48 hours before the meeting, so book the meeting for Nov 3 or Nov 4 and ask for the draft by Nov 1.
- If no faculty partner has signed on by Oct 30, run an internal review instead: both cofounders plus at least two Data Analysis members who did not write the rubric. Then file one extra issue, "Clinical review of rubric v0", in the post-demo milestone so the clinical review still happens.
- Do not put the reviewer's personal contact details in the public repo. Names and affiliations go in the tracking issue only if the reviewer agrees.

### Steps
1. Check the NOMI-005 contact sheet and decide on day one whether this is a clinical review (partner confirmed) or an internal review (no partner yet). Write the decision in the tracking issue.
2. Book a one-hour video or in-person meeting on Nov 3 or Nov 4. Send the calendar invite yourself and include a video link.
3. Write the one-page cover note (keep it in the shared drive, not the repo). Include: what Nomi is in two sentences, what the rubric is for, and 5 to 8 specific questions. Example questions: "Are the severity levels for NSAIDs in adults 65+ with high blood pressure reasonable?", "Should diphenhydramine be a hard stop for adults 65+ or a large deduction?", "Is the tier wording appropriate for a consumer app?", "Which dimension weights look wrong to you?"
4. Send the packet (dimensions doc, rubric draft, cover note) at least 48 hours before the meeting. Ask the reviewer to mark up the rubric directly or reply with comments.
5. Draft a credit proposal before the meeting. Suggested options to offer: named acknowledgment in the app's About screen, co-authorship on any paper that uses their review, and a description of the work for their students. Send it in writing and get a written yes.
6. Run the meeting. One cofounder leads, the other takes notes. Walk through the questions in order, then ask for anything else they would change. Spend the last 5 minutes on credit and on whether they will review a sample of scores in Sprint 5 (NOMI-073).
7. Within 24 hours, file one GitHub issue per requested change. Each issue has: what the reviewer asked for, the section of `docs/rubric/v0.md` it affects, the reviewer's reasoning, and a suggested priority (P0 if it changes a demo product's tier, P1 otherwise). Label it `rubric-review` and `team:data-analysis`.
8. Create the tracking issue, link every `rubric-review` issue, and record the attendees, the review type and the credit agreement.
9. Send the reviewer a thank-you email with the list of changes you filed so they can correct anything you misunderstood.
10. Bring the tracking issue to Sprint 4 planning so the NOMI-051 owner can pull the changes in.

### Done when
- [ ] Review packet sent at least 48 hours before the meeting (date recorded in the tracking issue)
- [ ] Meeting held for about one hour, with attendees listed in the tracking issue
- [ ] Every requested change filed as its own issue labeled `rubric-review`, all before Sprint 4 planning
- [ ] Tracking issue links every `rubric-review` issue
- [ ] Credit agreement confirmed in writing by the partner and summarized in the tracking issue (clinical review), or a "Clinical review of rubric v0" issue filed in the post-demo milestone (internal review)

### How to check your work
Open the tracking issue and click through every linked issue. Each one should make sense to someone who was not in the meeting: it names the rubric section and the change. Ask the NOMI-051 owner to read three of them and confirm they know what to change in code.

### Out of scope
- Finding a faculty partner (NOMI-005)
- Writing or editing the rubric itself (NOMI-049)
- Implementing the rubric and term tables (NOMI-051)
- Faculty review of real product scores (NOMI-073)
- The public methodology write-up (NOMI-077)

### Resources
- Product overview and glossary: `docs/nomi-101.md`
- Risk dimensions and personas: `docs/scoring/dimensions.md`
- Rubric draft: `docs/rubric/v0.md`

---

## NOMI-037: Raise barcode identity coverage to 95% with a regression fixture for every fix
**Team:** platform | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-025

### Summary
Fix the identity resolver so that at least 95% of our real-world ground-truth barcodes resolve to the correct product, and add a regression test case for every barcode you fix. The demo's blind scan depends on this.

### Why this matters
The demo opens with someone in the audience handing us a box we have never seen. If the barcode doesn't resolve, nothing else in the app matters. The NOMI-025 coverage report lists every miss with a cause, and most misses fall into a few fixable groups: store-brand labelers, barcodes that don't follow the usual drug format, and labels that have changed since the box was made.

### What you will deliver
- Fixes in the resolver module from NOMI-025 under `pipeline/src/nomi_pipeline/identity/`
- `pipeline/knowledge/barcode_overrides.csv`: a reviewed table linking barcodes that contain no NDC to the right product, with columns `barcode`, `ndc11`, `spl_set_id`, `matched_by`, `checked_by`, `note`
- `pipeline/tests/fixtures/identity_regression.csv` with one row per fixed barcode: `barcode`, `expected_ndc11`, `expected_spl_set_id`, `miss_category`, `fixed_in` (PR or commit)
- `pipeline/tests/identity/test_regression.py` that runs every row through the resolver
- An updated coverage report in `pipeline/reports/identity_coverage.md` showing the before and after numbers, with the remaining misses categorized

### Before you start
- **NDC** and **NDC11**: FDA's product code and our normalized 11-digit form. See the glossary in `docs/nomi-101.md`.
- **UPC-A and number system**: drug barcodes usually start with `3` followed by the 10-digit NDC. Barcodes starting with another digit carry no NDC that we can read directly, so the NOMI-007 parser returns `no_ndc` for them.
- **Labeler**: the company named on the label (the first segment of the NDC). Store brands are made by contract manufacturers, so the labeler is often not the store.
- **SPL set id**: the stable id of a DailyMed label across versions. See the glossary.
- **Stale label**: the box on the shelf was printed under an NDC or label version that FDA's current directory no longer lists.
- Inputs: the NOMI-025 coverage report and miss list, `pipeline/tests/fixtures/barcodes.csv` (NOMI-020, with Drug Facts photos in the shared drive), `data/bronze/ndc.parquet` (NOMI-009) and `data/bronze/spl_products.parquet` (NOMI-010).
- To judge "correct product" you need an expected NDC or set id for each barcode. If the NOMI-025 report doesn't have one for a miss, read it off the Drug Facts photo and add it to your regression row.

### Steps
1. Run the current resolver over `pipeline/tests/fixtures/barcodes.csv` and save the baseline coverage number and miss list. Confirm it matches the NOMI-025 report.
2. Group every miss by cause in a table in your PR: store-brand labeler, barcode without NDC (not starting with `3`), stale label or NDC, multiple candidates matched, wrong product chosen, data missing from FDA files, other. Count each group and fix the largest group first.
3. For barcodes that start with `3` but miss: check whether one of the three NDC11 candidates exists in the NDC directory under a different package, or only in an older DailyMed label version. If older versions explain it, let the resolver fall back to the most recent label that lists that NDC and mark the result `stale_label: true`.
4. For stale NDCs not in the current directory, check FDA's NDC directory page for its files of excluded or no-longer-listed products and confirm whether the NDC appears there. If it does, document the source in the PR before adding it as a fallback input.
5. For barcodes that don't start with `3`: first test whether digits 2 to 11 form an NDC that exists in the directory (some labelers print the NDC with a different leading digit). If not, match on labeler and product name: take the product name and store from the ground-truth row, search `ndc.parquet` for the same brand or generic name, dosage form and strength, and confirm the match against the Drug Facts photo. Add each confirmed match to `pipeline/knowledge/barcode_overrides.csv` with `matched_by` set to `labeler_name` and `checked_by` set to your name.
6. Make the resolver check `barcode_overrides.csv` for the raw barcode before returning `no_ndc`.
7. When several candidates match, fix the tie-break rule so it prefers the candidate whose label is OTC and whose package NDC exactly matches, and log any remaining conflicts.
8. Add every fixed barcode to `pipeline/tests/fixtures/identity_regression.csv`, then write `test_regression.py` so it loads the CSV and asserts the resolver returns the expected NDC11 and set id for each row.
9. Rerun the full coverage and update `pipeline/reports/identity_coverage.md`: total barcodes, resolved correctly, resolved to the wrong product, not resolved, and the cause of each remaining miss.
10. Ask a second Platform member to check 10 random override rows against the Drug Facts photos.

### Done when
- [ ] At least 95% of ground-truth barcodes in `barcodes.csv` resolve to the correct product, as shown in `pipeline/reports/identity_coverage.md`
- [ ] Every barcode fixed in this ticket has a row in `identity_regression.csv`
- [ ] `uv run pytest pipeline/tests/identity` passes, including the regression test
- [ ] Every row in `barcode_overrides.csv` has `matched_by` and `checked_by` filled in, and 10 rows were checked by a second person (noted in the PR)
- [ ] Every remaining miss is listed with a cause in the coverage report

### How to check your work
Run `uv run pytest pipeline/tests/identity`. Then pick five barcodes from the old miss list, run each through the resolver, and compare the returned product name and strength with the Drug Facts photo. All five should match. Finally, remove one row from the override file and confirm the regression test fails for that barcode.

### Out of scope
- Looking barcodes up on the phone (NOMI-040)
- Scanning new boxes outside the ground-truth set (NOMI-066)
- Category and scope flags (NOMI-026)
- Name search for boxes that won't scan (NOMI-058, NOMI-063)

### Resources
- FDA NDC directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- openFDA downloads: https://open.fda.gov/data/downloads/
- Glossary: `docs/nomi-101.md`

---

## NOMI-038: Build the SQLite dataset file (v1) with `uv run pipeline build` and publish it to R2
**Team:** platform | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-002, NOMI-025

### Summary
Add a `build` command to the pipeline that packs products, ingredients, label warnings, categories and scope flags into one SQLite file, `nomi.sqlite`, plus a manifest describing exactly how it was made, and publish both to R2. The phone app bundles this file and looks products up in it offline.

### Why this matters
Nomi works in airplane mode because the whole dataset ships inside the app as one file. This is the first version of that file. The app team (NOMI-040) needs it this sprint to show real products after a scan. Scores, benchmarks and alternatives are added to the same file in NOMI-056, so the table layout you choose here carries forward.

### What you will deliver
- `pipeline/src/nomi_pipeline/build/sqlite.py` and a `build` subcommand so `uv run pipeline build` works
- `data/build/nomi.sqlite` and `data/build/manifest.json` (gitignored, produced by the command)
- A schema file committed at `pipeline/src/nomi_pipeline/build/schema.sql` with every table and index
- A GitHub Actions workflow `.github/workflows/publish-dataset.yml` (manual trigger) that builds and uploads the file to R2
- Tests in `pipeline/tests/build/`
- A short section in `pipeline/README.md` on how to build and where the published file lives

### Before you start
- **NDC11**: the 11-digit normalized NDC. See the glossary in `docs/nomi-101.md`. The app looks products up by package NDC11.
- **UNII**: FDA's ingredient id and our ingredient key. See the glossary.
- **Scope flag / homeopathic flag**: from NOMI-026. Homeopathic products are shown as "Not evaluated by FDA for safety or effectiveness" and not scored; out-of-scope products (sunscreen, hand sanitizer and so on) are not scored.
- **R2**: Cloudflare's file storage, set up in NOMI-008. Team members have read-only credentials; write credentials are for CI only, which is why publishing runs in a GitHub Actions workflow.
- **Manifest**: a JSON file that records what went into the build, so any score can be traced to its data and code.
- Inputs: `data/silver/product.parquet` (NOMI-025, with category and scope columns from NOMI-026), `data/bronze/spl_ingredients.parquet` (NOMI-010), and label warnings from `data/silver/label_facts.parquet` (NOMI-045). NOMI-045 is in this sprint: if it isn't ready, build the warnings table from the rule extractor output (NOMI-031), and if that isn't available either, create the table empty so the schema is final.
- The `product` contract is in `packages/schema/schemas/` with Pydantic models in `packages/schema/generated/` (NOMI-002). Use the models to validate rows before writing.
- Agree table and column names with the NOMI-040 owner on day one, since they build a fixture database with the same layout.

### Steps
1. Write `schema.sql`. Suggested tables:
   - `package (ndc11 TEXT PRIMARY KEY, product_id TEXT NOT NULL)`
   - `product (product_id TEXT PRIMARY KEY, spl_set_id, spl_version, brand_name, generic_name, labeler, dosage_form, route, marketing_category, otc_category, scope_flag, is_homeopathic)`
   - `product_ingredient (product_id, unii, name, strength_value, strength_unit, is_active)`
   - `label_warning (product_id, warning_id, dimension, text, loinc_section)`
   - `category (otc_category TEXT PRIMARY KEY, label)`
   - `meta (key TEXT PRIMARY KEY, value TEXT)` holding the dataset version and build info
   Add indexes on `product_ingredient(product_id)` and `label_warning(product_id)`.
2. Write `build/sqlite.py`: read the input Parquet files with Polars, validate each product against the generated Pydantic model, and write rows into a new SQLite file at `data/build/nomi.sqlite`. Always build into a fresh file; never update an old one in place.
3. Sort rows by primary key before inserting and don't store build timestamps inside tables, so the same inputs give the same file.
4. Run `VACUUM` and `ANALYZE` at the end so the file is compact and SQLite has index statistics.
5. Write `data/build/manifest.json` with: `dataset_version` (start at `0.1.0`), `schema_version`, `code_commit` (from `git rev-parse HEAD`), `inputs` (path and SHA-256 of each input file), `row_counts` per table, `sqlite_sha256`, `size_bytes`, and `compressed_size_bytes` (gzip level 9).
6. Register `build` as a subcommand of the existing `pipeline` CLI from NOMI-008.
7. Write tests: the file opens, every table exists, every `package.product_id` exists in `product`, and the five reference products from `packages/schema/examples/` can be looked up by NDC11.
8. Write `.github/workflows/publish-dataset.yml` with a `workflow_dispatch` trigger. It runs the build and uploads `nomi.sqlite.gz` and `manifest.json` to `datasets/v<dataset_version>/` in the R2 bucket using the CI write credentials stored as repository secrets.
9. Time lookups on your laptop: run 1,000 random NDC11 lookups with Python's `sqlite3` and record the median and 99th percentile.
10. Time lookups on a mid-range Android phone (record the model in the PR) together with the NOMI-040 owner, using the dev build and the published file. Record the median and slowest of 100 lookups.
11. Document the build command and the published R2 path in `pipeline/README.md`.

### Done when
- [ ] `uv run pipeline build` produces `data/build/nomi.sqlite` and `data/build/manifest.json` on a fresh clone with data fetched
- [ ] Manifest contains dataset version, input hashes, code commit, row counts and compressed size
- [ ] The publish workflow has run once and the file is in R2 under `datasets/v0.1.0/`
- [ ] All five reference products look up by NDC11 in the tests
- [ ] Any NDC11 lookup takes under 10 ms on a mid-range Android phone, with the phone model and timings in the PR
- [ ] `uv run pytest pipeline/tests/build` passes

### How to check your work
Run `uv run pipeline build` twice and compare `sqlite_sha256` in the two manifests: they should match. Then open the file with `sqlite3 data/build/nomi.sqlite` and run `SELECT p.brand_name FROM package k JOIN product p USING (product_id) WHERE k.ndc11 = '<an NDC11 from the Tylenol reference product>';`. You should see the Tylenol product name.

### Out of scope
- Scores, term tables, benchmarks, alternatives and templates in the file (NOMI-056)
- Name search index (NOMI-058)
- Bundling the file in the app (NOMI-040)
- Size and index tuning beyond what is needed for 10 ms (NOMI-067)
- Running all pipeline stages in one command (NOMI-043)
- Release diff report (NOMI-059)

### Resources
- SQLite documentation: https://www.sqlite.org/docs.html
- Cloudflare R2: https://developers.cloudflare.com/r2/
- Polars: https://docs.pola.rs/
- Pydantic: https://docs.pydantic.dev/
- Data contracts: `packages/schema/README.md`

---

## NOMI-039: Store profiles encrypted on the device, with multiple profiles and "Delete all my data"
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-028, NOMI-003

### Summary
Build the storage layer that saves each user's profiles (who they scan for, age band, conditions, medication types) encrypted on the phone, lets them create, edit, delete and switch between profiles, and wipes everything with one "Delete all my data" action. No profile data ever goes over the network.

### Why this matters
A profile holds health information: conditions like high blood pressure and medications like blood thinners. Our rule is that health data never leaves the phone (ADR-0002, `docs/adr/0002-privacy.md`). Keeping it on the device means we never hold health data on a server, which keeps us out of scope of laws such as the FTC Health Breach Notification Rule and Washington's My Health My Data Act (the legal intake in NOMI-021 confirms how these apply). Every personalized score depends on reading the active profile from this storage.

### What you will deliver
- `apps/mobile/src/storage/profiles.ts` with functions `listProfiles()`, `getProfile(id)`, `saveProfile(profile)`, `deleteProfile(id)`, `getActiveProfileId()`, `setActiveProfileId(id)` and `deleteAllData()`
- A `Profile` TypeScript type in `apps/mobile/src/storage/types.ts`
- Onboarding and profile screens (NOMI-028) wired to this storage
- A "Delete all my data" button in the profile settings screen, with a confirmation dialog
- Unit tests in `apps/mobile/src/storage/__tests__/`
- A short privacy check report in the PR: how you inspected network traffic and what you saw

### Before you start
- **Profile** and **persona**: see the glossary in `docs/nomi-101.md`. Personas: adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding.
- **Conditions and medication types**: the lists in `docs/scoring/dimensions.md` (NOMI-016), for example hypertension, kidney disease, glaucoma, anticoagulants, MAOIs/SSRIs.
- **ADR-0002**: our privacy decision record. Read `docs/adr/0002-privacy.md` before writing code.
- **expo-secure-store**: an Expo library that stores small values in the iOS Keychain and Android Keystore, which are encrypted by the operating system. Check its size limit per value in the Expo docs.
- **Keychain items can survive uninstalling the app on iOS.** That is why "Delete all my data" must delete stored items explicitly instead of relying on uninstall.
- **Network inspection**: watching all traffic from the phone through a proxy such as mitmproxy (free) to confirm nothing sensitive is sent.
- If NOMI-028 hasn't merged, test the storage with a temporary debug screen that creates hardcoded profiles, then wire it into the real screens when NOMI-028 lands.

### Steps
1. Define the `Profile` type: `id` (random UUID), `label` (e.g. "Me", "Mom"), `persona` (one of the eight personas), `sex` (optional), `conditions` (array of ids from NOMI-016), `medicationTypes` (array of ids from NOMI-016), `createdAt`, `updatedAt`.
2. Install `expo-secure-store` with `npx expo install expo-secure-store`.
3. Store each profile as JSON under its own key, `profile.<id>`, plus an index key `profiles.index` holding the list of ids and a key `profiles.active` holding the active id. Set the `keychainAccessible` option so items are only readable when the device is unlocked and are not migrated to other devices; choose the option in the Expo docs and note your choice in the PR.
4. If a profile could exceed the per-value size limit, switch to this layout instead: generate a random key, store only the key in `expo-secure-store`, and store the encrypted profiles in a file. Write the decision in the PR.
5. Implement the functions listed above. `deleteProfile` removes the profile and, if it was active, makes the first remaining profile active. If no profiles remain, the app falls back to a default adult profile without storing anything.
6. Implement `deleteAllData()`: delete every profile key, the index and the active key, and anything else the app stores locally. Leave a clearly named place in the function for scan history, which NOMI-063 adds later.
7. Wire the onboarding screens (NOMI-028) to `saveProfile` and `setActiveProfileId`. Add create, edit, delete and switch actions to the profile screens.
8. Add the "Delete all my data" button with a confirmation dialog ("This deletes all profiles on this phone. This can't be undone."). After deleting, return the user to onboarding.
9. Write unit tests with a mocked secure store: create two profiles, switch active, edit one, delete one, then delete all and confirm storage is empty.
10. Search the app code for `fetch(`, `axios` and any analytics or crash-reporting packages. Confirm none receive profile fields. Do not add any such SDK.
11. Inspect network traffic: install mitmproxy on your laptop, route one iPhone or Android phone through it, then complete onboarding with a profile that has conditions and medication types, scan three boxes, and switch profiles. Save the list of requests and confirm none contain profile fields (search the captured traffic for the condition ids you chose).
12. Write the privacy check report in the PR: device, steps taken, number of requests captured, and the result.

### Done when
- [ ] Profiles are stored with `expo-secure-store` (or an encrypted file whose key is in it), never in plain AsyncStorage or plain files
- [ ] A user can create, edit, delete and switch between at least three profiles in the dev build
- [ ] "Delete all my data" removes every stored item; after it, relaunching the app shows onboarding
- [ ] Unit tests for the storage functions pass
- [ ] Network inspection during onboarding and scanning shows no profile data leaving the device, documented in the PR
- [ ] No analytics or crash-reporting SDK is added

### How to check your work
Create a profile with "high blood pressure" and "blood thinners", force-quit the app and reopen it: the profile should still be there and active. Tap "Delete all my data", force-quit and reopen: you should land on onboarding with no profiles. In mitmproxy, search the captured traffic for `hypertension` and `anticoagulant` (or whatever ids you used): there should be no matches.

### Out of scope
- Onboarding and profile screen design (NOMI-028)
- Profile switcher on the result screen (NOMI-061)
- Scoring with the active profile (NOMI-060)
- Recent scans storage (NOMI-063)
- Encrypted sync between devices (post-demo, see `planning/post-demo.md`)
- Privacy policy text (post-demo epic in `planning/post-demo.md`)

### Resources
- expo-secure-store: https://docs.expo.dev/versions/latest/sdk/securestore/
- mitmproxy: https://mitmproxy.org/
- Privacy decision: `docs/adr/0002-privacy.md`
- Conditions and medication types: `docs/scoring/dimensions.md`

---

## NOMI-040: Bundle the dataset in the app and show real product data after a scan, offline
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-007, NOMI-030, NOMI-038 (same sprint)

### Summary
Ship the `nomi.sqlite` dataset inside the app, look up the scanned barcode's NDC candidates in it, and send the user to the right result state with real product data. All of this works with the phone in airplane mode.

### Why this matters
Until now, scans have shown fixture data. This is the ticket where pointing the camera at a real box first shows that box's real name, ingredients and label warnings. The demo is run in airplane mode, so the lookup must be local and fast: scan to product in under 300 ms.

### What you will deliver
- `apps/mobile/src/lib/db.ts`: opens the bundled database once at app start and exposes `lookupBarcode(barcode: string): Promise<LookupResult>`
- `apps/mobile/scripts/fixture.sql`: inserts the five reference products from `packages/schema/examples/` into the same tables as NOMI-038, for building a fixture database
- An npm script `pnpm --filter mobile db:fixture` that builds `apps/mobile/assets/nomi.sqlite` from `fixture.sql`, and `pnpm --filter mobile db:copy` that copies `data/build/nomi.sqlite` into the same place
- Metro config updated so `.sqlite` files are bundled as assets
- The scan flow (NOMI-030) wired to `lookupBarcode`
- Unit tests for the lookup logic, and timing results in the PR

### Before you start
- **NDC candidates**: a barcode with no hyphens can match three possible NDC11 codes. `ndcCandidates()` in `apps/mobile/src/lib/barcode.ts` (NOMI-007) returns all three plus a `status` (`ok`, `invalid_check_digit`, `no_ndc`, `bad_length`). See NOMI-007 and the glossary in `docs/nomi-101.md`.
- **Scan flow states** (NOMI-030): scored, preliminary (ingredients and label warnings only), homeopathic, not found, invalid barcode. Scores arrive in Sprint 4, so for now every found in-scope product uses the preliminary state.
- **expo-sqlite**: Expo's SQLite library. Its docs include a section on importing an existing database file bundled as an asset.
- The dataset file is generated, not committed: `apps/mobile/assets/nomi.sqlite` must be in `.gitignore`.
- NOMI-038 is in the same sprint. Agree the table names with its owner on day one (suggested: `package`, `product`, `product_ingredient`, `label_warning`, `meta`). Start with the fixture database and switch to the real build when NOMI-038 publishes it.

### Steps
1. Install expo-sqlite with `npx expo install expo-sqlite`.
2. Add `sqlite` to the bundled asset extensions in `apps/mobile/metro.config.js` (`config.resolver.assetExts.push('sqlite')`).
3. Write `scripts/fixture.sql` with `CREATE TABLE` statements matching NOMI-038 and `INSERT` rows for the five reference products (Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil, store-brand diphenhydramine), using the NDCs, ingredients and warnings in `packages/schema/examples/`.
4. Add the `db:fixture` script (`sqlite3 assets/nomi.sqlite < scripts/fixture.sql`) and the `db:copy` script. Add `assets/nomi.sqlite` to `.gitignore`.
5. Write `db.ts`: open the bundled database once at app start following the expo-sqlite "import an existing database" instructions, and keep the connection open. Never open it per scan.
6. Implement `lookupBarcode`: call `ndcCandidates(barcode)`; if the status is `invalid_check_digit` or `bad_length`, return `{ state: 'invalid_barcode' }`; if `no_ndc`, return `{ state: 'not_found' }`; otherwise run one query `SELECT ... FROM package JOIN product USING (product_id) WHERE ndc11 IN (?, ?, ?)`.
7. Map the query result: no rows gives `not_found`; a homeopathic product gives `homeopathic`; an out-of-scope product gives `preliminary` with its scope flag so the screen can say it isn't scored (flag this case in the PR for the NOMI-029 owner); any other product gives `preliminary` with product name, ingredients and strengths, and label warnings. If more than one candidate matches, take the first by NDC11 order and log a warning.
8. Wire `lookupBarcode` into the scan flow so a successful camera read navigates to the matching state screen with the result.
9. Add timing: record `performance.now()` when the camera reports a barcode and again when the result screen has rendered. Log the difference in dev builds only.
10. Write unit tests for the mapping in step 7 using an in-memory or fixture database.
11. When NOMI-038 publishes, run `db:copy`, rebuild the dev build, and scan the five reference boxes plus at least five other boxes from the ground-truth set.
12. Turn on airplane mode on one iPhone and one Android phone, scan 10 boxes on each, and record the median and slowest scan-to-product time in the PR.

### Done when
- [ ] The dataset is bundled in the dev build and not committed to git
- [ ] Scanning a real box shows its real product name, ingredients and label warnings from the database
- [ ] Invalid, not-found and homeopathic barcodes reach their own states
- [ ] Scan to product shown in under 300 ms with the phone in airplane mode, on one iPhone and one Android phone (timings in the PR)
- [ ] Lookup unit tests pass

### How to check your work
Put the phone in airplane mode, open the app and scan a Tylenol box. You should see Tylenol's name and acetaminophen with its strength. Scan a non-drug barcode (a cereal box): you should get the not-found state. Check the dev log for the timing line: it should be under 300 ms.

### Out of scope
- Building the dataset file (NOMI-038)
- Scores and the scored state (NOMI-060)
- Name search and manual barcode entry (NOMI-058, NOMI-063)
- Downloading dataset updates in the background (post-demo, see `planning/post-demo.md`)
- Performance tuning beyond 300 ms (NOMI-069)

### Resources
- expo-sqlite: https://docs.expo.dev/versions/latest/sdk/sqlite/
- Expo development builds: https://docs.expo.dev/develop/development-builds/introduction/
- Reference products: `packages/schema/examples/`
- Barcode parser: `apps/mobile/src/lib/barcode.ts`

---

## NOMI-041: Build the risk-dimension breakdown with tappable citations on the result screen
**Team:** visualization | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-029, NOMI-014

### Summary
Add the "why this score" section to the result screen: one bar per risk dimension showing how many points it took off, and a detail view for each dimension with its explanation and the sources behind it. It must be readable without color.

### Why this matters
A bare number doesn't help anyone choose a medicine. Showing that Aleve lost points for stomach bleeding, blood pressure and kidney risk, with the FDA label section as the source, is what makes Nomi useful and trustworthy. It is also our main defense if a brand disputes a score: every point taken off links to its source.

### What you will deliver
- `apps/mobile/src/components/DimensionBreakdown.tsx`: the list of contribution bars, built from `DimensionBar` (NOMI-027)
- `apps/mobile/src/app/result/dimension.tsx`: the detail screen or bottom sheet for one dimension, showing explanation and citations with `CitationChip` (NOMI-027)
- The breakdown added to the result screen in `apps/mobile/src/app/result/`, rendering all five reference products
- A short test log in the PR from 5 testers

### Before you start
- **Risk dimension**: one kind of risk we rate, such as liver, GI bleeding, blood pressure, kidney, memory and thinking. See the glossary in `docs/nomi-101.md` and `docs/scoring/dimensions.md`.
- **Contribution**: how many points a dimension took off the 0-100 score for this profile. It comes from the `score-record` contract (NOMI-002): score, contribution per dimension, explanation and provenance.
- **Citation sources** you must be able to show: an FDA label section (for example "Warnings: Stomach bleeding warning"), a STOPP/START criterion, an ACB rating, and a FAERS signal. See the glossary for STOPP/START, ACB and FAERS.
- **NOMI-014 concept**: the chosen design for the score and breakdown, in the Figma library (NOMI-012). Follow it.
- Data: use the five reference products in `packages/schema/examples/` (NOMI-015). Each has draft dimension severities and expected scores for three profiles. Explanation text from templates (NOMI-048) is in progress this sprint; until it lands, use the explanation text in the reference records.
- The app may be offline. Citations must show their text (source name, section, document id) without a network connection; a link to DailyMed is optional and only opens when online.

### Steps
1. Read the NOMI-014 decision and the Figma frames for the breakdown and the dimension detail.
2. Write a mapper that turns a `score-record` into breakdown rows: `dimensionId`, `label` (plain words from `dimensions.md`, e.g. "Memory and thinking"), `points` (points taken off), `severityWord`, `citations`.
3. Build `DimensionBreakdown`: sort rows by points taken off, largest first. Show dimensions with zero points in a collapsed line "No concerns found for: ..." so the user sees they were checked.
4. Make every row readable without color: show the points as text (e.g. "-18 points"), a severity word (e.g. "High"), and a bar length. Color is extra, never the only signal.
5. Make each row tappable. The detail view shows the dimension name, the explanation sentences, and one `CitationChip` per citation with source type, section or criterion id, and document id.
6. Add screen-reader labels to each row, for example "Stomach bleeding, high concern, 18 points taken off. Double tap for sources."
7. Add the breakdown to the result screen and check it with all five reference products for all three profiles.
8. Check readability without color: on iPhone use Settings > Accessibility > Display & Text Size > Color Filters > Grayscale (or the Android equivalent) and confirm every row still reads correctly.
9. Run the tester session: 5 people outside the Visualization team. Show each one a reference product for one profile (for example Aleve for a 70-year-old with high blood pressure) and ask "Why did this product get this score?" A pass means they name the top two dimensions and point to where the source is shown. Record each answer in the PR.
10. Fix anything that at least two testers got stuck on, and retest with one person.

### Done when
- [ ] The breakdown renders for all five reference products and all three profiles
- [ ] Tapping any dimension opens its explanation and citations, and citations show their text offline
- [ ] Every row reads correctly in grayscale mode
- [ ] Every row has a screen-reader label
- [ ] 5 testers explained why a reference product scored the way it did, with answers logged in the PR
- [ ] Matches the NOMI-014 concept in Figma, confirmed by a second Visualization member

### How to check your work
Open the result screen for Aleve with the 65+ high blood pressure profile. The top rows should be GI bleeding, blood pressure and kidney, each with a citation to the label's warnings. Turn on grayscale and confirm you can still tell which dimension matters most. Turn on VoiceOver and swipe through the rows: each should read its name, level and points.

### Out of scope
- The benchmark line and profile switcher (NOMI-061)
- Writing the explanation templates (NOMI-048)
- Computing scores on the phone (NOMI-060)
- Alternative comparison (NOMI-062)
- Full accessibility pass across all screens (NOMI-070)

### Resources
- Risk dimensions: `docs/scoring/dimensions.md`
- Reference products: `packages/schema/examples/`
- Data contracts: `packages/schema/README.md`
- React Native accessibility: https://reactnative.dev/docs/accessibility

---

## NOMI-042: Publish the coverage dashboard (v1) to GitHub Pages
**Team:** visualization | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-025, NOMI-026

### Summary
Build a static web dashboard in `apps/dashboard` that shows how well the pipeline covers real products: barcode resolution by store, brand vs store brand and category; products by category and scope flag; and label section coverage. Publish it to GitHub Pages so the team and the demo audience can see it.

### Why this matters
Fifteen people are changing the pipeline every day, and the team needs one shared place to see whether coverage is going up or down. The demo also includes a short data story ("we resolve X% of real barcodes from five stores"), and this dashboard is where that number comes from.

### What you will deliver
- `pipeline/src/nomi_pipeline/build/dashboard_data.py` and a subcommand `uv run pipeline dashboard-data` that writes small summary JSON files (counts only) to `pipeline/reports/dashboard/`
- A static site in `apps/dashboard/` (Vite and TypeScript) that reads those JSON files and draws the charts
- `.github/workflows/dashboard.yml` that builds the site and deploys it to GitHub Pages on every merge to `main` that changes `apps/dashboard/` or `pipeline/reports/dashboard/`
- The live GitHub Pages URL in `apps/dashboard/README.md`

### Before you start
- **Barcode coverage**: the share of ground-truth barcodes (NOMI-020, `pipeline/tests/fixtures/barcodes.csv`) that resolve to a product. The resolver and its report come from NOMI-025.
- **Store brand**: a product sold under the store's own name (CVS Health, Equate, Up and Up, Kroger, Publix). If `barcodes.csv` has no brand vs store brand column, derive it from the brand name and list the rule in the PR.
- **OTC category and scope flag**: from NOMI-026. Category is the product group (internal analgesics, antacids, cough-cold and so on); scope flags mark homeopathic and out-of-scope products.
- **Label section coverage**: the share of labels that contain each Drug Facts section (Uses, Warnings, Directions and so on), from the NOMI-023 report.
- Only aggregate counts go into the committed JSON files. Never commit product-level raw data; `pipeline/reports/` is for committed summary reports.
- The repo is public, so GitHub Pages is free.

### Steps
1. Write `dashboard_data.py`. Using DuckDB or Polars, produce:
   - `barcode_coverage.json`: total and resolved counts, overall and split by store, by brand vs store brand, and by category
   - `products_by_category.json`: product counts per OTC category and per scope flag (homeopathic, out of scope, in scope)
   - `section_coverage.json`: for each Drug Facts section, the number and share of labels that have it
   - `meta.json`: generation date, dataset version, code commit
2. Register the `dashboard-data` subcommand and run it. Commit the JSON files to `pipeline/reports/dashboard/`.
3. Create the Vite site in `apps/dashboard/` (`pnpm create vite` with the vanilla TypeScript template) and add it to the pnpm workspace.
4. Copy the JSON files into the site at build time (a small prebuild script), so the site always reads the committed reports.
5. Build three sections with a free chart library such as Observable Plot: barcode coverage (one headline number plus bar charts by store, brand type and category), products by category and scope, and label section coverage.
6. Show the generation date, dataset version and code commit at the top of the page so viewers know how fresh it is.
7. Label every chart with its numbers as text, not only as bar lengths, so it reads without color.
8. Write `.github/workflows/dashboard.yml` using the official GitHub Pages actions to build and deploy on merge to `main`. Enable Pages in the repository settings (ask a cofounder if you lack access).
9. Compare every headline number with the pipeline logs and reports: barcode coverage with `pipeline/reports/identity_coverage.md` (NOMI-025), category counts with the NOMI-026 counts, and section coverage with the NOMI-023 report. Note each comparison in the PR.
10. Add the live URL to `apps/dashboard/README.md` and present it at the Friday demo at the end of Sprint 3.

### Done when
- [ ] `uv run pipeline dashboard-data` writes the four JSON files to `pipeline/reports/dashboard/`
- [ ] The site is live on GitHub Pages and the URL is in `apps/dashboard/README.md`
- [ ] All three sections render: barcode coverage (by store, brand vs store brand, category), products by category and scope flag, label section coverage
- [ ] Every headline number matches the pipeline logs and reports, with the comparison in the PR
- [ ] Shown at the Friday demo

### How to check your work
Run `uv run pipeline dashboard-data`, then `pnpm --filter dashboard dev` and open the local URL. The overall barcode coverage number should equal the one in `pipeline/reports/identity_coverage.md`. Change one number in a JSON file by hand, reload, and confirm the chart changes, then revert it.

### Out of scope
- FAERS signal explorer page (NOMI-071)
- Improving coverage itself (NOMI-037)
- Category and scope assignment (NOMI-026)
- Scores and benchmarks on the dashboard (later, after NOMI-054)

### Resources
- GitHub Pages: https://docs.github.com/en/pages
- Deploy Pages action: https://github.com/actions/deploy-pages
- Vite: https://vitejs.dev/
- Observable Plot: https://observablehq.com/plot/
- DuckDB: https://duckdb.org/docs/
- Dashboard plan: `apps/dashboard/README.md`

---

## NOMI-043: Add `uv run pipeline run` to run every stage with a run manifest
**Team:** platform | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-008

### Summary
Add one command, `uv run pipeline run`, that runs every pipeline stage in order (fetch, ingest, resolve, extract, signals, score, build), skips stages whose inputs haven't changed, and writes a run manifest recording input versions, the code commit and a hash of every output.

### Why this matters
Every score Nomi shows must trace back to the exact data and code that produced it. Today each stage is run by hand, so nobody can say for sure which inputs went into a given dataset. One command with a manifest makes the dataset reproducible: anyone can rebuild it, and two runs on the same inputs must give the same result.

### What you will deliver
- `pipeline/src/nomi_pipeline/run.py` with a stage registry and the `run` subcommand
- Run manifests written to `data/runs/<run_id>/manifest.json`, plus `data/runs/latest.json` pointing to the last run
- Options `--only <stage>` (run one stage), `--force` (ignore the skip check) and `--dry-run` (print what would run)
- Tests in `pipeline/tests/test_run.py`
- A section in `pipeline/README.md` explaining the command and the manifest

### Before you start
- **Stages**: listed in `pipeline/README.md`. Each lives in its own package under `pipeline/src/nomi_pipeline/`: fetch, ingest, identity (resolve), extract, evidence (signals), score, build.
- **Run manifest**: a JSON file that says what ran, on which inputs, with which code, and what it produced.
- **Hash**: a SHA-256 of a file's bytes. If two files have the same hash, they are identical.
- Several stages don't exist yet (signals and score land in Sprint 4). Register them anyway. When a stage has no implementation, the runner prints "not implemented, skipped" and continues, so adding it later is one line.
- The CLI already exists from NOMI-008 (`uv run pipeline fetch`). Add `run` to the same CLI, using the same framework.

### Steps
1. Define a `Stage` record: `name`, `inputs` (list of paths or globs under `data/` and `pipeline/knowledge/`), `outputs` (list of paths), `code_paths` (the stage's package folder), and `fn` (the function to call).
2. Register the seven stages in order: `fetch`, `ingest`, `resolve`, `extract`, `signals`, `score`, `build`. Point each at its existing entry function where one exists.
3. For each stage, compute a fingerprint: hashes of all input files plus a hash of the stage's code folder (or the git tree hash of that folder).
4. Before running a stage, compare its fingerprint with the one in `data/runs/latest.json`. If they match and all outputs exist with the recorded hashes, skip it and log "unchanged, skipped".
5. After a stage runs, hash every output file and record it.
6. Write the manifest: `run_id` (timestamp plus short commit), `code_commit` (`git rev-parse HEAD`, and `dirty: true` if there are uncommitted changes), `started_at`, `finished_at`, and for each stage: `status` (`ran`, `skipped_unchanged`, `not_implemented`, `failed`), `inputs` with hashes, `outputs` with hashes, and duration.
7. Stop the run at the first failed stage and write the manifest with the failure recorded.
8. Find and remove sources of non-determinism in the existing stages: sort rows before writing Parquet, don't write current timestamps into data files, and pin random seeds. If a file format can't be made byte-identical, compare a hash of its sorted contents instead and document which files use this in the README.
9. Write tests with two tiny fake stages: a second run skips both; changing an input file reruns only the stages that depend on it; `--force` reruns everything.
10. Run `uv run pipeline run --force` twice on the same inputs and compare the output hashes in the two manifests.
11. Document the command, the options and the manifest fields in `pipeline/README.md`.

### Done when
- [ ] `uv run pipeline run` runs all implemented stages in order and reports unimplemented ones as skipped
- [ ] Each run writes `data/runs/<run_id>/manifest.json` with input versions, code commit and output hashes
- [ ] A second run with unchanged inputs skips every stage
- [ ] Two forced runs on the same inputs produce identical output hashes (manifests attached to the PR)
- [ ] `uv run pytest pipeline/tests/test_run.py` passes

### How to check your work
Run `uv run pipeline run`, then run it again: every stage should say "unchanged, skipped". Touch one input of the `extract` stage (for example add a line to a knowledge file and remove it again in a copy) and rerun: only `extract` and later stages should run. Compare `outputs` in the two forced-run manifests with `diff`: there should be no differences.

### Out of scope
- Implementing the stages themselves (their own tickets, e.g. NOMI-038, NOMI-045, NOMI-051, NOMI-053)
- The release command and diff report (NOMI-059)
- Scheduled runs in GitHub Actions (post-demo epic in `planning/post-demo.md`)

### Resources
- uv: https://docs.astral.sh/uv/
- Polars: https://docs.pola.rs/
- Stage list and outputs: `pipeline/README.md`

---

## NOMI-044: Build the FAERS drug-reaction pairs table split by age band, sex and event group
**Team:** platform | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-024

### Summary
Turn the cleaned FAERS tables into one tidy table, `data/silver/faers_pairs.parquet`, with one row per report, suspect drug and reaction, plus the patient's age band and sex and the reaction's event group. Signal detection (NOMI-053) reads this table.

### Why this matters
FAERS is our real-world evidence: it shows which problems people report with which drugs. To ask "is liver injury reported more often with acetaminophen than expected, in adults 65+?" we need each drug paired with each reaction in the same report, split by age and sex, and grouped into the kinds of events that match our risk dimensions. Without this table, NOMI-053 can't compute signals.

### What you will deliver
- `pipeline/src/nomi_pipeline/evidence/pairs.py` and a subcommand that writes `data/silver/faers_pairs.parquet`
- `pipeline/knowledge/faers_event_groups.yaml`: each event group, the risk dimension it maps to, and the MedDRA preferred terms in it
- A reconciliation report in `pipeline/reports/faers_pairs.md`
- Tests in `pipeline/tests/evidence/test_pairs.py` using a small fixture

### Before you start
- **FAERS**: FDA's Adverse Event Reporting System. See the glossary in `docs/nomi-101.md`. NOMI-024 already loaded and deduplicated it into `data/bronze/faers/` (latest `caseversion` per `caseid`).
- **FAERS tables you need**: DEMO (one row per report: `primaryid`, `caseid`, age, age unit, sex), DRUG (one row per drug in a report: `primaryid`, `drug_seq`, `role_cod`, `drugname`), REAC (one row per reaction: `primaryid`, `pt`).
- **Drug role codes**: `PS` primary suspect, `SS` secondary suspect, `C` concomitant (taken at the same time, not suspected), `I` interacting. Keep only `PS` and `SS`.
- **MedDRA**: the medical vocabulary FAERS uses for reactions. A **preferred term (PT)** is a specific reaction such as "Hepatic failure"; a **system organ class (SOC)** is the top-level group such as "Hepatobiliary disorders". MedDRA uses British spelling, for example "Gastrointestinal haemorrhage".
- **MedDRA licensing**: the PT text is in the public FAERS files, but the MedDRA hierarchy files (PT to SOC) are distributed by MSSO under a subscription. Before using hierarchy files, confirm with the cofounders and the NOMI-006 license audit that we may use them. If we can't, build event groups from PT names only (step 5) and leave `soc` empty, and say so in the PR.
- **Event group**: our own grouping of PTs that matches a risk dimension, for example "liver injury" for the liver dimension.
- **Age bands** for this table: 0-11, 12-17, 18-64, 65+, plus `unknown`.
- Ingredient ids are added to drug rows in NOMI-046 (same sprint). Keep `primaryid` and `drug_seq` in every row so NOMI-046's output joins straight in.

### Steps
1. Read `docs/scoring/dimensions.md` (NOMI-016) and draft `faers_event_groups.yaml` with at least these groups: liver injury, GI bleeding, kidney injury, cardiovascular events, cognitive impairment, sedation and falls, serotonin syndrome, bleeding, and allergic reactions. For each group list the dimension and the PTs, for example liver injury: "Hepatic failure", "Acute hepatic failure", "Hepatotoxicity", "Drug-induced liver injury", "Hepatitis".
2. Check each PT name exists in the FAERS REAC data (`SELECT DISTINCT pt` in DuckDB) and fix spelling to match exactly.
3. Ask a Data Analysis member to review the event groups, since NOMI-053 depends on them.
4. Convert age to years using the age unit column (`YR` years, `MON` months, `WK` weeks, `DY` days, `HR` hours, `DEC` decades) and assign the age band. Treat missing or impossible ages (below 0 or above 120) as `unknown`.
5. Normalize sex to `M`, `F` or `unknown`.
6. If the MedDRA license is confirmed, join PTs to their primary SOC; otherwise leave `soc` null.
7. Build the pairs: join DRUG (filtered to `role_cod` in `PS`, `SS`) with REAC on `primaryid`, then join DEMO. Each row is one report, one suspect drug, one reaction. Columns: `primaryid`, `caseid`, `quarter`, `drug_seq`, `role_cod`, `drugname`, `pt`, `soc`, `event_group` (null if the PT is in no group), `dimension`, `age_band`, `sex`.
8. Write the output with Polars, sorted by `primaryid`, `drug_seq`, `pt`.
9. Write the reconciliation report. Start from the deduplicated report count in the NOMI-024 stats, and show how many reports were dropped for having no `PS`/`SS` drug and how many for having no reaction. Then check that the row count equals the sum over reports of (suspect drugs x reactions). Add counts per age band, sex and event group.
10. Write tests with a fixture of three fake reports covering a concomitant drug (dropped), two suspect drugs with two reactions (four rows), and an age in months.

### Done when
- [ ] `data/silver/faers_pairs.parquet` exists with the columns in step 7 and only `PS` and `SS` drugs
- [ ] Every row has an age band (0-11, 12-17, 18-64, 65+ or unknown) and a sex (M, F or unknown)
- [ ] `faers_event_groups.yaml` covers at least the nine groups in step 1 and was reviewed by a Data Analysis member
- [ ] MedDRA license status is recorded in the PR, and SOC is filled only if use is confirmed
- [ ] Row and report counts reconcile with the NOMI-024 dedup stats, shown in `pipeline/reports/faers_pairs.md`
- [ ] `uv run pytest pipeline/tests/evidence/test_pairs.py` passes

### How to check your work
In DuckDB, count rows where `drugname` contains "ACETAMINOPHEN" and `event_group = 'liver injury'`. You should see many thousands across all quarters. Count reports in the pairs table with `COUNT(DISTINCT primaryid)` and confirm it equals the number in your reconciliation report.

### Out of scope
- FAERS loading and deduplication (NOMI-024)
- Mapping drug names to ingredients (NOMI-046)
- Computing IC and IC025 signals (NOMI-053)
- The signal explorer page (NOMI-071)

### Resources
- FAERS quarterly data files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- openFDA FAERS overview: https://open.fda.gov/data/faers/
- MedDRA: https://www.meddra.org/
- DuckDB: https://duckdb.org/docs/

---

## NOMI-045: Merge rule and LLM label extraction, measure agreement, and run on every in-scope label
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-031, NOMI-032

### Summary
Combine the rule-based extractor (NOMI-031) and the LLM extractor (NOMI-032) into one set of label facts per product, accept fields where they agree, list disagreements for a person to review, run it on every in-scope label, and measure accuracy on 100 hand-checked labels. The result is `data/silver/label_facts.parquet`.

### Why this matters
Label facts (warnings, age limits, maximum dose, conditions to ask a doctor about) feed the knowledge base, the scores and the dataset on the phone. Each extractor makes mistakes, but they make different ones. Where both agree we can trust the value; where they disagree a person decides. Measuring precision and recall on hand-checked labels tells us how much we can rely on the result.

### What you will deliver
- `pipeline/src/nomi_pipeline/extract/merge.py` and a subcommand that writes `data/silver/label_facts.parquet`
- `data/silver/label_facts_review.parquet`: one row per disagreement for review
- `pipeline/tests/fixtures/label_facts_handcheck.jsonl`: the 100 hand-checked labels with the correct value for every field
- `pipeline/reports/label_extraction.md`: precision, recall and agreement per field, plus run stats and LLM cost
- Tests in `pipeline/tests/extract/test_merge.py`

### Before you start
- **Drug Facts panel** and **LOINC section code**: see the glossary in `docs/nomi-101.md`. Section text is in `data/bronze/spl_sections.parquet` (NOMI-023).
- **Mandated warning**: standard warning text FDA requires, such as "Liver warning" on acetaminophen. The catalogue is `pipeline/knowledge/mandated_warnings.yaml` (NOMI-017).
- **Extraction schema**: the fields both extractors produce, in `packages/schema/schemas/` (NOMI-032): uses, age limits, max dose, ask-a-doctor conditions, interacting drug classes, do-not-use conditions, pregnancy, allergens, mandated warnings.
- **In-scope label**: a product that is not flagged homeopathic or out of scope in NOMI-026.
- **Precision**: of the values we extracted, the share that are correct. **Recall**: of the correct values, the share we extracted. **Agreement**: the share of fields where rules and LLM gave the same value.
- **Cost**: the NOMI-032 projection for all in-scope labels must stay under $50. Confirm the projected cost with a cofounder before starting the full LLM run, and stop if it would exceed $50.
- Some fields come only from the LLM (ask-a-doctor conditions, interacting drug classes) because rules can't extract them. They have no second opinion, so mark them and measure them on the hand-checked set.

### Steps
1. Write merge rules per field and put them in a table in the PR:
   - List fields (mandated warnings, allergens, do-not-use conditions): an item found by both is `agreed`; an item found by only one is a disagreement.
   - Number fields (max daily dose, dosing interval, minimum age): `agreed` if equal after converting to the same unit; otherwise a disagreement.
   - LLM-only fields: status `llm_only`.
2. Give every value a `status` (`agreed`, `rules_only`, `llm_only`, `conflict`) and a `source` so later steps know how much to trust it.
3. Write `merge.py` to apply these rules per label and write one row per label and field to `label_facts.parquet`, keyed by `spl_set_id` and `spl_version`. Write each disagreement, with both values and the section text, to `label_facts_review.parquet`.
4. Write unit tests with three small labels: one where both agree, one with a missing warning in the LLM output, and one with different max doses.
5. Pick 100 labels for hand-checking, spread across categories (at least 10 each from pain/fever, allergy, sleep, cough/cold and digestive) and including the five reference products from `packages/schema/examples/`.
6. Hand-check the 100 labels by reading each Drug Facts panel on DailyMed and writing the correct value for every field into `label_facts_handcheck.jsonl`. Have a second person check 10 of them.
7. Run the rules extractor and the LLM extractor on every in-scope label (LLM through the Message Batches API, as in NOMI-032), then run the merge.
8. Score the merged output against the hand-checked labels and compute precision, recall and agreement per field.
9. If mandated-warning recall is below 98%, find the missed warnings, fix the rule patterns or merge rule, add the cases to the NOMI-017 fixtures in `pipeline/tests/fixtures/warnings/`, and rerun.
10. Write `pipeline/reports/label_extraction.md`: labels processed, failures, LLM cost, per-field precision, recall and agreement, and the number of open disagreements.

### Done when
- [ ] `data/silver/label_facts.parquet` has a row for every in-scope label, and every value has a `status`
- [ ] Disagreements are listed in `label_facts_review.parquet`
- [ ] 100 hand-checked labels are committed, with 10 checked by a second person
- [ ] Mandated-warning recall is at least 98% on the 100 hand-checked labels
- [ ] Per-field precision, recall and agreement, and the actual LLM cost, are in `pipeline/reports/label_extraction.md`
- [ ] `uv run pytest pipeline/tests/extract` passes

### How to check your work
Query `label_facts.parquet` for a Tylenol Extra Strength label: it should have the Liver warning with status `agreed` and a max daily dose matching the label. Query an Aleve label: it should have the Stomach bleeding warning. Open `label_facts_review.parquet`, read five disagreements and confirm each really is a disagreement between the two extractors.

### Out of scope
- Writing the rule extractor (NOMI-031) or LLM extractor (NOMI-032)
- Classifying uses into the taxonomy (NOMI-047)
- Resolving every disagreement by hand (only listed here; demo products are reviewed in NOMI-073)
- A full annotated gold set with guidelines (post-demo epic in `planning/post-demo.md`)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Anthropic API docs (Message Batches): https://docs.anthropic.com/
- Mandated warning catalogue: `pipeline/knowledge/mandated_warnings.yaml`
- Glossary: `docs/nomi-101.md`

---

## NOMI-046: Map every FAERS drug row to its ingredients
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-024, NOMI-033

### Summary
Run the FAERS drug-name matcher (NOMI-033) over every drug row in FAERS, so each row that names an OTC product gets the UNII ids of its ingredients. Review the most common names the matcher missed and spot-check its answers.

### Why this matters
FAERS reports name drugs in free text: "TYLENOL PM", "advil liqui-gels 200mg", "acetaminophen/diphenhydramine". Our knowledge base and scores are keyed by ingredient. Until each report's drug names map to ingredients, FAERS signals (NOMI-053) can't be attached to the ingredients we score, and wrong mappings would put the wrong evidence behind a score.

### What you will deliver
- `pipeline/src/nomi_pipeline/evidence/normalize.py` and a subcommand that writes `data/silver/faers_drug_ingredient.parquet` with columns `primaryid`, `drug_seq`, `drugname`, `unii`, `ingredient_name`, `match_method`, `match_score`
- `pipeline/knowledge/faers_name_overrides.csv`: hand-reviewed mappings for frequent strings the matcher missed, with columns `drugname`, `uniis`, `reviewed_by`, `note`
- `pipeline/tests/fixtures/faers_mapping_spotcheck.csv`: the 200 spot-checked rows with a `correct` column
- `pipeline/reports/faers_mapping.md`: coverage, spot-check result and top remaining unmapped strings

### Before you start
- **FAERS**, **UNII**, **RxNorm/RxCUI**: see the glossary in `docs/nomi-101.md`.
- **The matcher** (NOMI-033): `pipeline/src/nomi_pipeline/evidence/name_matcher.py`. It tries exact match, then RxNorm synonyms, then fuzzy matching, and expands combination names to all their ingredients.
- **Crosswalk**: `data/silver/ingredient_crosswalk.parquet` (NOMI-019) links RxNorm ingredients to UNII. The "OTC ingredient list" in this ticket means the ingredients in that crosswalk that appear in OTC products from the NDC directory (NOMI-009).
- **FAERS drug rows**: the DRUG table in `data/bronze/faers/` (NOMI-024), one row per drug per report, with `drugname` and, in newer quarters, a `prod_ai` column naming the active ingredient. Confirm with the NOMI-033 owner whether the matcher already uses `prod_ai`; if not, try it as an extra input when `drugname` doesn't match.
- **OTC drug row**: a drug row whose drug contains at least one ingredient from the OTC ingredient list. This is the denominator for the 90% target.
- Because unmapped rows can't be classified automatically, estimate how many of them are OTC by labeling a random sample (step 6).

### Steps
1. Get the distinct `drugname` values with their row counts (DuckDB: `SELECT drugname, COUNT(*) FROM drug GROUP BY 1 ORDER BY 2 DESC`). Running the matcher once per distinct string is much faster than once per row.
2. Run the matcher over every distinct string, expanding combination names to all their ingredients, and join the result back to the drug rows.
3. Apply `faers_name_overrides.csv` before the matcher so reviewed mappings always win.
4. List the 500 most frequent unmapped strings. Review each by hand: if it names an OTC product or ingredient, add it to the override file with its UNIIs; if it's not an OTC drug (a prescription drug, "UNKNOWN", a device), record that in the `note` column so it isn't reviewed again.
5. Rerun steps 2 to 3 with the overrides.
6. Estimate the denominator: draw 200 random unmapped rows (weighted by row, not by distinct string) and label whether each refers to an OTC ingredient. Use that share to estimate how many unmapped rows are OTC.
7. Compute coverage: mapped OTC rows divided by (mapped OTC rows plus estimated unmapped OTC rows). Report it overall and for the top 20 OTC ingredients.
8. Spot-check: draw 200 random mapped rows, check each mapping by hand against the drug string, and fill the `correct` column. Have a second person check 20 of them.
9. If the spot-check is below 97%, find the pattern behind the errors (often fuzzy matches on short names), tighten the rule or add overrides, and redo the spot-check on a fresh sample.
10. Write `pipeline/reports/faers_mapping.md` with coverage, the denominator estimate and how you made it, spot-check accuracy, and the 50 most frequent remaining unmapped strings.

### Done when
- [ ] `data/silver/faers_drug_ingredient.parquet` exists, and combination products have one row per ingredient
- [ ] The 500 most frequent unmapped strings were reviewed, with results in `faers_name_overrides.csv`
- [ ] At least 90% of OTC drug rows are mapped, with the denominator method in the report
- [ ] At least 97% of 200 spot-checked mappings are correct, with the sample committed
- [ ] `pipeline/reports/faers_mapping.md` is committed

### How to check your work
Look up rows where `drugname` is "NYQUIL" (or similar). Each should map to three ingredients: acetaminophen, dextromethorphan and doxylamine. Look up "ADVIL": it should map to ibuprofen only. Count rows mapped to acetaminophen and compare with a plain text search for "ACETAMINOPHEN" or "TYLENOL" in `drugname`: the mapped count should be at least as large.

### Out of scope
- Building or tuning the matcher's core logic (NOMI-033)
- The RxNorm to UNII crosswalk (NOMI-019)
- Drug-reaction pairs and age bands (NOMI-044)
- Computing signals (NOMI-053)

### Resources
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/index.html
- FAERS quarterly data files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- DuckDB: https://duckdb.org/docs/
- Glossary: `docs/nomi-101.md`

---

## NOMI-047: Classify every in-scope product's uses into a 25-use taxonomy
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-032, NOMI-026

### Summary
Define a taxonomy of about 25 uses (pain, fever, nasal allergy, sleep and so on), classify every in-scope product into one or more of them from its label's Uses section, and measure accuracy on 200 hand-labeled products. The result fills the `uses` field on every in-scope product.

### Why this matters
Benchmarks and safer alternatives only make sense between products used for the same thing. ZzzQuil's alternative should be another sleep aid, not Claritin, and "better than 82% of pain relievers" needs to know which products are pain relievers. The label's Uses section says what a product is for, and this ticket turns that text into a fixed set of uses.

### What you will deliver
- `pipeline/knowledge/uses.yaml`: the taxonomy, with `id`, `label`, `description`, `keywords` and two example label phrases per use
- `pipeline/src/nomi_pipeline/extract/uses.py` and a subcommand that writes `data/silver/product_uses.parquet` (`spl_set_id`, `use_id`, `source`, `status`)
- The `uses` field filled on `data/silver/product.parquet` for every in-scope product
- `pipeline/tests/fixtures/uses_labeled.csv`: 200 hand-labeled products
- `pipeline/reports/uses.md`: per-use precision, recall and F1, macro-F1, and the products with no use

### Before you start
- **Uses**: what a product is for. See the glossary in `docs/nomi-101.md`. On the label it's the "Uses" section, LOINC code `34067-9`; text is in `data/bronze/spl_sections.parquet` (NOMI-023). Some labels lack it; the "Purpose" section (`55105-1`) is a fallback.
- **In-scope product**: not flagged homeopathic or out of scope in NOMI-026. NOMI-026 also gives an OTC category per product, which is a useful hint.
- **Multi-label**: one product can have several uses. NyQuil treats cough, congestion, pain and fever, and helps with sleep.
- **Macro-F1**: compute the F1 score (the balance of precision and recall) for each use separately, then average them so rare uses count as much as common ones.
- The LLM call follows NOMI-032: Claude structured output through the Message Batches API, with the prompt and model version recorded in provenance. Estimate the cost on 50 products first and confirm the total with a cofounder before the full run.
- If the NOMI-032 extraction already returns a uses list, map it to the taxonomy instead of making a second LLM call.

### Steps
1. Draft `uses.yaml` with about 25 uses. Start from: pain, fever, nasal allergy, itchy or watery eyes, sleep, cough, chest congestion, nasal congestion, sore throat, heartburn and acid, gas, constipation, diarrhea, nausea and motion sickness, upset stomach, topical pain, eye redness, dry eye, skin itch and rash, fungal skin infection, cold sores, minor cuts and burns, smoking cessation, hemorrhoids, and other. Add keywords and two example phrases from real labels for each.
2. Ask the NOMI-054 and NOMI-055 owners (benchmarks and alternatives) to review the taxonomy, since they will group products by it.
3. Write keyword rules: a use matches if the Uses text contains one of its keywords, for example "nighttime sleep aid" or "sleeplessness" for sleep, "heartburn" or "acid indigestion" for heartburn and acid.
4. Write the LLM classification: send the Uses text (or Purpose text as a fallback) with the taxonomy and ask for a list of use ids. Return only ids from the taxonomy.
5. Merge: a use found by both the LLM and the rules gets status `agreed`; a use found by only one gets `llm_only` or `rules_only`. Keep all three in the output but note them in the report.
6. Hand-label 200 products, spread across categories with at least 5 products per use where possible, and including the five reference products. Have a second person label 20 of them and record how often you agree.
7. Run on all in-scope products and compute per-use precision, recall and F1 plus macro-F1 on the 200 labeled products.
8. If macro-F1 is below 0.9, look at the worst uses, fix keywords or the prompt, and rerun.
9. Find in-scope products with no use. Assign them using the NOMI-026 category where it's unambiguous, otherwise review by hand, so every in-scope product has at least one use.
10. Write the `uses` field onto `product.parquet` and write `pipeline/reports/uses.md`.

### Done when
- [ ] `pipeline/knowledge/uses.yaml` has about 25 uses with keywords and examples, reviewed by the NOMI-054 or NOMI-055 owner
- [ ] 200 hand-labeled products committed, 20 double-labeled
- [ ] Macro-F1 is at least 0.9 on the hand-labeled set, shown in `pipeline/reports/uses.md`
- [ ] Every in-scope product has at least one use
- [ ] LLM cost reported in the PR

### How to check your work
Look up ZzzQuil: its uses should include sleep and should not include nasal allergy. Look up Claritin: nasal allergy (and possibly itchy or watery eyes), not sleep. Look up NyQuil: cough, nasal congestion, pain, fever, and probably sleep. Count products with an empty `uses` list among in-scope products: it should be zero.

### Out of scope
- Benchmarks by use (NOMI-054)
- Choosing alternatives (NOMI-055)
- Category and scope flags (NOMI-026)
- The LLM extractor itself (NOMI-032)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Anthropic API docs (Message Batches): https://docs.anthropic.com/
- scikit-learn F1 score: https://scikit-learn.org/stable/modules/generated/sklearn.metrics.f1_score.html
- Glossary: `docs/nomi-101.md`

---

## NOMI-048: Write the explanation templates (v0) at an 8th-grade reading level
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S3 | **Depends on:** NOMI-016, NOMI-022

### Summary
Write fill-in-the-blank sentences that explain each risk to the user: one template for each risk dimension and severity level, and one for each condition or medication modifier. Each sentence has a citation slot, reads at an 8th-grade level or below, and a CI check enforces this. The templates ship in the dataset and the phone fills them in.

### Why this matters
The explanation is the sentence a user reads under "why this score", for example "Diphenhydramine can affect memory and thinking in adults 65 and older." Using fixed templates instead of generated text means every sentence is predictable, reviewed in advance and tied to a source. Plain wording matters because many of our users are older adults and caregivers.

### What you will deliver
- One YAML file per risk dimension in `pipeline/knowledge/templates/`, for example `liver.yaml`, `gi_bleeding.yaml`, each with templates for severities 1, 2 and 3
- `pipeline/knowledge/templates/modifiers.yaml` with one template per condition and medication modifier
- `pipeline/src/nomi_pipeline/score/templates.py`: loads templates, fills placeholders and renders an explanation for a product and profile (used for tests and previews; the phone has its own filler)
- `pipeline/tests/knowledge/test_templates.py`: checks every template has a citation slot, uses only known placeholders, and scores at grade 8 or below
- A CI step that runs these tests
- Rendered explanations for the five reference products pasted into the PR

### Before you start
- **Risk dimension**, **severity** (0-3), **persona**: see the glossary in `docs/nomi-101.md` and `docs/scoring/dimensions.md` (NOMI-016).
- **Modifier**: a condition or medication type that raises risk on a dimension, for example high blood pressure with decongestants. The list is in `docs/scoring/dimensions.md`.
- **Reading level**: the Flesch-Kincaid grade level estimates the school grade needed to read a text. The `textstat` Python package computes it.
- **Interview vocabulary**: `docs/research/interviews-round-1.md` (NOMI-022) records the words real users use. If it hasn't merged, use plain everyday words and add a checklist item in the PR to update wording when it lands.
- **Citation slot**: a field on each sentence that the phone fills with the source (label section, STOPP/START criterion, ACB rating or FAERS signal), so every sentence shows where it came from.
- Keep templates simple: placeholders in `{curly_braces}` only, no conditions or loops, so the TypeScript filler on the phone is a simple text replacement.
- Templates describe risk; they don't give medical instructions beyond what the label says. When action is needed, use wording like "Ask a pharmacist or doctor before using this."

### Steps
1. Choose the placeholders and list them in a short comment at the top of each template file and in the PR: `{ingredient}`, `{persona}` (e.g. "adults 65 and older"), `{condition}` (e.g. "high blood pressure"), `{max_daily_dose}`. Don't add others without agreeing with the app team.
2. Define the template format. Example entry in `gi_bleeding.yaml`:
   ```yaml
   dimension: gi_bleeding
   templates:
     - severity: 2
       text: "{ingredient} can cause bleeding in the stomach, especially for {persona}."
       citation_slot: required
   ```
3. Write templates for every dimension in `docs/scoring/dimensions.md` at severities 1, 2 and 3. Use plain words: "liver damage" not "hepatotoxicity", "memory and thinking" not "anticholinergic burden", "stomach bleeding" not "GI hemorrhage".
4. Write one template per modifier in `modifiers.yaml`, for example: "{ingredient} can raise blood pressure. This matters because you have {condition}."
5. Read the interview synthesis (NOMI-022) and replace any words users didn't recognize with the words they used. List the swaps in the PR.
6. Write `templates.py` to load all templates, fill placeholders from a dictionary, and render the explanation for a product and profile using the dimension severities in the reference records.
7. Write the tests: every template has `citation_slot: required`; every placeholder is in the allowed list; after filling placeholders with example values, every template scores Flesch-Kincaid grade 8.0 or below with `textstat`.
8. Add the test to CI (it runs with the existing `uv run pytest` job if it lives in `pipeline/tests/`).
9. Render explanations for the five reference products from `packages/schema/examples/` for the three reference profiles, and paste the output into the PR.
10. Ask a non-team member to read the rendered Benadryl-type explanation for a 75-year-old and say it back in their own words. Note the result in the PR.

### Done when
- [ ] A template exists for every dimension at severities 1, 2 and 3, and for every modifier in `docs/scoring/dimensions.md`
- [ ] Every template has a citation slot
- [ ] Every template scores grade 8 or below in the CI readability test
- [ ] Templates render without errors for all five reference products, with output in the PR
- [ ] Interview vocabulary applied, or a follow-up item noted if NOMI-022 hasn't merged

### How to check your work
Run `uv run pytest pipeline/tests/knowledge/test_templates.py`. Change one template to "Hepatotoxicity is potentiated by concomitant ethanol consumption" and rerun: the readability test should fail. Render ZzzQuil for the 65+ profile: the output should mention memory and thinking in plain words and have a citation on every sentence.

### Out of scope
- Showing explanations on the result screen (NOMI-041)
- Packing templates into the dataset file (NOMI-056)
- Deciding severities (NOMI-034, NOMI-035) or points (NOMI-049)
- Running user interviews (NOMI-022)

### Resources
- textstat: https://pypi.org/project/textstat/
- Risk dimensions and modifiers: `docs/scoring/dimensions.md`
- Interview synthesis: `docs/research/interviews-round-1.md`
- Reference products: `packages/schema/examples/`

---

## NOMI-049: Write the rubric v0 specification that turns ratings into a 0-100 score
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S3 | **Depends on:** NOMI-034, NOMI-035

### Summary
Write `docs/rubric/v0.md`: the exact rules that turn each ingredient's severities into points and a 0-100 score for a given profile, including modifiers, hard stops, tiers and the expected scores for the five reference products. It must be precise enough to implement without asking questions and clear enough for a pharmacist to review.

### Why this matters
Rubric v0 is the scoring model for the demo. Every number a user sees comes from it, so it has to be transparent, deterministic and cited. It is reviewed by our faculty partner (NOMI-036) and implemented in Sprint 4 (NOMI-051). It is also written so that the later evidence-based model can replace its weights without changing the app, because the app only adds up points from term tables.

### What you will deliver
- `docs/rubric/v0.md`, merged, with these sections: purpose and principles, points table, modifiers, how dimensions combine, dose and duration, hard stops, efficacy, homeopathic and out-of-scope policy, tiers and wording, monotonicity, worked examples, expected scores for the five reference products, and open questions
- A spreadsheet or small Python script, committed at `docs/rubric/v0_examples.py` (or linked from the shared drive if a spreadsheet), that computes the worked examples so the numbers can be rechecked
- Approval comments from both cofounders on the PR, and the document sent to the faculty partner (through NOMI-036)

### Before you start
- **Rubric**, **severity**, **risk dimension**, **persona**, **profile**, **hard stop**, **term tables**: see the glossary in `docs/nomi-101.md`.
- **Inputs**: the ingredient ratings in `pipeline/knowledge/ingredients/` (NOMI-034, NOMI-035) and the dimension and persona definitions in `docs/scoring/dimensions.md` (NOMI-016).
- **Term tables constraint**: the phone only looks up and adds values (ADR-0001, `docs/adr/0001-architecture.md`; `term-tables` contract in `packages/schema/schemas/`, NOMI-002). So every rule must be computable on the phone with lookups, sums, max or min, and a final clamp to 0-100. No other math.
- **Monotonicity**: more risk can never raise a score. A higher severity, an extra condition or an extra risky ingredient must give the same or a lower score.
- **Invariants NOMI-051 will test**: NSAIDs are never in the top (green) tier for adults 65+ with high blood pressure or kidney disease, and salicylates (such as aspirin) are a hard stop for children. Your rules must guarantee both.
- **Homeopathic products**: shown as "Not evaluated by FDA for safety or effectiveness" and not scored (NOMI-026).
- **Efficacy**: whether the ingredient works for its use. Example: FDA has proposed removing oral phenylephrine from the OTC monograph because it is not effective as a nasal decongestant; confirm the current status on fda.gov before citing it.
- **Reference products and profiles**: `packages/schema/examples/` (NOMI-015) has Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil and a store-brand diphenhydramine, with draft expected scores for three profiles: adult, 65+ with high blood pressure, and child 6-11.
- If NOMI-034 or NOMI-035 hasn't merged, write the rules against the severities in the reference products and update the examples when the knowledge base lands.
- For tier wording, avoid words like "safe" and "unsafe". Check the NOMI-021 legal summary for wording guidance if it's available.

### Steps
1. Write the principles section in a few lines: start at 100 and subtract points; every point traces to a cited severity; rules are deterministic; the phone only adds.
2. Write the points table: points taken off for severity 1, 2 and 3 on each dimension. Start with one base table (for example 0, 5, 15, 35) and a weight per dimension (for example liver and GI bleeding weigh more than local skin irritation), then give the resulting points per severity and dimension. Explain each weight in one line.
3. Define persona handling: severities are already rated per persona in the knowledge base, so state whether points also differ by persona and why.
4. Write the modifier rules: for each condition and medication modifier in `docs/scoring/dimensions.md`, say how it changes points (for example "+1 severity on blood pressure for decongestants and NSAIDs if the profile has hypertension"), with the citation it comes from.
5. Define how dimensions combine within a product: within one dimension, take the highest severity across the product's ingredients (or say how stacking works, for example two sedating ingredients); across dimensions, add the points. State the final clamp to 0-100.
6. Define dose and duration where the label gives them, for example per-dose strength compared with the label's maximum, or label limits such as "stop use if pain gets worse or lasts more than 10 days". Say exactly which fields from label facts (NOMI-045) are used.
7. Define hard stops: which label statements and criteria make a product red regardless of points (for example a "do not use" for the profile's persona, salicylates for children). List each with its source.
8. Define the efficacy dimension: how lack of evidence of effectiveness lowers the score, and its source.
9. Write the homeopathic and out-of-scope policy: not scored, the exact text shown, and that they never appear as alternatives.
10. Define tiers: score bands (for example 75-100, 50-74, 25-49, 0-24), the word shown for each, and the meaning in one sentence. Hard stops always land in the lowest tier.
11. Write the monotonicity rule and show why your rules satisfy it: all points are non-negative deductions, modifiers only raise severity, and combining takes max or sum.
12. Check the two invariants: work through Aleve for a 65+ profile with high blood pressure and confirm it can't reach the top tier; work through an aspirin product for a child 6-11 and confirm it's a hard stop.
13. Compute expected scores for the five reference products for the three profiles with your script or spreadsheet, and put the full working for at least two of them (for example Tylenol and Aleve for the 65+ high blood pressure profile) in the document.
14. List open questions for the faculty partner at the end, for example "Should diphenhydramine be a hard stop for adults 65+ or a large deduction?"
15. Get approval from both cofounders on the PR, then hand the merged document to the NOMI-036 owner to send to the faculty partner.

### Done when
- [ ] `docs/rubric/v0.md` is merged with every section listed in "What you will deliver"
- [ ] Points per severity, dimension and persona, and every modifier, have a stated reason or citation
- [ ] The document states the monotonicity rule and shows the rules satisfy it
- [ ] Expected scores for all five reference products and three profiles are in the document and reproducible with the committed script or linked spreadsheet
- [ ] Worked examples show NSAIDs are never top tier for 65+ with high blood pressure or kidney disease, and salicylates are a hard stop for children
- [ ] Approved by both cofounders on the PR and sent to the faculty partner

### How to check your work
Give the document to a Data Analysis member who didn't write it. Without asking you anything, they should be able to compute the score for NyQuil for the 65+ high blood pressure profile and get the same number as your script. Then raise one severity in a worked example and confirm the score goes down or stays the same.

### Out of scope
- Implementing the rubric and exporting term tables (NOMI-051)
- Combining ingredients into product scores in code and detecting duplicate ingredients across products (NOMI-052)
- Running the faculty review (NOMI-036)
- Benchmarks (NOMI-054) and alternatives (NOMI-055)
- The evidence-synthesis model that replaces these weights (post-demo epic in `planning/post-demo.md`)

### Resources
- Risk dimensions and personas: `docs/scoring/dimensions.md`
- Architecture decision: `docs/adr/0001-architecture.md`
- Knowledge base: `pipeline/knowledge/ingredients/`
- Reference products: `packages/schema/examples/`
- FDA (check current status of monograph changes): https://www.fda.gov/

---

# Sprint 4: Nov 6 to Nov 12 (feature freeze Nov 12)

## NOMI-050: Update the demo script to v2 and announce the feature freeze
**Team:** cofounders | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-004

### Summary
Rewrite `docs/demo/script.md` so it shows only what will really ship on Nov 20, pick the physical boxes we will scan, write down what gets cut if a ticket slips, and announce the feature freeze to the whole team on Nov 12.

### Why this matters
Three sprints in, we know which features are on track and which are not. If the script still promises things that won't exist, teams keep building new features in the last week instead of fixing and rehearsing. Locking the script and the freeze date protects Sprint 5 for bug fixes, the blind test and rehearsals.

### What you will deliver
- `docs/demo/script.md` updated to v2 (a "Version 2" line and date at the top), merged to `main`
- A "Demo boxes" table in the script: product name, store, barcode, which script moment it is used for
- A "Cut list" section in the script: for each at-risk ticket, what we drop or fake if it slips, decided in advance
- A written confirmation from each team lead (Platform, Visualization, Data Analysis) in the PR that their parts of the script are accurate
- A feature freeze announcement posted in the team's main channel on Nov 12

### Before you start
- Read the current `docs/demo/script.md` (v1, from NOMI-004) and the "The demo" section of `docs/nomi-101.md`.
- **Feature freeze** (Nov 12): after this date no new features are merged, only bug fixes, data fixes and polish. **Code freeze** (Nov 17): after this date nothing merges without cofounder approval.
- Key dates already agreed in v1: feature freeze Nov 12, code freeze Nov 17, blind test Nov 18, rehearsals Nov 18-19, demo Nov 20.
- The v1 script has these moments: blind scan in airplane mode; Benadryl for a 30-year-old vs a 75-year-old; Tylenol vs Aleve for a 70-year-old with high blood pressure; NyQuil duplicate-acetaminophen warning; homeopathic and not-found states; data story (coverage dashboard and FAERS signal explorer).
- **Duplicate-acetaminophen warning**: NyQuil contains acetaminophen, so taking it with Tylenol doubles the dose. See NOMI-052.
- **Homeopathic**: products FDA has not evaluated for safety or effectiveness. Nomi shows a notice instead of a score (NOMI-026).
- The Sprint 4 tickets each demo moment depends on: profile switch (NOMI-060, NOMI-061), Tylenol vs Aleve (NOMI-055, NOMI-062), NyQuil warning (NOMI-052), search fallback (NOMI-058, NOMI-063), data story (NOMI-042, NOMI-053, NOMI-071).

### Steps
1. On Nov 6, open each Sprint 4 ticket listed above on the project board and ask its owner in their team channel: "Will this be merged by Nov 12? If not, what part will be?" Record answers in a short table in your PR description.
2. Walk through `docs/demo/script.md` line by line. For each moment, mark it "on track", "at risk" or "cut" based on those answers.
3. Rewrite the script so every line describes something that will exist. Keep the same structure as v1: moment, what the presenter says, what the audience sees, which phone and profile.
4. Choose the demo boxes. For each script moment, pick a real box (for example Benadryl Allergy, Tylenol Extra Strength, Aleve, NyQuil, a homeopathic product, a non-drug barcode for not-found). Scan each one with the current dev build and confirm it resolves. Record product, store, barcode and moment in the "Demo boxes" table. Buy two of each.
5. Write the "Cut list". For each "at risk" moment, write the fallback in one line. Example: "If NOMI-062 slips, skip the comparison screen and show both result screens one after the other."
6. Update the key dates section if anything changed, and add the owner of each date (who runs the blind test, who books the rehearsal room).
7. Open a PR with the script changes. Tag the three team leads and ask each to comment "Confirmed for <team>" or list corrections.
8. Apply corrections until all three leads have confirmed, then merge.
9. On Nov 12, post the freeze announcement in the team's main channel. Include: freeze is in effect now, what can still merge (bug fixes, data fixes, copy and polish), code freeze date Nov 17, a link to the merged script, and who to ask for an exception.

### Done when
- [ ] `docs/demo/script.md` v2 merged, with "Demo boxes" and "Cut list" sections
- [ ] Every moment in the script maps to a merged or in-review ticket, or appears in the cut list
- [ ] Platform, Visualization and Data Analysis leads each confirmed in the PR
- [ ] At least two of each demo box bought and scanned once with the dev build
- [ ] Freeze announcement posted on Nov 12 with a link to the script

### How to check your work
Hand the script to someone who wasn't involved and ask them to point at the ticket behind each moment. If they find a moment with no ticket and no fallback in the cut list, fix the script. Then read only the cut list aloud: every item should be something you could do on stage without new code.

### Out of scope
- Running the blind test and rehearsals (NOMI-064)
- Preparing the demo phones (NOMI-068)
- Fixing UI bugs found in dry runs (NOMI-072)

### Resources
- Current script: `docs/demo/script.md`
- Big picture and glossary: `docs/nomi-101.md`
- Sprint plan: `planning/backlog.md`

---

## NOMI-051: Implement rubric v0 in Python and export term tables
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-049, NOMI-002

### Summary
Turn the written rubric (`docs/rubric/v0.md`) into deterministic Python code in `pipeline/src/nomi_pipeline/score/`, export it as term tables and hard-stop rules in the `term-tables` format, and protect it with invariant tests and 30 golden vectors.

### Why this matters
This is the scoring model. The phone never runs a model: it only looks up and adds the points that this code exports. So every score a user sees comes from here. If the code doesn't match the rubric, or breaks a basic safety rule (like rating an NSAID green for a 75-year-old with kidney disease), the app will show it.

### What you will deliver
- `pipeline/src/nomi_pipeline/score/rubric.py`: scores one ingredient for one profile, following `docs/rubric/v0.md`
- `pipeline/src/nomi_pipeline/score/term_tables.py`: exports term tables and hard-stop rules to `data/gold/term_tables.json`, valid against `packages/schema/schemas/term-tables`
- A CLI step: `uv run pipeline score terms`
- `pipeline/tests/score/test_invariants.py` with the invariant and Hypothesis property tests
- `packages/schema/golden/vectors.json` with 30 golden vectors

### Before you start
- **Rubric**: the written rules that turn severities into points and a 0-100 score. Read all of `docs/rubric/v0.md` (NOMI-049) first.
- **Severity**: a 0-3 rating of one ingredient on one risk dimension for one persona, stored in the knowledge base YAML in `pipeline/knowledge/ingredients/` (NOMI-034, NOMI-035).
- **Persona / profile / risk dimension / hard stop**: see the glossary in `docs/nomi-101.md`. A hard stop makes a product red regardless of points.
- **Term tables**: the rubric written as lookup rows: "this ingredient, this dimension, this persona (and optional condition) costs N points." The phone sums matching rows. If a rule can't be written as an additive row or a hard stop, the phone can't run it, so raise it with the NOMI-049 owner.
- **Golden vector**: a test case of (product, profile, expected score) that both Python and the phone must reproduce exactly (checked in CI by NOMI-057).
- **Monotonicity**: more risk can never raise a score. Adding a condition, raising a severity or adding an ingredient must never increase the score.
- **Hypothesis**: a Python library for property-based tests. It generates many random inputs and checks that a rule always holds.
- **Salicylates**: aspirin and related ingredients such as bismuth subsalicylate (in Pepto-Bismol). Linked to Reye's syndrome in children.
- If NOMI-049 isn't approved yet, code against the latest draft and keep a list of open questions in the PR. If the knowledge base files are incomplete, use the five reference products in `packages/schema/examples/` (NOMI-015) as input.
- NOMI-052 (product aggregation) builds on your ingredient scoring. Agree the function signature with its owner on day one.

### Steps
1. Read `docs/rubric/v0.md` and list every rule as one line in a scratch table: rule, input fields, output (points, hard stop, tier). Mark any rule that is not additive.
2. Write a loader in `pipeline/src/nomi_pipeline/score/knowledge.py` that reads every YAML file in `pipeline/knowledge/ingredients/` into Pydantic models from `packages/schema/generated/`.
3. Implement `score_ingredient(ingredient, profile) -> IngredientScore` in `rubric.py`. Return points per dimension, hard stops triggered, and the citation behind each non-zero value. No randomness, no dict-order dependence, no floating-point rounding surprises (round once, at the end, as the rubric says).
4. Implement the export in `term_tables.py`: for every ingredient, dimension, persona and condition or medication modifier, write one row with its points; write hard-stop rules separately; include `model_version` (for example `rubric-v0.1`).
5. Validate the export against the `term-tables` JSON Schema in the export function, and fail loudly if it doesn't match.
6. Register `uv run pipeline score terms` to run the export and write `data/gold/term_tables.json`.
7. Write invariant tests in `pipeline/tests/score/test_invariants.py`:
   - NSAIDs (ibuprofen, naproxen, aspirin) are never in the green tier for the 65+ persona with high blood pressure or with kidney disease.
   - Salicylates are a hard stop for the child personas defined in the rubric.
8. Write Hypothesis property tests for monotonicity: for random profiles and ingredients, adding a condition, adding a medication type or raising any severity by 1 never raises the score.
9. Write a parity test that scores a profile two ways, directly with `rubric.py` and by summing the exported term-table rows, and asserts they are equal. This is what makes the phone's job possible.
10. Create `packages/schema/golden/vectors.json` with 30 vectors. Each has `id`, `product` (NDC11 or reference product id), `profile` (persona, conditions, medication types), `expected_score`, `expected_tier`, `expected_hard_stops`. Cover all five reference products, every persona at least once, and the demo cases: Benadryl for 30 vs 75, Tylenol vs Aleve for a 70-year-old with high blood pressure.
11. Ask a cofounder to review the 30 vectors against the rubric and record their approval in the PR.

### Done when
- [ ] `uv run pipeline score terms` writes `data/gold/term_tables.json` that validates against the `term-tables` schema
- [ ] Same input gives byte-identical output on two runs
- [ ] NSAID and salicylate invariant tests pass
- [ ] Hypothesis monotonicity tests pass
- [ ] Direct scoring equals summed term tables for every golden vector
- [ ] 30 golden vectors in `packages/schema/golden/`, reviewed by a cofounder in the PR

### How to check your work
Run `uv run pytest pipeline/tests/score`. Then run the export twice and compare with `shasum data/gold/term_tables.json`. Finally, by hand, score Benadryl for a 30-year-old and a 75-year-old: the 75-year-old must score lower because of the anticholinergic dimension (diphenhydramine is rated 3 on the ACB scale). If not, recheck the rubric and the knowledge base.

### Out of scope
- Combining ingredients into product scores and duplicate detection (NOMI-052)
- Benchmarks (NOMI-054) and alternatives (NOMI-055)
- The CI job comparing Python and TypeScript (NOMI-057)
- The phone's scoring engine (NOMI-060)
- Expanding to 100 golden vectors (NOMI-074)

### Resources
- Rubric: `docs/rubric/v0.md`
- Dimensions and personas: `docs/scoring/dimensions.md`
- Schemas: `packages/schema/schemas/`
- Hypothesis docs: https://hypothesis.readthedocs.io/
- Pydantic docs: https://docs.pydantic.dev/

---

## NOMI-052: Score combination products and detect duplicate ingredients
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-051 (same sprint)

### Summary
Write the code that combines the scores of each ingredient in a product into one product score, handles stacking risks inside a product (such as two sedating ingredients), and detects when two products share an active ingredient.

### Why this matters
Many top sellers contain several active ingredients. NyQuil has acetaminophen, dextromethorphan and doxylamine. Someone who takes NyQuil and Tylenol together doubles their acetaminophen without knowing it, which is a real cause of liver injury. The NyQuil duplicate warning is a demo moment, and combination products are where a single-ingredient score would be wrong.

### What you will deliver
- `pipeline/src/nomi_pipeline/score/product.py` with `score_product(product, profile) -> ProductScore`
- `pipeline/src/nomi_pipeline/score/duplicates.py` with `find_duplicates(products: list[Product]) -> list[DuplicateWarning]`
- Golden vectors for combination products added to `packages/schema/golden/vectors.json`
- Tests in `pipeline/tests/score/test_product.py` and `pipeline/tests/score/test_duplicates.py`

### Before you start
- **Active ingredient**, **risk dimension**, **profile**, **term tables**, **golden vectors**: see the glossary in `docs/nomi-101.md`.
- **Combination product**: a product with more than one active ingredient. Demo examples: NyQuil (acetaminophen, dextromethorphan, doxylamine), Tylenol PM (acetaminophen, diphenhydramine), Advil PM (ibuprofen, diphenhydramine), Excedrin (acetaminophen, aspirin, caffeine). Confirm exact ingredients and strengths on DailyMed for the product versions you test.
- **Stacking**: two ingredients in one product hitting the same dimension, for example two sedating or two anticholinergic ingredients. The rubric (`docs/rubric/v0.md`) says how dimensions combine; follow it exactly.
- **Duplicate ingredient**: the same active ingredient (same UNII, FDA's ingredient ID) in two different products. The same function will be reused by the post-demo Medicine Cabinet feature (see `planning/post-demo.md`), so it must take a list of products, not just two.
- **Agree the interface with the NOMI-051 owner on day one**: what `score_ingredient` returns and how you call it. Write the agreed signatures in both PR descriptions.
- If NOMI-051 hasn't merged, write a stub `score_ingredient` that returns fixed points per dimension and code against it. Use the five reference products in `packages/schema/examples/` (NOMI-015) as input.
- Every combination rule must still be expressible as term-table rows or hard stops, because the phone only adds rows. If it isn't, flag it to the NOMI-051 owner.

### Steps
1. Read the "how dimensions combine" section of `docs/rubric/v0.md` and write down, in the PR, the exact rule for: summing across ingredients, stacking within one dimension, and caps if any.
2. Implement `score_product` in `product.py`: call `score_ingredient` for each active ingredient, combine per dimension according to the rubric, apply hard stops from any ingredient, and return total score, tier, contribution per dimension and the ingredient behind each contribution.
3. Implement stacking: when two or more ingredients in the product hit the same dimension (for example sedation/falls from doxylamine and diphenhydramine-type ingredients), apply the rubric's stacking rule. Add a test with a constructed product that has two sedating antihistamines.
4. Implement `find_duplicates` in `duplicates.py`: group active ingredients by UNII across the given products and return a warning for each UNII that appears in more than one product, with the product names and per-product strengths.
5. Add a `max_daily_dose` note where label facts are available (from `data/silver/label_facts.parquet`, NOMI-045), so the warning can say each product's own limit. If label facts aren't available, leave the field empty.
6. Make sure the outputs can be exported for the phone: write combination and stacking points into the term-table export (coordinate with NOMI-051) so the phone gets the same answer by summing rows.
7. Add golden vectors for NyQuil, Tylenol PM, Advil PM and Excedrin, each for at least two profiles (an adult 18-64 and a 65+ with high blood pressure), to `packages/schema/golden/vectors.json`.
8. Add a duplicate test: NyQuil plus Tylenol Extra Strength must return one warning for acetaminophen; Advil PM plus Tylenol PM must return one warning for diphenhydramine (the UNII must match even if the salt differs; check how NOMI-010 stores salts and document the rule you use).
9. Run `uv run pytest pipeline/tests/score` and fix failures.

### Done when
- [ ] `score_product` returns a score, tier and per-dimension contribution for every reference product
- [ ] Stacking test with two sedating ingredients passes
- [ ] Golden vectors for NyQuil, Tylenol PM, Advil PM and Excedrin added and passing
- [ ] NyQuil + Tylenol returns an acetaminophen duplicate warning; a product list with no shared ingredient returns none
- [ ] Interface agreed with the NOMI-051 owner and written in the PR

### How to check your work
Run `uv run pytest pipeline/tests/score`. Then print the per-dimension contributions for NyQuil for a 75-year-old: you should see contributions from at least liver (acetaminophen) and sedation or anticholinergic (doxylamine). If one ingredient is missing, your loop over active ingredients is wrong.

### Out of scope
- Ingredient-level scoring and the base term-table export (NOMI-051)
- Showing duplicate warnings in the app (post-demo Medicine Cabinet, `planning/post-demo.md`)
- Choosing alternatives (NOMI-055)

### Resources
- Rubric: `docs/rubric/v0.md`
- DailyMed (to confirm ingredients and strengths): https://dailymed.nlm.nih.gov/dailymed/

---

## NOMI-053: Compute FAERS signals and map them to risk dimensions
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-044, NOMI-046

### Summary
Compute disproportionality signals (IC and IC025) from FAERS for each ingredient and event group, split by age band and sex, map them to Nomi's risk dimensions, and write `data/gold/signal.parquet` plus a short write-up of the method and its limits.

### Why this matters
FAERS is our real-world evidence layer and the core of the demo's data story. It can't tell us how often a drug causes harm, but it can show which problems get reported with an ingredient more often than expected. Shrinkage keeps rare ingredients from producing noisy, misleading signals. The signal explorer (NOMI-071) and the validation note (NOMI-076) read this table.

### What you will deliver
- `pipeline/src/nomi_pipeline/evidence/signals.py` with the IC computation
- `uv run pipeline evidence signals` writing `data/gold/signal.parquet`, matching the `signal` schema in `packages/schema/schemas/`
- `pipeline/docs/signals.md` with "Method" and "Limitations" sections
- Tests in `pipeline/tests/evidence/test_signals.py`

### Before you start
- **FAERS**: FDA's database of adverse event reports. It has no denominator: we don't know how many people took a drug without a problem, so we can't compute risk rates.
- **Event group**: a set of MedDRA reaction terms that belong to one of our risk dimensions (for example "hepatic failure" and related terms for liver). The groups and their dimension mapping come from NOMI-044.
- **MedDRA**: the medical vocabulary FAERS uses for reactions.
- **Disproportionality**: comparing how often a reaction is reported with a drug to how often you'd expect if the drug and reaction were unrelated.
- **IC (information component)** from **BCPNN** (Bayesian Confidence Propagation Neural Network, the method the WHO's Uppsala Monitoring Centre uses): a log2 ratio of observed to expected reports, shrunk toward 0 when counts are small. A commonly used form is `IC = log2((observed + 0.5) / (expected + 0.5))`, where `expected = (reports with the drug) x (reports with the event) / (total reports)`.
- **IC025**: the lower end of the 95% credibility interval for IC. IC025 above 0 counts as a signal. Use the closed-form approximation from Noren et al. (2013) or compute it from the gamma/beta posterior; confirm the formula you use in the paper before coding, and cite it in `pipeline/docs/signals.md`.
- Inputs: `data/silver/faers_pairs.parquet` (NOMI-044; one row per case, drug and reaction, with age band 0-11, 12-17, 18-64, 65+ and sex, primary and secondary suspect drugs only) and ingredient ids on drug rows (NOMI-046).
- If NOMI-044 or NOMI-046 hasn't merged, build a small fixture in `pipeline/tests/fixtures/faers_pairs_sample.parquet` with a few thousand synthetic rows where you know the answer (for example one drug-event pair planted at 5x the expected rate) and develop against it.
- Polars or DuckDB both work for the counting. Keep it to one pass per grouping.

### Steps
1. Write the test first in `test_signals.py`: on your fixture, the planted pair must have IC025 > 0 and an unrelated pair must not.
2. In `signals.py`, compute counts per (ingredient, event group, age band, sex): observed reports with both, reports with the ingredient, reports with the event group, total reports in that stratum. Count each case once per pair (use case id, not rows).
3. Compute `expected`, `IC` and `IC025` per row using the formula you confirmed in the paper. Also compute and store the totals for "all ages" and "all sexes" so the explorer can show unstratified values.
4. Map event groups to risk dimensions using the mapping from NOMI-044 and add a `dimension` column.
5. Write the output with the columns the `signal` schema requires: ingredient, dimension, age band, sex, IC, IC025, report count. Validate it against the schema in the CLI step.
6. Register `uv run pipeline evidence signals` and run it on the full data.
7. Run the sanity checks and record the IC025 values in the PR: acetaminophen and liver; NSAIDs (ibuprofen, naproxen, aspirin) and GI bleeding; NSAIDs and kidney; diphenhydramine and cognition in the 65+ band.
8. Write `pipeline/docs/signals.md` with a "Method" section (inputs, formula, citation, strata, minimum counts) and a "Limitations" section covering at least: no denominator; masking (a drug with very many reports of a reaction can hide signals for other drugs); notoriety bias (publicity about a risk increases reporting of it); duplicate and incomplete reports; reports show association, not cause.

### Done when
- [ ] `data/gold/signal.parquet` written by `uv run pipeline evidence signals` and valid against the `signal` schema
- [ ] Fixture test passes: the planted pair is a signal, the unrelated pair is not
- [ ] All four sanity checks show IC025 > 0, with values recorded in the PR (or a documented reason if one doesn't)
- [ ] `pipeline/docs/signals.md` has Method and Limitations sections with the IC formula cited

### How to check your work
Run `uv run pytest pipeline/tests/evidence`. Then open the output in DuckDB, for example `duckdb -c "select * from 'data/gold/signal.parquet' where ingredient = 'acetaminophen' and dimension = 'liver'"`, and check the IC025 is above 0 and the report count matches a manual count from `faers_pairs.parquet`.

### Out of scope
- Building FAERS pair tables (NOMI-044) and mapping drug names to ingredients (NOMI-046)
- Using signals to change severities or scores (rubric work, NOMI-049; not part of v0)
- The signal explorer page (NOMI-071)
- Validation against known risks and a reference set (NOMI-076)

### Resources
- FAERS quarterly data files: https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html
- FAERS overview: https://www.fda.gov/drugs/surveillance/fdas-adverse-event-reporting-system-faers
- Polars docs: https://docs.pola.rs/
- DuckDB docs: https://duckdb.org/docs/

---

## NOMI-054: Export category benchmark breakpoints per use and persona
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-047, NOMI-051 (same sprint)

### Summary
Compute the score distribution of all in-scope products for each use (pain, sleep, heartburn...) and each persona, and export percentile breakpoints so the phone can say "Better than 82% of pain relievers for you."

### Why this matters
A score of 64 means little on its own. Comparing it with other products used for the same purpose gives it meaning. Because the final score is personalized on the phone, we can't ship a fixed percentile per product; we ship the breakpoints of each distribution and the phone places the user's score on it.

### What you will deliver
- `pipeline/src/nomi_pipeline/score/benchmarks.py`
- `uv run pipeline score benchmarks` writing `data/gold/benchmarks.parquet`
- Tests in `pipeline/tests/score/test_benchmarks.py`
- A spot-check table of 10 benchmarks in the PR description

### Before you start
- **Benchmark**: a product's rank among products with the same use, for the same persona.
- **Use**: what a product is for, from the uses classifier (NOMI-047), stored as a `uses` list on each product. A product can have several uses; it appears in each use's distribution.
- **Persona**: see the glossary in `docs/nomi-101.md`.
- **Percentile breakpoint**: the score at a given percentile of a distribution. If you export the score at every 5th percentile (p0, p5, ..., p100, 21 values), the phone can find where any score falls by interpolating between the two nearest breakpoints.
- Rule from the backlog: never compare across different uses. A sleep aid is never benchmarked against antacids.
- Products flagged homeopathic or out of scope (NOMI-026) are not scored, so leave them out.
- If NOMI-047 hasn't merged, use the OTC category from NOMI-026 as a temporary stand-in for use, and switch once uses land. If NOMI-051 / NOMI-052 haven't merged, use a stub score function and the reference products in `packages/schema/examples/` to build the pipeline end to end.

### Steps
1. Write `benchmarks.py` to load all in-scope products with their `uses` and score each product for each persona with no conditions, using the product scoring from NOMI-052.
2. For each (use, persona), compute the score at percentiles 0, 5, 10, ..., 100 and the number of products `n`.
3. Skip any (use, persona) with fewer than 5 products and log them; a percentile over 3 products is misleading. Record the skipped list in the PR.
4. Write `data/gold/benchmarks.parquet` with columns `use`, `persona`, `n`, `breakpoints` (list of 21 scores in ascending order), `model_version`.
5. Add a helper `percentile_for(score, breakpoints) -> float` in the same file. It mirrors what the phone does in NOMI-060, and tests use it.
6. Write tests: breakpoints are non-decreasing; a product's own score maps to its rank within one breakpoint step; no row mixes two uses.
7. Register `uv run pipeline score benchmarks` and run it on the full product table.
8. Confirm every use in the demo aisles (pain, fever, nasal allergy, sleep, cough, congestion, heartburn, constipation, diarrhea and the others from NOMI-047 in those aisles) has breakpoints for at least the adult 18-64 and 65+ personas.
9. Spot-check 10 benchmarks by hand: pick 10 (product, use, persona) combinations, compute the rank manually in a spreadsheet or DuckDB, and compare with `percentile_for`. Put the 10 rows in the PR.

### Done when
- [ ] `data/gold/benchmarks.parquet` written by `uv run pipeline score benchmarks`
- [ ] Every use in the demo aisles has breakpoints for adult 18-64 and 65+
- [ ] No benchmark row combines more than one use (test passes)
- [ ] Breakpoints are non-decreasing (test passes)
- [ ] 10 hand spot-checks in the PR, each within one breakpoint step of the computed value

### How to check your work
Run `uv run pytest pipeline/tests/score/test_benchmarks.py`. Then look up Tylenol Extra Strength for the pain use and the adult persona and compute its percentile; it should be plausible next to Advil and Aleve for the same persona. Check that the sleep use only contains sleep products by listing them in DuckDB.

### Out of scope
- Classifying uses (NOMI-047)
- Shipping benchmarks in the SQLite dataset (NOMI-056)
- Computing the percentile on the phone (NOMI-060) and showing it (NOMI-061)

### Resources
- Uses taxonomy: see NOMI-047 output in `data/silver/`
- Polars docs (quantile): https://docs.pola.rs/
- DuckDB docs: https://duckdb.org/docs/

---

## NOMI-055: Precompute safer alternatives and tradeoff summaries
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-047, NOMI-052 (same sprint)

### Summary
For every in-scope product, precompute a list of alternative products that share a use, with a summary of which risk dimensions differ, and an "ask your pharmacist" fallback when no candidate exists. The phone ranks the list for the active profile.

### Why this matters
Telling someone a product is risky for them is only half useful; the other half is a safer option for the same purpose. The comparison screen (NOMI-062) and the Tylenol vs Aleve demo moment use this data. When no OTC product is clearly better, the honest answer is "ask your pharmacist," and we must never suggest something for a different purpose (ZzzQuil must never suggest Claritin).

### What you will deliver
- `pipeline/src/nomi_pipeline/score/alternatives.py`
- `uv run pipeline score alternatives` writing `data/gold/alternatives.parquet`
- Tests in `pipeline/tests/score/test_alternatives.py`
- A review sheet of 30 hand-checked products with verdicts, linked in the PR

### Before you start
- **Use**: what a product is for (NOMI-047). Alternatives must share at least one use with the scanned product.
- **Risk dimension**, **profile**, **persona**: see the glossary in `docs/nomi-101.md`.
- **Tradeoff summary**: for a pair of products, the dimensions where they differ. Example for a 70-year-old with high blood pressure: Aleve scores worse on GI bleeding, blood pressure and kidney; Tylenol scores worse on liver at high doses.
- Why the pipeline precomputes and the phone ranks: the user's conditions never leave the phone, so the pipeline can't know the final ranking. It ships a candidate list with per-dimension points for each persona, and the phone re-scores and sorts them (NOMI-060, NOMI-062).
- Preference rule: prefer single-ingredient products. A single ingredient avoids exposing the user to ingredients they don't need.
- ZzzQuil is a sleep aid (diphenhydramine); Claritin is an allergy medicine (loratadine). They don't share a use.
- If NOMI-047 hasn't merged, use the OTC category from NOMI-026 as a stand-in and switch later. If NOMI-052 hasn't merged, use a stub score and the reference products in `packages/schema/examples/`.

### Steps
1. In `alternatives.py`, for each in-scope product, find all other in-scope products that share at least one use.
2. Exclude candidates with any hard stop for the persona being considered, and exclude products with the same set of active ingredients (a different brand of the same thing isn't an alternative).
3. Score each candidate per persona (no conditions) using NOMI-052. Keep the top 10 candidates per product and persona by score, breaking ties in favor of single-ingredient products, then by fewer active ingredients.
4. For each (product, candidate) pair, compute the tradeoff summary: list of dimensions where points differ, with the direction (better or worse) and size. Store it as structured data, not prose, so templates (NOMI-048) can render it.
5. Add a `shared_use` field to each pair, and a `fallback` field on each product: `ask_pharmacist` when no candidate is better than the product for that persona, or when there are no candidates.
6. Write `data/gold/alternatives.parquet` with columns `ndc11`, `persona`, `candidate_ndc11`, `rank`, `shared_use`, `single_ingredient`, `tradeoffs`, `fallback`, `model_version`.
7. Write tests: every candidate shares a use with its product; ZzzQuil's candidates never include Claritin or any product without the sleep use; a product with no same-use products gets `ask_pharmacist`.
8. Register `uv run pipeline score alternatives` and run it.
9. Pick 30 products across the demo aisles (include Tylenol, Aleve, ZzzQuil, NyQuil, Benadryl). For each, look at the top 3 alternatives for the adult and 65+ personas and mark "sensible" or "not sensible" with a reason in a sheet. Fix rules (not individual products) for any "not sensible" result and recheck.

### Done when
- [ ] `data/gold/alternatives.parquet` written by `uv run pipeline score alternatives`
- [ ] Shared-use test and ZzzQuil-never-Claritin test pass
- [ ] Products with no better candidate have `fallback = ask_pharmacist`
- [ ] 30 hand-checked products reviewed, all judged sensible after fixes, sheet linked in the PR

### How to check your work
Run `uv run pytest pipeline/tests/score/test_alternatives.py`. Then query Aleve's alternatives for the 65+ persona; a single-ingredient acetaminophen product should appear near the top, with tradeoffs showing GI bleeding, blood pressure and kidney better and liver worse or equal.

### Out of scope
- Classifying uses (NOMI-047)
- Ranking for the active profile on the phone and the comparison screen (NOMI-060, NOMI-062)
- Shipping the data in SQLite (NOMI-056)
- Explanation wording (NOMI-048)

### Resources
- Rubric: `docs/rubric/v0.md`
- Dimensions: `docs/scoring/dimensions.md`
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/

---

## NOMI-056: Add scores, benchmarks and alternatives to the SQLite dataset (builder v2)
**Team:** platform | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-038, NOMI-051 (same sprint)

### Summary
Extend `uv run pipeline build` so `nomi.sqlite` contains everything the phone needs to score and compare products: term tables, hard stops, dimension rows, benchmark breakpoints, alternative candidates and explanation templates. Keep it under 20 MB compressed and rebuild it nightly during the sprint.

### Why this matters
The app works offline because the whole dataset ships inside it as one SQLite file. Version 1 (NOMI-038) has products and label facts but nothing to score with. Without this ticket, the scoring engine (NOMI-060) and the result screens have no data. A nightly rebuild keeps the app team testing on fresh data instead of last week's.

### What you will deliver
- New tables in the builder in `pipeline/src/nomi_pipeline/build/`: `term`, `hard_stop`, `dimension`, `benchmark`, `alternative`, `template`
- `data/build/nomi.sqlite` and its manifest, with compressed size recorded in the manifest
- A schema validation step that runs at the end of every build
- A scheduled GitHub Actions workflow `.github/workflows/nightly-dataset.yml` that rebuilds and publishes to R2 every night until Nov 12

### Before you start
- **Term tables**, **hard stop**, **risk dimension**, **benchmark**, **R2**: see the glossary in `docs/nomi-101.md`.
- Inputs and who makes them: term tables and hard stops in `data/gold/term_tables.json` (NOMI-051); combination rows (NOMI-052); benchmark breakpoints in `data/gold/benchmarks.parquet` (NOMI-054); alternatives in `data/gold/alternatives.parquet` (NOMI-055); templates in `pipeline/knowledge/templates/` (NOMI-048); dimension definitions from `docs/scoring/dimensions.md` (NOMI-016).
- **Manifest**: the JSON file next to `nomi.sqlite` with dataset version, input hashes and code commit (NOMI-038). You add size fields.
- If an input hasn't merged, create a small fixture in the same shape (for example `pipeline/tests/fixtures/term_tables_sample.json` built from the reference products in `packages/schema/examples/`) and build from it. Each table must exist in the SQLite file even if it holds fixture data, so the app team can code against it.
- R2 write credentials are for CI only (NOMI-008). Store them as GitHub Actions secrets, never in the repo.

### Steps
1. Write the SQLite DDL for the six new tables in `pipeline/src/nomi_pipeline/build/schema.sql`. Use integer keys and short codes for dimensions and personas to keep the file small. Add indexes on the columns the phone queries: `term(ingredient_id, persona)`, `alternative(ndc11, persona)`, `benchmark(use, persona)`.
2. Agree the table shapes with the NOMI-060 owner on day one and paste the DDL in both PRs.
3. Load each input and insert it in the build step. Store benchmark breakpoints and tradeoffs as compact JSON text or a child table; pick one and document it in `schema.sql` comments.
4. Add a validation step: after the build, export a sample of rows from each table and validate them against the matching JSON Schemas in `packages/schema/schemas/`. Fail the build if any row is invalid.
5. Compress the file the same way the app download will use (for example `gzip -9`) and write `size_bytes` and `compressed_size_bytes` into the manifest.
6. Fail the build if the compressed size is over 20 MB. If you're over, drop unused columns, normalize repeated strings into lookup tables, and run `VACUUM` before measuring.
7. Write `.github/workflows/nightly-dataset.yml` with a `schedule` trigger (for example `cron: "0 8 * * *"`, which is 08:00 UTC) that runs `uv run pipeline build`, uploads `nomi.sqlite` and the manifest to R2 under a dated path, and posts the size in the job summary.
8. Tell the Visualization team the R2 path and how to pull the latest build into `apps/mobile/assets/nomi.sqlite`.

### Done when
- [ ] `nomi.sqlite` contains `term`, `hard_stop`, `dimension`, `benchmark`, `alternative` and `template` tables
- [ ] Build fails on any schema validation error (shown by a test that feeds one bad row)
- [ ] Manifest records `size_bytes` and `compressed_size_bytes`, and compressed size is at most 20 MB
- [ ] Nightly workflow ran successfully at least twice and uploaded to R2
- [ ] Table DDL agreed with the NOMI-060 owner

### How to check your work
Run `uv run pipeline build`, then `sqlite3 data/build/nomi.sqlite ".tables"` and confirm all new tables appear. Run `sqlite3 data/build/nomi.sqlite "select count(*) from term"` and check it isn't 0. Open the manifest and confirm the compressed size. Check the Actions tab for green nightly runs.

### Out of scope
- Computing term tables, benchmarks or alternatives (NOMI-051, NOMI-054, NOMI-055)
- The name search index (NOMI-058)
- Release runs and diff reports (NOMI-059)
- Further size and query tuning on low-end phones (NOMI-067)

### Resources
- Builder v1: `pipeline/src/nomi_pipeline/build/` (NOMI-038)
- SQLite docs: https://www.sqlite.org/docs.html
- GitHub Actions scheduled workflows: https://docs.github.com/en/actions
- Cloudflare R2: https://developers.cloudflare.com/r2/

---

## NOMI-057: Add a CI job that checks Python and TypeScript scores match on golden vectors
**Team:** platform | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-051 (same sprint)

### Summary
Build a GitHub Actions job that runs every golden vector in `packages/schema/golden/` through the Python scoring code and the TypeScript evaluator on the phone side, and fails with a clear diff if any score differs.

### Why this matters
The same score is computed twice: in Python in the pipeline, and in TypeScript on the phone. The numbers we check and review come from Python, but users see the TypeScript result. If the two ever disagree, a user sees a number nobody checked. This job makes such a change impossible to merge.

### What you will deliver
- `pipeline/tests/golden/run_python.py` that writes `python-results.json` (vector id, score, tier, hard stops)
- `apps/mobile/src/scoring/__tests__/golden.test.ts` (or a script) that writes `ts-results.json` in the same shape
- `scripts/compare_golden.py` that compares the two files and prints a table of mismatches
- `.github/workflows/golden-parity.yml` that runs all three and fails on any mismatch

### Before you start
- **Golden vectors**: test cases of (product, profile, expected score) in `packages/schema/golden/vectors.json`, created in NOMI-051 and extended in NOMI-052.
- **Term tables**: the exported scoring lookup rows the phone adds up. The TypeScript evaluator sums term-table rows; the Python side uses the rubric code. If they agree on every vector, the export is correct.
- The TypeScript evaluator is built in NOMI-060 (same sprint) in `apps/mobile/src/scoring/`. If it hasn't merged, write a minimal evaluator in the test file that sums term-table rows for a profile and applies hard stops, and replace it with the NOMI-060 import when it lands. Agree the function name with the NOMI-060 owner (for example `scoreProduct(termTables, product, profile)`).
- If NOMI-051 hasn't merged, create 3 vectors by hand from the reference products in `packages/schema/examples/` with a matching tiny term-table fixture.
- CI conventions (path filters, caching) come from NOMI-001; follow the existing workflows in `.github/workflows/`.

### Steps
1. Write `run_python.py`: load `vectors.json`, score each vector with the NOMI-051/NOMI-052 Python code, and write `python-results.json` with `id`, `score`, `tier`, `hard_stops` (sorted list).
2. Write the TypeScript side: load the same `vectors.json` and the exported term tables (`data/gold/term_tables.json` or a committed fixture copy in `packages/schema/golden/term_tables.json`), score each vector, and write `ts-results.json` in the same shape.
3. Decide how the term tables reach CI. The simplest option: commit a small term-table export for the golden products only to `packages/schema/golden/term_tables.json`, regenerated by `uv run pipeline score terms --golden`. Document the regenerate command in `packages/schema/README.md`.
4. Write `compare_golden.py`: for every id, compare Python vs TypeScript vs `expected_score` in the vector. Print a table with columns `id`, `product`, `profile`, `expected`, `python`, `typescript`, and exit non-zero on any mismatch or missing id.
5. Write `.github/workflows/golden-parity.yml`: trigger on PRs that touch `pipeline/src/nomi_pipeline/score/**`, `apps/mobile/src/scoring/**` or `packages/schema/golden/**`; install uv and pnpm; run the three scripts; print the table in the job summary.
6. Make the job a required check on `main` (ask a cofounder, who has admin rights).
7. Prove it fails: on a throwaway branch, change one `expected_score` by 1, open a draft PR, and confirm the job goes red with that vector in the table. Link the run in your PR and close the throwaway PR.

### Done when
- [ ] The workflow runs on every PR that touches scoring or golden vectors
- [ ] Any mismatch between Python, TypeScript or expected values fails the job
- [ ] Failure output is a table naming each mismatched vector and the three values
- [ ] A deliberate mismatch run is linked in the PR showing the job fail
- [ ] The job is a required status check on `main`

### How to check your work
Run the three steps locally: `uv run python pipeline/tests/golden/run_python.py`, the TypeScript test command, then `uv run python scripts/compare_golden.py`. You should see "30 of 30 match" (or the current count). Edit one expected score locally and rerun; you should see one row in the mismatch table and a non-zero exit code.

### Out of scope
- Writing the golden vectors (NOMI-051, NOMI-052; expanded in NOMI-074)
- Building the on-device scoring engine (NOMI-060)
- Release diff reports (NOMI-059)

### Resources
- GitHub Actions docs: https://docs.github.com/en/actions
- uv docs: https://docs.astral.sh/uv/
- Golden vectors: `packages/schema/golden/`

---

## NOMI-058: Build an offline name search index (SQLite FTS5) into the dataset
**Team:** platform | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-038

### Summary
Add a full-text search index to `nomi.sqlite` that finds products by brand, generic or ingredient name, ranks common products first, and returns results in under 50 ms on a phone. The app's search screen (NOMI-063) uses it.

### Why this matters
Some boxes won't scan: crumpled packaging, glare, or barcodes we can't resolve. Searching by name is the fallback, and it has to work offline like everything else. In the demo, a box from the audience that fails to scan should still be findable in seconds.

### What you will deliver
- A `product_search` FTS5 virtual table created in the builder in `pipeline/src/nomi_pipeline/build/`
- A `popularity` value per product used for ranking
- A search query function `search_products(conn, text, limit=10)` in `pipeline/src/nomi_pipeline/build/search.py` with the exact SQL the app will use
- `pipeline/tests/fixtures/search_queries.csv` with 20 test queries and expected products
- Tests in `pipeline/tests/build/test_search.py`

### Before you start
- **SQLite FTS5**: SQLite's built-in full-text search extension. You create a virtual table, insert text, and query it with `MATCH`. It supports prefix search (`tylen*`) and a relevance function, `bm25()`.
- **Brand / generic / ingredient name**: "Advil" is a brand, "ibuprofen tablets" a generic name, "ibuprofen" the active ingredient. Store brands (CVS Health, Equate, Up&Up) use the generic name plus a store name.
- Inputs: product, ingredient and name columns already in `nomi.sqlite` from NOMI-038.
- **Popularity**: we have no sales data. Use a proxy, for example the number of package NDCs for the product plus a bonus if the product appears in the ground-truth barcodes (`pipeline/tests/fixtures/barcodes.csv`, NOMI-020). Document the proxy you choose.
- Confirm that the SQLite version in expo-sqlite on the phone includes FTS5 before relying on it (check the expo-sqlite docs, then test on a dev build).
- If NOMI-038 hasn't merged, build a small SQLite file from the reference products in `packages/schema/examples/` plus 50 products you add by hand, and develop against it.

### Steps
1. Write `search_queries.csv` first: 20 rows with `query` and `expected_ndc11_or_name`. Include brand names (`tylenol`, `advil pm`, `zzzquil`, `nyquil`), ingredients (`diphenhydramine`, `loratadine`), store brands (`cvs allergy`, `equate ibuprofen`), partial words (`benadr`) and mixed case.
2. Add `product_search` to the builder: `CREATE VIRTUAL TABLE product_search USING fts5(brand, generic, ingredients, labeler, content='', tokenize='unicode61 remove_diacritics 2', prefix='2 3')`, with `rowid` equal to the product's integer id. Adjust columns to match NOMI-038's tables.
3. Compute `popularity` per product and store it in the products table.
4. Write the query in `search.py`: turn user text into an FTS5 query by splitting on spaces and adding `*` to the last token; order by `bm25(product_search, 10.0, 5.0, 5.0, 1.0)` combined with popularity (for example `bm25(...) - 0.5 * log(popularity + 1)`; tune the weights against the 20 queries).
5. Write `test_search.py` that runs every query in the CSV and asserts the expected product is in the top 3.
6. Measure the index size added to `nomi.sqlite` and report it in the PR. Keep it within the 20 MB compressed budget from NOMI-056.
7. Measure query time on a phone: hand the SQL and a build to the NOMI-063 owner, or install the dev build yourself, run all 20 queries on a mid-range phone, and record the slowest time.

### Done when
- [ ] `product_search` exists in `nomi.sqlite` after `uv run pipeline build`
- [ ] 20 test queries in `search_queries.csv`, each with the expected product in the top 3 (test passes)
- [ ] Every query runs in under 50 ms on a phone, with timings in the PR
- [ ] Index size reported in the PR

### How to check your work
Run `uv run pytest pipeline/tests/build/test_search.py`. Then try it in the shell: `sqlite3 data/build/nomi.sqlite "select rowid from product_search where product_search match 'zzzq*' order by bm25(product_search) limit 3"` and confirm ZzzQuil is first.

### Out of scope
- The search screen and manual barcode entry in the app (NOMI-063)
- Typo tolerance beyond prefix matching (post-demo)
- Size tuning on low-end phones (NOMI-067)

### Resources
- SQLite FTS5: https://www.sqlite.org/fts5.html
- expo-sqlite: https://docs.expo.dev/versions/latest/sdk/sqlite/

---

## NOMI-059: Build `pipeline release` with a score diff report and publish dataset v0.9
**Team:** platform | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-043, NOMI-056 (same sprint)

### Summary
Add `uv run pipeline release`, which runs the full pipeline, checks invariant tests and coverage thresholds, compares the new dataset to the previous one on a fixed set of profiles, and writes a diff report. Use it to publish dataset v0.9 with its report on a release PR.

### Why this matters
Before any dataset reaches a phone, a person should see what changed. A product whose score jumped or changed tier might be a real fix or a bug in the knowledge base, and only a review can tell. This is also the process the final v1.0 demo release (NOMI-065) will follow.

### What you will deliver
- `pipeline/src/nomi_pipeline/build/release.py` and the `uv run pipeline release --version 0.9` command
- `data/build/release-0.9/diff_report.md` (and a matching `diff_report.json`)
- Dataset v0.9 (`nomi.sqlite` and manifest) published to R2 under `releases/0.9/`
- A release PR with the diff report posted as a comment or in the description

### Before you start
- `uv run pipeline run` (NOMI-043) chains every stage and writes a run manifest. Release builds on it.
- **Invariant tests**: the safety rules in `pipeline/tests/score/` (NOMI-051), for example NSAIDs never green for 65+ with high blood pressure.
- **Coverage thresholds**: minimum shares the pipeline must reach, for example identity coverage on ground-truth barcodes (at least 95%, NOMI-037) and mandated-warning recall (at least 98%, NOMI-045). Collect the current thresholds from those tickets into one config file.
- **Golden profiles**: a fixed set of profiles used for every diff, for example adult 18-64, 65+ with high blood pressure, child 6-11, pregnant. Use the profiles in `packages/schema/golden/vectors.json`.
- **Tier**: the color band a score falls in (defined in `docs/rubric/v0.md`).
- **Hard stop**: a rule that makes a product red no matter what.
- If there is no previous release to compare against, compare against the latest nightly build from NOMI-056. If NOMI-056 hasn't merged, run a first release with an empty baseline and confirm everything shows as "added."

### Steps
1. Create `pipeline/release.toml` with thresholds: `identity_coverage_min = 0.95`, `mandated_warning_recall_min = 0.98`, `score_move_flag = 10` (points; agree the number with a cofounder), and the list of golden profiles.
2. In `release.py`, run `uv run pipeline run`, then `uv run pytest pipeline/tests/score`. Stop with a clear error if any invariant fails or a threshold isn't met.
3. Download the previous release (or latest nightly) `nomi.sqlite` from R2 as the baseline.
4. For each golden profile, score every product in both datasets using the Python scoring code.
5. Compute the diff: products added, products removed, score moves of at least `score_move_flag` points, tier changes, new hard stops, removed hard stops.
6. Write `diff_report.md` with a summary table (counts per change type per profile) followed by one section per change type listing products (name, NDC11, old, new, profile). Write the same data to `diff_report.json`.
7. Run `uv run pipeline release --version 0.9`. Upload the dataset, manifest and report to R2 under `releases/0.9/`.
8. Open a release PR that updates the dataset version reference, paste the summary table into the description and attach the full report. Ask a Data Analysis member to look at every tier change and new hard stop and comment on each.

### Done when
- [ ] `uv run pipeline release` stops with a clear message if an invariant or threshold fails (shown by a test)
- [ ] Diff report covers added, removed, score moves, tier changes and new hard stops for every golden profile
- [ ] Dataset v0.9 published to R2 under `releases/0.9/` with its manifest and diff report
- [ ] Release PR open with the report, and every tier change and new hard stop commented on by Data Analysis

### How to check your work
Run the release twice with no changes in between: the second diff report should list zero changes. Then change one severity in a knowledge base YAML on a local branch, rerun, and confirm the affected products show up as score moves.

### Out of scope
- The single-command pipeline run itself (NOMI-043)
- Adding scores to the dataset (NOMI-056)
- The final v1.0 demo release and cofounder sign-off (NOMI-065)

### Resources
- Pipeline CLI and run manifest: NOMI-043 in `pipeline/src/nomi_pipeline/`
- Cloudflare R2: https://developers.cloudflare.com/r2/
- uv docs: https://docs.astral.sh/uv/

---

## NOMI-060: Build the on-device scoring engine
**Team:** visualization | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-040, NOMI-051 (same sprint)

### Summary
Write the TypeScript code in `apps/mobile/src/scoring/` that computes a product's personalized score on the phone by looking up term-table points for the active profile, adding them up, applying hard stops, and computing the benchmark percentile.

### Why this matters
Personalized scoring happens on the phone so the user's age, conditions and medications never leave it (ADR-0002). This engine is what turns a scan into a score. It must match the Python scoring exactly, or users would see numbers nobody checked, so it contains no modeling logic: it only looks up and adds values the pipeline exported.

### What you will deliver
- `apps/mobile/src/scoring/engine.ts` with `scoreProduct(data, product, profile): ScoreResult`
- `apps/mobile/src/scoring/benchmark.ts` with `percentileFor(score, breakpoints): number`
- `apps/mobile/src/scoring/sqliteSource.ts` that reads term tables, hard stops and breakpoints from the bundled `nomi.sqlite`
- Unit tests in `apps/mobile/src/scoring/__tests__/` that pass every golden vector

### Before you start
- **Term tables**: rows that say "this ingredient, this dimension, this persona (and optional condition or medication) costs N points." Exported by NOMI-051, shipped in `nomi.sqlite` by NOMI-056.
- **Hard stop**: a rule that makes a product red no matter what, such as the label saying "do not use" for this persona.
- **Profile**: the active user's persona plus optional conditions and medication types, read from encrypted storage (NOMI-039).
- **Benchmark percentile**: where the score falls among products with the same use. The pipeline exports the score at percentiles 0, 5, ..., 100 per use and persona (NOMI-054); you interpolate between the two nearest values.
- **Golden vectors**: (product, profile, expected score) cases in `packages/schema/golden/vectors.json`. NOMI-057 runs your engine against them in CI.
- Database access goes through the layer from NOMI-040.
- If NOMI-051 / NOMI-056 haven't merged, agree the data shape with their owners on day one, then build against a small fixture in `apps/mobile/src/scoring/__fixtures__/term_tables.json` made from the reference products in `packages/schema/examples/`.
- Rule: no health data in logs, analytics or crash reports. Don't log profiles.

### Steps
1. Agree the input types with the NOMI-051 and NOMI-056 owners and use the generated types from `packages/schema/generated/`.
2. Write `engine.ts` as a pure function: input is plain data (term rows, hard-stop rules, product ingredients, profile), output is `{ score, tier, contributions: [{ dimension, points, ingredientId, citationIds }], hardStops: [...] }`. No database calls inside, so it can be tested on Node.
3. Implement the steps in this order: select term rows matching the product's ingredients and the profile's persona; add rows for each of the profile's conditions and medication types; sum points per dimension; compute the total as the rubric defines (for example 100 minus total points, clamped to 0-100; confirm in `docs/rubric/v0.md`); apply hard stops; map to a tier.
4. Write `benchmark.ts`: given a score and 21 breakpoints, return the percentile by linear interpolation. Handle scores below the lowest and above the highest breakpoint.
5. Write `sqliteSource.ts` that loads the rows for one product and one persona with indexed queries, and caches term rows by ingredient for the session.
6. Write the golden test: load `packages/schema/golden/vectors.json` and the term-table fixture, run every vector, and assert `score`, `tier` and `hardStops` equal the expected values. Coordinate output format with the NOMI-057 owner so CI can reuse it.
7. Write a timing test on a phone: in the dev build, score each reference product for three profiles 100 times and log the median and slowest time to the dev console (no profile data in the log).
8. Wire the engine into the result screen so a scan shows a real computed score instead of the fixture score.

### Done when
- [ ] Every golden vector in `packages/schema/golden/` passes in the TypeScript tests
- [ ] The NOMI-057 CI job is green with your engine
- [ ] Scoring one product takes under 20 ms on a mid-range phone (median and slowest times in the PR)
- [ ] `percentileFor` tests cover below-min, above-max and exact-breakpoint scores
- [ ] Scanning a reference product in the dev build shows the computed score
- [ ] No profile data appears in any log or network request

### How to check your work
Run the app's TypeScript test command and confirm every golden vector passes. In the dev build, scan a Benadryl box with a 30-year-old profile, then switch to a 75-year-old profile: the 75-year-old score must be lower. Compare both numbers to the matching golden vectors.

### Out of scope
- Computing or exporting term tables (NOMI-051) and shipping them (NOMI-056)
- The profile switcher and benchmark display (NOMI-061)
- Ranking alternatives on screen (NOMI-062)
- Performance work across the whole scan flow (NOMI-069)

### Resources
- Rubric: `docs/rubric/v0.md`
- Privacy rules: `docs/adr/0002-privacy.md`
- expo-sqlite: https://docs.expo.dev/versions/latest/sdk/sqlite/

---

## NOMI-061: Add the benchmark and profile switcher to the result screen
**Team:** visualization | **Priority:** P0 | **Sprint:** S4 | **Depends on:** NOMI-041, NOMI-060 (same sprint)

### Summary
Add three things to the result screen: a "Better than X% of [use] for you" line with a small distribution visual, a profile switcher (me, my child, my parent) that rescores instantly, and a badge showing whether the score is preliminary or verified.

### Why this matters
This is the demo's personalization moment: the same Benadryl box gets a different score for a 30-year-old and a 75-year-old, live on stage. The benchmark gives the score meaning, and the review-status badge is honest about which scores a person has checked.

### What you will deliver
- `apps/mobile/src/components/BenchmarkStrip.tsx`: the sentence plus a small distribution visual
- `apps/mobile/src/components/ProfileSwitcher.tsx`: chips for each saved profile
- `apps/mobile/src/components/ReviewStatusBadge.tsx`
- The three components wired into the result screen in `apps/mobile/src/app/result/`

### Before you start
- **Benchmark**: a product's rank among products with the same use for this persona. The percentile comes from `percentileFor` in `apps/mobile/src/scoring/benchmark.ts` (NOMI-060), using breakpoints from NOMI-054.
- **Use**: what the product is for (pain, sleep, nasal allergy...). Show the use in plain words, for example "pain relievers" or "sleep aids".
- **Profile**: who the scan is for, stored encrypted on the phone (NOMI-039). Users can have several (me, my child, my parent).
- **Preliminary vs verified**: verified means every ingredient's ratings were curated and reviewed by a person; preliminary means some were derived automatically (see NOMI-075). The flag comes from the dataset; if it isn't there yet, treat reference products as verified and everything else as preliminary.
- Use components and tokens from `apps/mobile/src/components/` (NOMI-027) and the visuals chosen in NOMI-014. Follow the Figma prototype from NOMI-013.
- If NOMI-060 hasn't merged, call a stub `scoreProduct` that returns the expected scores from `packages/schema/golden/vectors.json`.
- The score must never rely on color alone (about 1 in 12 men is color-blind).

### Steps
1. Build `BenchmarkStrip`: the text "Better than {X}% of {use} for you" where X is a whole number, and a small horizontal strip showing the distribution (for example the 21 breakpoints as ticks) with a marker at the user's score. Add a screen-reader label with the same sentence.
2. Hide the benchmark when there is no breakpoint row for this use and persona, and show nothing in its place (no "0%").
3. Build `ProfileSwitcher`: one chip per saved profile with its name and age band; the active one is selected. Tapping a chip sets the active profile and calls `scoreProduct` again. No loading spinner: the score, breakdown and benchmark update in the same render.
4. Add a "+ Add" chip at the end that opens profile creation from NOMI-028/NOMI-039.
5. Build `ReviewStatusBadge` with two states, "Verified" and "Preliminary", each with an icon and text (not color only). Tapping "Preliminary" shows one sentence explaining what it means.
6. Place the three components on the result screen as in the Figma prototype: switcher near the score, benchmark under the score, badge next to the tier label.
7. Create two demo profiles on a test phone, a 30-year-old and a 75-year-old, and scan a Benadryl box. Switch between them and confirm the score, breakdown and benchmark all change.
8. Record a short screen video of the Benadryl switch and attach it to the PR.

### Done when
- [ ] The benchmark sentence and visual show for every reference product that has breakpoints
- [ ] Switching profile updates score, breakdown and benchmark without a loading state
- [ ] The review-status badge shows text and an icon for both states
- [ ] Screen readers read the benchmark sentence and the badge state
- [ ] The Benadryl 30 vs 75 flow works end to end on a real phone, with a video in the PR

### How to check your work
On a real phone, scan Benadryl with the 30-year-old profile, note the score and benchmark, then tap the 75-year-old chip. The score must drop and the memory/thinking dimension should grow in the breakdown. Turn on VoiceOver or TalkBack and confirm the benchmark sentence and badge are read aloud.

### Out of scope
- The scoring engine and percentile math (NOMI-060)
- Computing breakpoints (NOMI-054)
- The comparison screen (NOMI-062)
- Full accessibility pass across all screens (NOMI-070)

### Resources
- Figma prototype and library: NOMI-013, NOMI-012, NOMI-014
- Demo script: `docs/demo/script.md`
- Expo docs: https://docs.expo.dev/

---

## NOMI-062: Build the alternative and tradeoff comparison screen
**Team:** visualization | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-055 (same sprint), NOMI-060 (same sprint)

### Summary
Build a screen, opened from the result screen, that ranks alternative products for the active profile and compares the scanned product with the chosen alternative side by side: scores, risk-dimension tradeoffs, shared use and a one-line reason, with an "Ask your pharmacist" state when there is no better option.

### Why this matters
The comparison explains why Tylenol may be the better choice than Aleve for one person and not for another. It shows the tradeoff across risk dimensions, not just two numbers. This is the Tylenol vs Aleve demo moment for a 70-year-old with high blood pressure.

### What you will deliver
- `apps/mobile/src/app/compare/` screen
- `apps/mobile/src/scoring/rankAlternatives.ts` that re-scores and sorts candidates for the active profile
- A "See safer options" entry point on the result screen
- An "Ask your pharmacist" state

### Before you start
- **Alternative candidates**: for each product, the pipeline exports a list of products that share a use, with tradeoff data per persona (NOMI-055), shipped in the `alternative` table of `nomi.sqlite` (NOMI-056).
- **Tradeoff**: the risk dimensions where two products differ. Example for a 70-year-old with high blood pressure: Aleve is worse on GI bleeding, blood pressure and kidney; Tylenol is worse on liver at high doses.
- **Risk dimension**, **profile**, **use**: see the glossary in `docs/nomi-101.md`.
- The phone ranks candidates because only the phone knows the user's conditions. Use `scoreProduct` from NOMI-060 to score each candidate for the active profile.
- If NOMI-055 or NOMI-056 haven't merged, create a fixture `apps/mobile/src/app/compare/__fixtures__/alternatives.json` with Aleve -> Tylenol Extra Strength and ZzzQuil -> store-brand diphenhydramine from the reference products in `packages/schema/examples/`. If NOMI-060 hasn't merged, use the expected scores from the golden vectors.
- Follow the comparison wireframe from NOMI-013 and use components from NOMI-027.

### Steps
1. Write `rankAlternatives(data, product, profile)`: load candidates for the product and the profile's persona, score each with `scoreProduct`, drop any with a hard stop, keep only candidates that score higher than the scanned product, and sort by score (ties: single-ingredient first).
2. Add a "See safer options" button on the result screen. Show it only when at least one candidate exists after ranking; otherwise show the "Ask your pharmacist" line on the result screen instead.
3. Build the compare screen top section: the two products side by side, each with name, score, tier word and the shared use ("Both used for: pain").
4. Build the tradeoff section: one row per dimension where the two differ, with a bar or marker for each product and a text label ("Lower risk" / "Higher risk") so it reads without color. Order rows by size of the difference.
5. Add a one-line reason at the top, filled from the templates (NOMI-048) where available, for example "Lower risk of stomach bleeding and blood pressure effects for you." If templates aren't in the dataset yet, build the sentence from the top two dimension names.
6. Add a horizontal list of other ranked alternatives under the comparison; tapping one swaps it into the right-hand column.
7. Build the "Ask your pharmacist" state: shown when no candidate scores higher for this profile. One sentence explaining there is no clearly safer OTC option for this person and a pharmacist can help.
8. Test with a non-expert tester (someone outside the team): set up a 70-year-old profile with high blood pressure, scan Aleve, open the comparison with Tylenol, and ask "Which would you pick for this person and why?" Write their answer in the PR.

### Done when
- [ ] Alternatives are ranked by the active profile's score, and switching profiles re-ranks them
- [ ] Side-by-side view shows both scores, the shared use, dimension tradeoffs and a one-line reason
- [ ] Tradeoffs are readable without color (text labels present)
- [ ] "Ask your pharmacist" state appears when no candidate scores higher
- [ ] A non-expert tester correctly explains the Tylenol vs Aleve tradeoff for a 70-year-old with high blood pressure, with their answer in the PR

### How to check your work
Scan Aleve with a 70-year-old high-blood-pressure profile and open the comparison: Tylenol should rank above Aleve, with GI bleeding, blood pressure and kidney marked lower risk for Tylenol. Then scan ZzzQuil and confirm no allergy product such as Claritin appears. Switch to a profile with liver disease and check the ranking changes.

### Out of scope
- Choosing candidates and computing tradeoffs in the pipeline (NOMI-055)
- The scoring engine (NOMI-060)
- Explanation template wording (NOMI-048)
- Medicine Cabinet and interaction checks (post-demo, `planning/post-demo.md`)

### Resources
- Demo script: `docs/demo/script.md`
- Dimensions: `docs/scoring/dimensions.md`
- Expo Router: https://docs.expo.dev/router/introduction/

---

## NOMI-063: Add manual barcode entry, name search and recent scans
**Team:** visualization | **Priority:** P1 | **Sprint:** S4 | **Depends on:** NOMI-058 (same sprint), NOMI-030

### Summary
Give users a way to find a product when the camera can't read the barcode: type the barcode digits, search by name using the offline search index, or pick from recent scans stored only on the phone.

### Why this matters
Some boxes won't scan: crumpled packaging, glare, curved bottles, or barcodes we can't resolve. Without a fallback the user hits a dead end. In the demo, if a box from the audience fails to scan, we need to find it by name in a few seconds.

### What you will deliver
- `apps/mobile/src/app/search/` screen with a search field and results list
- A manual barcode entry sheet reachable from the scanner
- A "Recent" list of the last 20 scans, stored encrypted on the device
- A "Can't scan? Search instead" button on the scanner screen

### Before you start
- **NDC candidates**: a typed barcode goes through the same parser as a scanned one, `ndcCandidates` in `apps/mobile/src/lib/barcode.ts` (NOMI-007), then the same lookup as a scan (NOMI-040).
- **FTS index**: the `product_search` full-text table in `nomi.sqlite` (NOMI-058). Use the exact query SQL from `pipeline/src/nomi_pipeline/build/search.py` so ranking matches the pipeline tests.
- **Scan flow states**: scored, preliminary, homeopathic, not found, invalid barcode (NOMI-030). Typed barcodes must reach the same states.
- **Privacy rule**: scan history is health-related and stays on the device, encrypted (ADR-0002). Store recent scans with the encrypted storage from NOMI-039. Never send search text or recent scans anywhere.
- If NOMI-058 hasn't merged, use a SQL `LIKE '%text%'` query on product names in the fixture database as a temporary stand-in, and switch to the FTS query when it lands.

### Steps
1. Add a "Can't scan? Search instead" button to the scanner screen that opens `apps/mobile/src/app/search/`.
2. Build the search screen: a text field focused on open, the "Recent" list shown when the field is empty, and results shown as you type (debounce about 150 ms).
3. Run the FTS query on each change and show up to 10 results with brand name, generic name, strength and labeler, so store brands are distinguishable.
4. Tapping a result opens the result screen for that product, the same as a scan.
5. Add a "Type barcode" option on the search screen: a numeric keypad field that accepts 12 or 13 digits, runs `ndcCandidates`, and on `invalid_check_digit` or `bad_length` shows the invalid-barcode state from NOMI-030; on success runs the normal lookup.
6. Save each successful scan, search pick or typed barcode to "Recent" (product id and timestamp only) in encrypted storage. Keep the last 20, newest first, with duplicates moved to the top.
7. Add "Clear recent" on the search screen and make sure NOMI-039's "Delete all my data" also clears recent scans.
8. Test with a tester: hand them a box and ask them to find it by name starting from the scanner. Time it and write the result in the PR.

### Done when
- [ ] Typing a valid barcode reaches the same result as scanning it; an invalid one shows the invalid-barcode state
- [ ] Name search uses the FTS index and returns results while typing
- [ ] Recent scans show the last 20, are stored encrypted, and are cleared by "Delete all my data"
- [ ] No search text or recent scans appear in any network request (checked with a network inspector)
- [ ] A tester finds a product by name in under 10 seconds from the scanner, with the time in the PR

### How to check your work
In airplane mode, type `tylen` and confirm Tylenol products appear. Type a barcode from a box at home and compare with scanning the same box. Scan three products, reopen search, and check they appear in "Recent" in the right order. Use "Delete all my data" and confirm the list is empty.

### Out of scope
- Building the FTS index and its ranking (NOMI-058)
- The barcode parser (NOMI-007) and database lookup (NOMI-040)
- Encrypted storage itself (NOMI-039)

### Resources
- expo-sqlite: https://docs.expo.dev/versions/latest/sdk/sqlite/
- SQLite FTS5: https://www.sqlite.org/fts5.html
- Privacy rules: `docs/adr/0002-privacy.md`

---

# Sprint 5: Nov 13 to Nov 19 (code freeze Nov 17, demo Nov 20)

## NOMI-064: Run the Nov 18 blind test and two full demo rehearsals
**Team:** cofounders | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-050

### Summary
Run a blind test on Nov 18 with 20 real OTC boxes that nobody on the team picked, record how each one did, and run two full rehearsals of the demo script on Nov 18 and Nov 19. Also prepare the fallbacks: a recorded video of the full demo and spare phones with the build installed.

### Why this matters
The demo opens with someone in the audience handing us a box we have never seen. A blind test is the only honest way to know whether that will work, because the team has been testing against the same boxes for weeks. Rehearsals catch everything else: timing, handoffs, a phone that won't mirror to the projector. The fallbacks mean the demo still happens if something breaks on stage.

### What you will deliver
- `docs/demo/blind-test.md`: one row per box with the outcome, plus a short summary (how many of 20 passed, what failed and why)
- `docs/demo/rehearsals.md`: notes from both rehearsals (date, duration, what went wrong, what was changed)
- A recorded video of the full demo script, stored in the team shared drive (not in the repo), with its link in `docs/demo/rehearsals.md`
- GitHub issues for every failure, labeled and assigned to the right ticket owner

### Before you start
- Read `docs/demo/script.md` (version 2, from NOMI-050). It lists every step of the demo, the demo boxes and the profiles.
- **Blind test**: scanning boxes that nobody on the team chose in advance, so we can't have tuned the app for them.
- **Resolved**: the app identified the right product. The product name and active ingredients on screen match the box.
- **Scored correctly**: the app shows a score (or the correct special state, such as "homeopathic, not evaluated by FDA") and a Data Analysis member reading the reasons finds nothing wrong compared with the label. See the glossary in `docs/nomi-101.md` for "hard stop", "persona" and "profile".
- **Airplane mode**: the demo phone has no network. Every scan in the blind test must be done in airplane mode, because that is how the demo runs.
- Key dates: code freeze Nov 17, blind test Nov 18, rehearsals Nov 18 and Nov 19, demo Nov 20. After code freeze, any fix needs cofounder approval.
- Demo phones come from NOMI-068 and the frozen dataset from NOMI-065. If those aren't ready on Nov 18, use the latest internal build on any team phone and note the build and dataset version in the results.

### Steps
1. By Nov 16, ask two or three people outside the team (friends, classmates) to buy or bring 20 OTC boxes in total from different stores. Tell them only "any over-the-counter medicine, any aisle, store brands welcome". Do not let any team member choose boxes.
2. Create `docs/demo/blind-test.md` with a table: `#`, `barcode`, `product name on box`, `store`, `aisle`, `product shown in app`, `resolved (yes/no)`, `score or state shown`, `profile used`, `scored correctly (yes/no)`, `scan time feel (fast/slow)`, `notes`, `issue link`.
3. On Nov 18, put the demo phone in airplane mode and set the profile to the adult 18-64 profile from the demo script.
4. Scan each box once as it is handed to you. Fill in the row right away. If the scan fails, try once more, then use manual entry or name search (NOMI-063) and note that in `notes`.
5. Have one Data Analysis member read the score reasons for every resolved box and mark `scored correctly`. Disagreements go to `notes`.
6. Count passes. A box passes when it is both resolved and scored correctly. Write the total (for example "18 of 20") and a short list of failure causes at the top of the file.
7. File a GitHub issue for every failure: identity misses go to the NOMI-066 owner, UI problems to NOMI-072, odd scores to NOMI-073. Label each `blind-test`. Since this is after code freeze, a cofounder decides which ones get fixed before Nov 20.
8. Do not store photos of boxes, names of the people who brought them, or any health details in the repo.
9. Run rehearsal 1 on Nov 18 with the full team: the whole script, in order, on the demo phones, with the projector or screen-share setup you will use on Nov 20. Time each section.
10. Write what went wrong and what you changed in `docs/demo/rehearsals.md`.
11. Record the full demo as a screen recording plus voice-over during or after rehearsal 1. Upload it to the shared drive and add the link to `docs/demo/rehearsals.md`.
12. Confirm with the NOMI-068 owner that at least one spare phone has the release build, demo profiles and airplane mode set up.
13. Run rehearsal 2 on Nov 19 with the fixes in place. Practice switching to the video and to the spare phone at least once each.
14. Update `docs/demo/rehearsals.md` and open a PR with both files.

### Done when
- [ ] 20 boxes scanned on Nov 18, all rows filled in `docs/demo/blind-test.md`
- [ ] At least 18 of 20 boxes resolved and scored correctly
- [ ] Every failure has a linked GitHub issue labeled `blind-test`
- [ ] Two full rehearsals done (Nov 18 and Nov 19), notes in `docs/demo/rehearsals.md`
- [ ] Recorded demo video in the shared drive, link in `docs/demo/rehearsals.md`
- [ ] At least one spare phone with the build installed, confirmed in rehearsal 2
- [ ] No personal data or box photos committed

### How to check your work
Open `docs/demo/blind-test.md` and count the rows where both `resolved` and `scored correctly` are `yes`; the number should match your summary. Open every issue link and confirm it exists. Ask someone who missed rehearsal 2 to watch the video and say whether they could follow the demo from it alone.

### Out of scope
- Fixing identity misses found in the blind test (NOMI-066)
- Fixing UI bugs (NOMI-072) and odd scores (NOMI-073)
- Setting up the demo phones (NOMI-068)
- Changing the demo script itself (done in NOMI-050; only small timing edits here)

### Resources
- Demo script: `docs/demo/script.md`
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-065: Release and tag demo dataset v1.0 and bundle it into the demo build
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-059

### Summary
Run the final release of the on-device dataset as version 1.0, get both cofounders to review its diff report, tag the dataset version together with the code commit that built it, and bundle that exact file into the demo build of the app. After Nov 17, no data changes go in without cofounder approval.

### Why this matters
The demo runs on one frozen, reviewed dataset so nothing changes underneath us in the final days. If a late knowledge-base edit slipped into the build the night before, a score we rehearsed could change on stage. A tagged release also means we can rebuild the exact same file later and explain every number in it.

### What you will deliver
- Dataset v1.0 (`nomi.sqlite` plus its manifest) published to R2
- A release PR with the v1.0 diff report posted on it and approvals from both cofounders
- A git tag `dataset-v1.0` on the commit that built the dataset
- The demo build of `apps/mobile` with v1.0 bundled at `apps/mobile/assets/nomi.sqlite`
- A short "data freeze" note posted in the team channel and in the release PR description

### Before you start
- **Dataset**: the single SQLite file that ships inside the app. It holds products, ingredients, label warnings, term tables (the scoring points), benchmarks, alternatives and explanation templates. See "Ship" in `docs/nomi-101.md`.
- **Manifest**: the file written next to the dataset with the dataset version, input data hashes and the code commit (from NOMI-038 and NOMI-043).
- **Diff report**: the comparison against the previous release (v0.9 from NOMI-059) on the golden profiles: products added or removed, score moves, tier changes and new hard stops.
- **R2**: Cloudflare's file storage where we publish datasets (glossary in `docs/nomi-101.md`).
- `uv run pipeline release` (NOMI-059) runs the full pipeline with invariant tests and coverage thresholds, and writes the diff report. Run `uv run pipeline release --help` to see how to set the version.
- Fixes from NOMI-066 (identity), NOMI-067 (size and speed), NOMI-073 (score review) and NOMI-075 (more ingredients) should merge before the final run. Ask their owners on Nov 13 for a merge date no later than Nov 16.
- If NOMI-059 hasn't merged, run the stages by hand with `uv run pipeline run` (NOMI-043) and `uv run pipeline build`, and write the diff by comparing scores from v0.9 and the new build for the golden profiles in a short DuckDB query. Tell the cofounders this release was built that way.

### Steps
1. On Nov 13, post in the team channel: the final release run is on Nov 16, and everything that should be in v1.0 must merge to `main` by then.
2. On Nov 16, pull `main` and confirm the working tree is clean (`git status`).
3. Run `uv run pipeline release` with version `1.0` (use the flag shown by `--help`, for example `--version 1.0`).
4. Confirm the run passed every invariant test and coverage threshold. If any failed, stop and fix before continuing.
5. Open a release PR titled `Dataset v1.0` and paste the diff report into it, or confirm the release command posted it.
6. Ask both cofounders to review the diff report. Every tier change and every new hard stop needs an explanation in the PR, such as "naproxen kidney rating corrected in NOMI-073".
7. After both approve, publish the dataset and manifest to R2 (the release command does this, or run the publish step from NOMI-038).
8. Tag the commit: `git tag -a dataset-v1.0 -m "Demo dataset v1.0" <commit>` and `git push origin dataset-v1.0`.
9. Confirm the manifest's code commit equals the tagged commit and its dataset version is `1.0`.
10. Download the published file from R2 into `apps/mobile/assets/nomi.sqlite` using the bundling step from NOMI-040. Check its SHA-256 (`shasum -a 256 apps/mobile/assets/nomi.sqlite`) against the hash in the manifest.
11. Build the demo release build of the app with that file bundled and give it to the NOMI-068 owner.
12. Post the data freeze rule in the team channel and in the release PR: "No changes to the dataset, `pipeline/knowledge/` or `pipeline/src/nomi_pipeline/score/` after Nov 17 without approval from a cofounder in the PR."
13. If a cofounder approves a change after Nov 17, cut `dataset-v1.0.1` the same way and record why in the release PR.

### Done when
- [ ] Release run finished with all invariants and coverage thresholds passing
- [ ] Diff report on the release PR, approved by both cofounders
- [ ] Every tier change and new hard stop in the diff has a one-line explanation
- [ ] Dataset v1.0 and manifest published to R2
- [ ] Git tag `dataset-v1.0` pushed, and the manifest's commit matches it
- [ ] The bundled `apps/mobile/assets/nomi.sqlite` hash matches the manifest
- [ ] Demo build with v1.0 handed to the NOMI-068 owner
- [ ] Data freeze rule posted in the team channel

### How to check your work
On a fresh clone, run `git checkout dataset-v1.0` and the release command again with the same inputs. The new file's hash should equal the published one (NOMI-043 makes runs reproducible). In the demo build, scan the five reference products (Tylenol Extra Strength, Aleve, ZzzQuil, NyQuil, store-brand diphenhydramine) and confirm the scores match the v1.0 diff report for the same profiles.

### Out of scope
- Building the release command and diff report (NOMI-059)
- Size and speed tuning (NOMI-067)
- Installing builds on the demo phones (NOMI-068)
- Fixing scores (NOMI-073) or identity misses (NOMI-066)

### Resources
- Cloudflare R2 docs: https://developers.cloudflare.com/r2/
- uv docs: https://docs.astral.sh/uv/
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-066: Fix identity misses found by scanning 50 new boxes
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-037

### Summary
Scan 50 OTC boxes that are not in our ground-truth barcode set, run each through the identity resolver, fix every box that resolves to the wrong product or to nothing, add each fixed case as a regression fixture, and report final coverage.

### Why this matters
The identity resolver turns a barcode into the exact product and its ingredients. We have tuned it against the same ground-truth barcodes (NOMI-020) for weeks, so its score on that set is no longer a fair guess of how it will do on a box from the audience. Fifty new boxes give us an honest number and a last chance to fix the misses before code freeze.

### What you will deliver
- `pipeline/tests/fixtures/barcodes_blind.csv` with the 50 new boxes, same columns as `pipeline/tests/fixtures/barcodes.csv`
- Resolver fixes in `pipeline/src/nomi_pipeline/identity/`
- One regression fixture per fixed miss, added to the regression fixtures created in NOMI-037
- `pipeline/reports/identity-blind-50.md`: per-box result, every miss with its cause and fix, and final coverage

### Before you start
- **Identity resolver**: the pipeline step that goes barcode -> NDC candidates -> FDA NDC directory -> DailyMed label -> ingredients and strengths (NOMI-025, NOMI-037). Its output is `data/silver/product.parquet`.
- **NDC**: FDA's product code, found inside most drug barcodes. **UPC-A**: the 12-digit retail barcode. See the glossary in `docs/nomi-101.md`.
- **Ground-truth set**: `pipeline/tests/fixtures/barcodes.csv` from NOMI-020. A new box must not have a barcode already in that file.
- Common causes of misses from the NOMI-025 and NOMI-037 reports: store-brand labelers, barcodes that don't start with `3` (so they contain no NDC), stale or missing labels, and several candidates matching. Read those reports first.
- **Correct**: the resolved product's name, active ingredients and strengths match the box.
- Code freeze is Nov 17 and the final dataset run (NOMI-065) is Nov 16. Fixes must merge by Nov 16 to reach the demo dataset.
- If the NOMI-037 regression fixtures don't exist yet, create `pipeline/tests/fixtures/identity_regressions.csv` with columns `barcode`, `expected_ndc11`, `expected_name`, `cause`, `fixed_in` and a test that reads it.

### Steps
1. On Nov 13, collect 50 boxes not in the ground-truth set. Visit at least two stores the NOMI-020 drive did not focus on, include at least 15 store brands, and cover every aisle (pain/fever, allergy, sleep, cough/cold, digestive, topical, eye/nasal, first aid). Typing the barcode from any barcode app is fine.
2. Check each barcode against `pipeline/tests/fixtures/barcodes.csv` and swap out any duplicates.
3. Write the 50 rows to `pipeline/tests/fixtures/barcodes_blind.csv` with the same columns as the ground-truth CSV. Keep any photos in the shared drive, not the repo.
4. Run the resolver over the new file and write the result next to each row: resolved NDC11, product name, ingredients.
5. Compare each result to the box by hand and mark it `correct`, `wrong product` or `not found`.
6. For every miss, find the cause and write it down: for example "labeler not in NDC directory", "no NDC in barcode, labeler and name match failed", "label superseded, using old set id".
7. Fix the cause in `pipeline/src/nomi_pipeline/identity/`. Prefer fixes that help a whole category (for example a whole store-brand labeler) over a one-off mapping.
8. Add each fixed box to the regression fixtures with the cause and your PR number.
9. Rerun the resolver on the 50 boxes and on the full ground-truth set. Confirm nothing that used to be correct is now wrong.
10. Write `pipeline/reports/identity-blind-50.md`: coverage before fixes, coverage after fixes, the list of misses with cause and fix, and any box still unresolved with the reason.
11. Tell the NOMI-065 owner when the fixes merge.

### Done when
- [ ] `barcodes_blind.csv` has 50 boxes, none in the ground-truth set, at least 15 store brands, every aisle represented
- [ ] At least 95% correct on the new boxes (48 of 50 or better)
- [ ] Every fixed miss has a regression fixture, and the regression test passes
- [ ] Ground-truth coverage did not drop
- [ ] `pipeline/reports/identity-blind-50.md` committed with before and after coverage
- [ ] Fixes merged by Nov 16

### How to check your work
Run `uv run pytest pipeline/tests/identity` and confirm all tests pass, including the new regression cases. Pick five of the boxes at random, scan them with the latest app build that bundles your fixed dataset, and confirm the product shown matches the box.

### Out of scope
- The 20-box blind test on Nov 18 (NOMI-064)
- App-side lookup and the "not found" screen (NOMI-040, NOMI-030)
- Name search fallback (NOMI-058, NOMI-063)

### Resources
- FDA NDC directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-067: Shrink the dataset and speed up on-phone lookups
**Team:** platform | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-056

### Summary
Measure how long every database query the app runs takes on a low-end Android phone, then add indexes, drop unused columns and tune compression until every lookup is under 10 ms and the dataset is within its 20 MB compressed budget. Report before and after numbers.

### Why this matters
"Instant" is the core promise of the scan, and low-end Android phones are where slowness shows first. The dataset ships inside the app, so a smaller file also means faster installs and updates. This ticket makes sure the database is never the slow part of a scan.

### What you will deliver
- Changes to the dataset builder in `pipeline/src/nomi_pipeline/build/` (indexes, schema pruning, compression settings)
- A dev-only benchmark screen in the app, for example `apps/mobile/src/app/dev/db-bench.tsx`, that times each query type
- `pipeline/reports/dataset-performance.md` with a before and after table: compressed size, uncompressed size, and median, p95 and max time per query type

### Before you start
- **Dataset**: `nomi.sqlite`, the SQLite file the app ships with (NOMI-038, NOMI-056). Glossary in `docs/nomi-101.md`.
- **Budget**: 20 MB compressed (set in NOMI-056) and under 10 ms per lookup (set in NOMI-038).
- **Query types to measure**: product by NDC11, ingredients for a product, label warnings for a product, term-table rows for a product and profile, hard-stop rules, benchmark breakpoints, alternative candidates, explanation templates, and name search (FTS5, NOMI-058). Find the exact SQL in `apps/mobile/src/lib/` and `apps/mobile/src/scoring/`.
- **Index**: a lookup structure that lets SQLite find rows without reading the whole table. `EXPLAIN QUERY PLAN <query>` shows `SCAN` when a whole table is read and `SEARCH ... USING INDEX` when an index is used.
- **p95**: the time that 95% of runs are faster than.
- Use the lowest-end Android phone the team has. Record its model, Android version and RAM in the report.
- Changes must merge by Nov 16 so they reach the v1.0 dataset (NOMI-065). If NOMI-056 hasn't merged, profile the NOMI-038 v1 dataset and apply the same steps.

### Steps
1. Build the current dataset with `uv run pipeline build` and record its uncompressed size and compressed size (use the same compression the build uses for R2).
2. Add the dev-only benchmark screen. For each query type, run it on 50 sample NDC11s from the reference products and ground-truth barcodes, 1 warm-up call then 20 timed calls each, using `performance.now()`. Show median, p95 and max. Only show this screen in development builds.
3. Run the benchmark on the low-end Android phone in airplane mode and record the "before" numbers in `pipeline/reports/dataset-performance.md`.
4. Open the dataset with `sqlite3 data/build/nomi.sqlite` and run `EXPLAIN QUERY PLAN` on every query. List every query that shows `SCAN`.
5. Add indexes in the builder for each of those queries, for example on `ndc11` and on `(ingredient_id, dimension, persona)` in the term tables.
6. Run `ANALYZE` at the end of the build so SQLite has statistics to plan queries.
7. List columns that no app query reads and remove them from the build. Check with the Visualization team before dropping anything.
8. Reduce size: store repeated strings (citations, templates, category names) once in lookup tables and reference them by integer id; run `VACUUM` at the end of the build; try a different `PRAGMA page_size` and compression level and keep whichever is smaller without slowing queries.
9. Rebuild, rerun schema validation and the golden-vector parity check (NOMI-057), and confirm both still pass.
10. Rerun the benchmark on the same phone and record the "after" numbers.
11. Repeat steps 4 to 10 until every query type meets the target.

### Done when
- [ ] Every query type's max time (after the warm-up call) is under 10 ms on the low-end Android phone
- [ ] Compressed dataset size is 20 MB or less, recorded in the manifest
- [ ] `EXPLAIN QUERY PLAN` shows no full-table `SCAN` for any app query
- [ ] Schema validation and the NOMI-057 golden-vector check pass on the new build
- [ ] `pipeline/reports/dataset-performance.md` has before and after numbers and the phone details
- [ ] Merged by Nov 16

### How to check your work
Open the benchmark screen on the low-end phone and confirm the numbers match your report. Scan the five reference products and confirm the results look the same as before your changes. Compare the build's file size with the size in the manifest.

### Out of scope
- App rendering and navigation speed (NOMI-069)
- Changing what data the dataset contains (NOMI-056)
- Releasing the dataset (NOMI-065)

### Resources
- SQLite query planner: https://www.sqlite.org/eqp.html
- SQLite ANALYZE: https://www.sqlite.org/lang_analyze.html
- SQLite FTS5: https://www.sqlite.org/fts5.html
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-068: Prepare four demo phones that run the full script offline
**Team:** platform | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-065

### Summary
Install the release build with dataset v1.0 on 2 iPhones and 2 Android phones, set up the demo profiles, verify the full demo script in airplane mode on each phone, and write a demo-day checklist.

### Why this matters
Demo day should not depend on anyone's personal phone settings or a venue's Wi-Fi. A notification popping up, a dim screen or an old build can ruin the key moment. Four prepared phones mean we have a main phone and spares on both platforms.

### What you will deliver
- 2 iPhones and 2 Android phones with the release build and dataset v1.0 installed
- Demo profiles set up on each phone, matching `docs/demo/script.md`
- `docs/demo/devices.md`: phone model, OS version, build number, dataset version, and a pass/fail table for every script step on every phone (no owner names or personal details)
- `docs/demo/day-checklist.md`: the steps to run on each phone on the morning of Nov 20

### Before you start
- **Release build**: a standalone build of the app (not the dev build), so it runs without a laptop or Metro server. Built with EAS from NOMI-011's setup.
- **Dataset v1.0**: the frozen dataset bundled in the build (NOMI-065).
- **Profile**: who the scan is for, such as "75-year-old" or "70-year-old with high blood pressure". Profiles are stored only on the phone (ADR-0002). Demo profiles are made-up, not anyone's real health data.
- **Airplane mode**: all radios off. The demo runs this way to show nothing needs a network.
- iPhone installs outside the App Store need the device registered with the Apple developer account (owner decided in NOMI-021). Register devices early with `eas device:create`.
- If NOMI-065 hasn't merged, install the latest internal build with dataset v0.9 to practice, then reinstall the v1.0 build as soon as it's ready.

### Steps
1. Pick the 4 phones. Prefer phones the team can keep for the whole week. If phones are borrowed, agree with the owners that they stay set up until after Nov 20.
2. Register the 2 iPhones with `eas device:create` and confirm they show up in the Apple developer account.
3. Build the release builds, for example `eas build --profile preview --platform ios` and `eas build --profile preview --platform android` (use the profile names in `apps/mobile/eas.json`).
4. Install on all 4 phones.
5. Open the app on each phone and confirm the dataset version shown in the app's about or debug screen, or check with the NOMI-065 owner how to read it, is `1.0`.
6. Create the demo profiles from `docs/demo/script.md`, for example adult 30, adult 75, and 70 with high blood pressure. Use the same names on every phone.
7. Turn on airplane mode and run the full script on each phone with the demo boxes: blind scan, Benadryl for 30 vs 75, Tylenol vs Aleve for 70 with high blood pressure, NyQuil duplicate acetaminophen, homeopathic and not-found states. Mark each step pass or fail in `docs/demo/devices.md`.
8. File an issue for any failure and tell the owner of the matching ticket (NOMI-069 speed, NOMI-072 UI).
9. Test screen mirroring or the camera-to-projector setup you will use on Nov 20 with at least one iPhone and one Android phone.
10. Write `docs/demo/day-checklist.md` with at least: charge to 100% and bring power banks; brightness to max and auto-brightness off; Do Not Disturb or Focus on and notifications off; auto-lock off; automatic app and OS updates off; airplane mode on; clear recent scans; switch to the starting profile; close all other apps; confirm build and dataset version.
11. Label each phone (for example "iOS-1 main", "Android-1 spare").
12. Run the checklist once end to end before the Nov 19 rehearsal, and fix anything it misses.

### Done when
- [ ] Release build with dataset v1.0 installed on 2 iPhones and 2 Android phones
- [ ] Demo profiles set up identically on all 4 phones
- [ ] The full script runs offline on all four phones, recorded as all pass in `docs/demo/devices.md`
- [ ] Screen mirroring tested on one iPhone and one Android phone
- [ ] `docs/demo/day-checklist.md` committed and used before the Nov 19 rehearsal

### How to check your work
Hand a phone to someone who hasn't touched it, ask them to follow `docs/demo/day-checklist.md`, then run the script. If they had to ask you anything, add it to the checklist.

### Out of scope
- Building and freezing the dataset (NOMI-065)
- Fixing speed problems (NOMI-069) and UI bugs (NOMI-072)
- Running the blind test and rehearsals (NOMI-064)

### Resources
- EAS Build: https://docs.expo.dev/build/introduction/
- Internal distribution: https://docs.expo.dev/build/internal-distribution/
- Demo script: `docs/demo/script.md`

---

## NOMI-069: Measure and cut scan-to-result time below 300 ms on every demo phone
**Team:** visualization | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-060

### Summary
Add timing marks to the app, measure cold start, barcode detection and scan-to-result time on every demo phone in airplane mode, and fix the slowest steps until scan-to-result is under 300 ms on all of them.

### Why this matters
"Scan in the aisle, answer instantly" is the product promise. If the result takes a second to appear on stage, the demo feels broken even when the data is right. We measure each step so we fix the real bottleneck instead of guessing.

### What you will deliver
- Timing instrumentation in `apps/mobile/src/` that logs each step to the console, turned on only when `EXPO_PUBLIC_PERF_LOG=1`
- Performance fixes in the app (for example preloading the database, caching, fewer re-renders)
- `docs/demo/performance.md`: a before and after table per phone for cold start, barcode detection and scan to result (median and max over 20 scans)

### Before you start
- **Scan to result**: from the moment the camera's code scanner reports a barcode (the `onCodeScanned` callback in `react-native-vision-camera`) to the first frame of the result screen showing the score.
- **Barcode detection**: from the barcode being in frame to `onCodeScanned` firing. Measure it with a slow-motion video of the screen and the box, or estimate it from repeated scans.
- **Cold start**: from tapping the app icon to the camera being ready to scan.
- **Steps inside scan to result**: barcode parse (`apps/mobile/src/lib/barcode.ts`), database lookup (NOMI-040), scoring (`apps/mobile/src/scoring/`, NOMI-060), navigation and render.
- Always measure on release builds in airplane mode. Dev builds are much slower and don't reflect the demo.
- Demo phones come from NOMI-068. If they aren't ready, measure on 2 team iPhones and 2 Android phones, including the slowest Android phone the team has.
- Timing logs must never include profile data and must never be sent over the network (ADR-0002).

### Steps
1. Add a small helper, for example `apps/mobile/src/lib/perf.ts`, with `mark(name)` and `report()` that use `performance.now()` and print to the console only when `EXPO_PUBLIC_PERF_LOG=1`.
2. Add marks at: app start, camera ready, `onCodeScanned`, barcode parsed, lookup done, scoring done, result screen first layout (use `onLayout` on the score element).
3. Build a release build with `EXPO_PUBLIC_PERF_LOG=1` and install it on each phone.
4. On each phone, in airplane mode, do 3 cold starts and 20 scans across the five reference products. Read the logs with `npx react-native log-ios` / `adb logcat` or Xcode and Android Studio consoles.
5. Record the "before" table in `docs/demo/performance.md`, with each step's share of scan to result.
6. Fix the slowest step first. Common fixes: open the database and prepare statements at app start, not on the first scan; load term tables and hard stops for the active profile once and cache them; keep the result screen mounted or prefetch it; avoid re-rendering the camera view when state changes; move non-critical work (saving recent scans, logging) until after the result is shown.
7. Use the React DevTools Profiler on a dev build to find components that re-render during a scan, and memoize them.
8. Rebuild and measure again after each fix. Keep notes on what each fix saved.
9. Repeat until every scan on every phone is under 300 ms.
10. Record the "after" table and a short list of the fixes in `docs/demo/performance.md`.
11. Confirm the golden-vector check (NOMI-057) still passes, so caching didn't change any score.

### Done when
- [ ] Scan to result under 300 ms on every one of the 20 measured scans on every demo phone, in airplane mode
- [ ] Cold start and barcode detection measured and recorded for every phone
- [ ] `docs/demo/performance.md` has before and after tables and the list of fixes
- [ ] Timing logs are off unless `EXPO_PUBLIC_PERF_LOG=1` and contain no profile data
- [ ] NOMI-057 golden-vector check still passes
- [ ] Merged before code freeze on Nov 17

### How to check your work
Install the release build with logging on, scan Tylenol, Aleve and ZzzQuil five times each on the slowest phone, and confirm every logged scan-to-result time is under 300 ms. Then watch someone scan without logging and confirm it feels instant.

### Out of scope
- Database indexes and dataset size (NOMI-067)
- New features or screens (feature freeze was Nov 12, NOMI-050)
- Installing builds on demo phones (NOMI-068)

### Resources
- VisionCamera code scanning: https://react-native-vision-camera.com/docs/guides/code-scanning
- React Native performance: https://reactnative.dev/docs/performance
- Expo environment variables: https://docs.expo.dev/guides/environment-variables/

---

## NOMI-070: Make every demo screen work with screen readers and large text
**Team:** visualization | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-061

### Summary
Go through every screen in the demo flow with VoiceOver (iPhone) and TalkBack (Android) and at the largest text sizes, fix missing labels, clipped text and anything shown by color alone, and recheck contrast. Record the audit and fixes in a checklist.

### Why this matters
Our first users include older adults and their caregivers. Many use large text, and some use screen readers. If the score or a warning can't be read at large sizes or isn't announced by a screen reader, the app fails the people it's built for. Scores are also shown in colors, and about 1 in 12 men is color-blind, so color can never be the only signal.

### What you will deliver
- Accessibility fixes in `apps/mobile/src/app/` and `apps/mobile/src/components/`
- `apps/mobile/docs/accessibility-audit.md`: one row per screen and check (VoiceOver, TalkBack, largest text, color alone, contrast) with pass/fail, issue found and fix

### Before you start
- **VoiceOver / TalkBack**: the built-in screen readers on iOS and Android. They read out each element's label and role.
- **Dynamic Type / font size**: the system text size setting. On iOS: Settings > Accessibility > Display & Text Size > Larger Text. On Android: Settings > Display > Font size (and Display size).
- **WCAG AA contrast**: at least 4.5:1 for normal text, 3:1 for large text and for icons and UI parts. Use the color tokens from NOMI-012 and NOMI-027.
- Screens in the demo flow: scanner, result (score, tier word, who it's for, dimension breakdown, citations, benchmark, profile switcher, hard-stop banner, disclaimer), comparison (NOMI-062), onboarding and profiles, search and manual entry (NOMI-063), and the states preliminary, homeopathic, not found and invalid barcode.
- Components already have screen-reader labels from NOMI-027. This ticket checks they make sense in context and fixes what's missing.
- If NOMI-061 hasn't merged, audit the screens that exist and come back to the benchmark and profile switcher when they land.
- Fixes must merge before code freeze on Nov 17.

### Steps
1. Create `apps/mobile/docs/accessibility-audit.md` with a row for every screen and state listed above.
2. Turn on VoiceOver on an iPhone. Go through the full demo flow using only swipes and double taps. For each element note whether it is announced, with a sensible label and role.
3. Fix missing or unclear labels with `accessibilityLabel`, `accessibilityRole`, `accessibilityHint` and `accessibilityState`. The score should read as one phrase, for example "Score 42 out of 100, Caution, for adult 65 and over", not separate numbers.
4. Announce a successful scan with `AccessibilityInfo.announceForAccessibility`, for example "Scanned Aleve. Opening result."
5. Group related items (a dimension bar and its label) with `accessible={true}` on the container so they're read together.
6. Repeat steps 2 to 5 with TalkBack on an Android phone.
7. Set text to the largest size on both platforms (including the extra accessibility sizes on iOS). Go through every screen and note any clipped, overlapping or cut-off text.
8. Fix clipping by letting text wrap, removing fixed heights, and making screens scroll. Don't set `allowFontScaling={false}` on content text; use `maxFontSizeMultiplier` only on small fixed elements like tab labels if needed.
9. Check that nothing is shown by color alone: every score has its tier word, every dimension bar has a label and value, warnings have an icon and text.
10. Recheck contrast for every score tier, banner and chip in light and dark mode with a contrast checker or the Xcode Accessibility Inspector. Fix tokens that fail.
11. Mark every row pass in the audit file, with the fix or PR for each issue.

### Done when
- [ ] The full demo flow completed with VoiceOver on, without sighted help
- [ ] The full demo flow completed with TalkBack on
- [ ] No clipped or overlapping text at the largest text size on both platforms
- [ ] Nothing communicated by color alone on any demo screen
- [ ] Every text and score state meets WCAG AA contrast in light and dark mode
- [ ] `apps/mobile/docs/accessibility-audit.md` committed with every row passing
- [ ] Merged before code freeze on Nov 17

### How to check your work
Ask a teammate who hasn't seen your changes to turn on VoiceOver, close their eyes, scan Aleve, and tell you the score, who it's for, and one reason. Then set the largest text size and take screenshots of the result and comparison screens; nothing should be cut off.

### Out of scope
- New screens or features (feature freeze, NOMI-050)
- General UI polish and copy review (NOMI-072)
- Changing the Figma library (NOMI-012)

### Resources
- React Native accessibility: https://reactnative.dev/docs/accessibility
- WCAG 2.1: https://www.w3.org/TR/WCAG21/
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-071: Build the FAERS signal explorer page in the dashboard
**Team:** visualization | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-042, NOMI-053

### Summary
Add a page to the internal dashboard (`apps/dashboard`) where anyone can pick an ingredient, risk dimension and age band and see the FAERS signal values with their intervals, with two guided walkthroughs and the limitations stated on the page. It is used in the data-story part of the demo.

### Why this matters
The demo's data story shows the real-world evidence behind our scores. FAERS signals show which problems are reported more often than expected with an ingredient, for example memory problems with diphenhydramine in older adults. Showing them with their limits stated plainly is what makes the story credible to faculty and technical audiences.

### What you will deliver
- A signal explorer page in `apps/dashboard`, published to GitHub Pages with the rest of the dashboard
- A data export step that turns `data/gold/signal.parquet` into the JSON the page reads, run by the dashboard's existing build (NOMI-042)
- Two walkthrough presets: diphenhydramine in adults 65+, and NSAIDs and kidney
- A limitations section on the page
- A check script that confirms the page data matches the `signal` table

### Before you start
- **FAERS**: FDA's Adverse Event Reporting System, millions of reports of bad reactions. It has no denominator: we don't know how many people took a drug without problems, so it can't give risk rates.
- **Signal / IC / IC025**: a signal means a reaction is reported with an ingredient more often than expected. IC (information component) measures this with shrinkage so rare ingredients don't produce noisy results. IC025 is its lower confidence bound; IC025 above 0 counts as a signal. See the glossary in `docs/nomi-101.md`.
- **Risk dimension**: one kind of risk we rate, such as liver, GI bleeding, kidney or memory/thinking (`docs/scoring/dimensions.md`).
- **Age bands** in the signal table: 0-11, 12-17, 18-64, 65+ (NOMI-044).
- The `signal` table (NOMI-053) has ingredient, dimension, age band, sex, IC, IC025 and report count. If it also has an upper bound (IC975), show the full interval. If not, show IC with its lower bound and say so on the page.
- If NOMI-053 hasn't merged, build against `apps/dashboard/fixtures/signal-sample.json` with about 20 made-up rows in the same shape, and show a "sample data" banner until the real table is wired in.

### Steps
1. Look at how NOMI-042 turns pipeline outputs into dashboard data and add the same kind of export for `data/gold/signal.parquet`, for example with DuckDB: `COPY (SELECT * FROM 'data/gold/signal.parquet') TO 'apps/dashboard/public/data/signal.json' (FORMAT JSON, ARRAY true)`.
2. Add a page, for example `apps/dashboard/src/pages/signals`, with filters for ingredient, dimension, age band and sex.
3. Show a chart of IC per ingredient (or per dimension) with the interval as a line and IC as a point, a vertical line at 0, and the report count next to each row. Label signals (IC025 above 0) with text, not only color.
4. Add a table view below the chart with the same numbers, sortable by IC025.
5. Add walkthrough 1: diphenhydramine, memory/thinking dimension, comparing age band 65+ with 18-64. Add two or three plain sentences explaining what the viewer is seeing.
6. Add walkthrough 2: NSAIDs (ibuprofen, naproxen, aspirin) and the kidney dimension. Same format.
7. Add a "What this does and doesn't show" section: FAERS has no denominator, so this is not a risk rate; reports don't prove the drug caused the reaction; masking (one heavily reported drug hides others); notoriety bias (news and warnings increase reporting); OTC products are under-reported. Link to `pipeline/docs/signals.md` (NOMI-076) once it exists.
8. Write a check script, for example `apps/dashboard/scripts/check-signals.py`, that reads the JSON and the parquet with DuckDB and fails if any row's IC, IC025 or report count differs.
9. Publish to GitHub Pages and share the link in the team channel before the Nov 18 rehearsal.

### Done when
- [ ] Signal explorer page live on GitHub Pages
- [ ] Filters for ingredient, dimension, age band and sex work, with IC and intervals shown
- [ ] Both walkthroughs (diphenhydramine 65+, NSAIDs and kidney) available as presets
- [ ] Limitations section on the page
- [ ] Check script passes: page numbers match the `signal` table
- [ ] Used in at least one rehearsal (NOMI-064)

### How to check your work
Pick three rows at random in the page table and look them up in DuckDB (`SELECT * FROM 'data/gold/signal.parquet' WHERE ingredient = ... AND dimension = ... AND age_band = ...`). The numbers should be identical. Ask someone outside the Data Analysis team to read walkthrough 1 and explain in one sentence what it shows and what it doesn't.

### Out of scope
- Computing the signals (NOMI-053)
- The written signal validation note (NOMI-076)
- Coverage dashboard pages (NOMI-042)

### Resources
- openFDA FAERS: https://open.fda.gov/data/faers/
- DuckDB JSON export: https://duckdb.org/docs/
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-072: Triage and fix demo UI bugs so none are open at code freeze
**Team:** visualization | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-061, NOMI-062

### Summary
Own the list of UI problems found in team dry runs: triage them daily, fix every P0 by Nov 17, and do a final copy review of every demo screen. The goal is zero open P0 UI bugs at code freeze.

### Why this matters
Dry runs surface many small UI problems: a cut-off label, a wrong back button, a confusing sentence. Each is minor, but together they make the demo look unfinished. One person owning the list makes sure the important ones get fixed before code freeze and the rest are written down for later.

### What you will deliver
- A GitHub label `ui-bug` and a triaged list of every UI issue from dry runs, each marked P0 or P1
- Fixes for every P0 UI issue, merged by Nov 17
- A copy review of every demo screen, with changes merged and a cofounder's approval in the PR

### Before you start
- **Dry run**: a team member walks through `docs/demo/script.md` on a real phone and reports anything that looks wrong.
- **P0 UI bug**: anything that would break or mislead during the demo script: a crash, wrong or missing data on screen, a state that doesn't appear when it should, broken navigation, clipped key text, or copy that could be read as medical advice.
- **P1 UI bug**: cosmetic issues that don't affect the demo (spacing, minor alignment). Log them; fix only if time allows.
- **Copy**: all user-facing text on the screens.
- The legal and regulatory summary from NOMI-021 says what wording to avoid. Read it before the copy review.
- Feature freeze was Nov 12 (NOMI-050). This ticket fixes problems; it does not add features.
- Issues found in the Nov 18 blind test (NOMI-064) come after code freeze. A cofounder decides whether each one gets fixed.

### Steps
1. Create the `ui-bug` label and post in the team channel: "Report UI problems from dry runs as issues with the `ui-bug` label, a screenshot and the script step."
2. Ask each team to do at least one dry run between Nov 13 and Nov 15.
3. Triage every new `ui-bug` issue once a day: set P0 or P1 using the definitions above, assign an owner, and close duplicates.
4. Fix P0 issues first, one small PR each, linked to its issue.
5. For the copy review, list every string on the demo screens (scanner, result, breakdown, citations, benchmark, profile switcher, comparison, onboarding, search, and the preliminary, homeopathic, not-found, invalid-barcode and hard-stop states).
6. Check each string: matches the wording in `docs/demo/script.md`; reads at about an 8th-grade level; doesn't call a product "safe" or tell the user to take or stop a medicine; the "not medical advice" disclaimer is on the result screen; the homeopathic state says "Not evaluated by FDA for safety or effectiveness"; tier words and persona names are the same everywhere.
7. Make the copy changes in one PR and ask a cofounder to approve it.
8. On Nov 16, list every open `ui-bug` P0 and confirm each one has an owner and a fix in review.
9. On Nov 17, confirm zero open P0 UI issues. Move any remaining P1 issues to a post-demo milestone.

### Done when
- [ ] Every `ui-bug` issue from dry runs is triaged as P0 or P1 with an owner
- [ ] Zero open P0 UI bugs on Nov 17
- [ ] Copy review done for every demo screen and state, approved by a cofounder
- [ ] Remaining P1 issues moved to a post-demo milestone

### How to check your work
Filter GitHub issues by `label:ui-bug label:P0 is:open`; the list should be empty on Nov 17. Do one last dry run of the full script on a demo phone and confirm you find nothing new that meets the P0 definition.

### Out of scope
- Scan speed (NOMI-069)
- Screen reader and large text fixes (NOMI-070)
- Identity misses (NOMI-066) and odd scores (NOMI-073)
- New features (feature freeze, NOMI-050)

### Resources
- Demo script: `docs/demo/script.md`
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-073: Review scores for the 100 most common products and fix the causes
**Team:** data-analysis | **Priority:** P0 | **Sprint:** S5 | **Depends on:** NOMI-052

### Summary
Look at the scores of the 100 most common OTC products for 3 profiles each (300 scores), flag every result that looks wrong, and fix each one at its source in the knowledge base or rubric. Keep a review log where every flagged score is either fixed or documented before code freeze.

### Why this matters
Invariant tests catch rule violations, such as an NSAID scoring green for a 70-year-old with high blood pressure. They don't catch results that are odd but technically allowed. A person reading through the most common products catches the scores that would embarrass us in front of an audience or a pharmacist, and fixing causes rather than single scores keeps the system honest.

### What you will deliver
- `pipeline/reports/score-review-top100.csv`: one row per product and profile with the score and your verdict
- `pipeline/reports/score-review-top100.md`: how the 100 products were chosen, a summary of issues by cause, and what was fixed or documented
- Fix PRs in `pipeline/knowledge/` or `pipeline/src/nomi_pipeline/score/`, each linked from the log
- A small export script, for example `pipeline/src/nomi_pipeline/score/review_export.py`, that NOMI-074 can reuse

### Before you start
- **Score**: 0 to 100 per product and profile, built from the rubric (`docs/rubric/v0.md`). **Tier**: the word band a score falls into. **Hard stop**: a rule that makes a product red no matter what, such as the label saying "do not use" for this persona. See the glossary in `docs/nomi-101.md`.
- **Knowledge base**: our cited severity ratings per ingredient in `pipeline/knowledge/ingredients/`.
- **Profiles to use**: the three from NOMI-015: adult 18-64 with no conditions; 65+ with high blood pressure; child 6-11.
- **Never edit one product's score.** Every fix must change a rating, modifier or rubric rule, so it applies to every product with that ingredient.
- **What counts as odd**: the label says "do not use" for that persona but the product isn't a hard stop; two products with the same ingredients and strengths score very differently; a combination product scores better than one of its ingredients alone; a top risk shown doesn't match the label's warnings; the reasons shown cite the wrong source.
- Product-level scores come from NOMI-052. If it hasn't merged, review the five reference products in `packages/schema/examples/` first, then continue when it lands.
- Fixes must merge by Nov 16 to reach the v1.0 dataset (NOMI-065). After Nov 17, changes need cofounder approval.

### Steps
1. Choose the 100 products: rank products in `data/silver/product.parquet` by how many times they appear in `pipeline/tests/fixtures/barcodes.csv` (count by product, not barcode), add the demo boxes from `docs/demo/script.md`, and fill the rest with the most common national brands and store brands in the demo aisles. Write the method in the `.md` file.
2. Write the export script. For each product and profile it outputs: `product`, `ndc11`, `category`, `profile`, `score`, `tier`, `hard_stop`, `top_3_dimensions`, `points_per_dimension`. Write it to `pipeline/reports/score-review-top100.csv`.
3. Add the columns `verdict` (`ok` or `flag`), `issue`, `cause` (`knowledge base`, `rubric`, `extraction`, `identity`, `other`), `resolution` (`fixed` or `documented`) and `link`.
4. Split the 100 products among the Data Analysis team. For each row, compare the score and top dimensions with the product's Drug Facts label on DailyMed and with similar products.
5. Mark `flag` on anything that matches the "what counts as odd" list, or that a reviewer can't explain from the label and rubric.
6. For each flag, find the cause. Example: "Store-brand naproxen scores higher than Aleve for 65+ with high blood pressure" might trace to a missing condition modifier in `pipeline/knowledge/ingredients/naproxen.yaml`.
7. Fix the cause with a cited change and a PR. Rerun the export and confirm the flag is gone and nothing else moved unexpectedly.
8. If a flag can't be fixed before code freeze, write in `resolution` why, and whether it affects the demo.
9. Send each issue to the NOMI-074 owner so it becomes a permanent invariant test.
10. If a faculty partner is available (NOMI-036), send them 20 rows (at least 5 flagged and fixed, the rest random) and log their comments.
11. Write the summary in `pipeline/reports/score-review-top100.md`: number of flags, by cause, fixed vs documented.

### Done when
- [ ] 100 products x 3 profiles = 300 rows in `score-review-top100.csv`, each with a verdict
- [ ] Every flagged row has a cause and is `fixed` (with a PR link) or `documented` (with a reason), before code freeze on Nov 17
- [ ] No fix edits a single product's score directly
- [ ] Every issue handed to the NOMI-074 owner
- [ ] Faculty sample review logged, or a note that no partner was available
- [ ] Summary committed in `score-review-top100.md`

### How to check your work
Rerun the export script after all fixes and confirm no row marked `fixed` still shows the original problem. Pick five `ok` rows at random and ask a second team member to explain each score from the label and rubric alone; if they can't, reconsider the verdict.

### Out of scope
- Writing invariant tests and golden vectors (NOMI-074)
- Adding ingredients outside the demo aisles (NOMI-075)
- Changing the rubric's design (NOMI-049); only fix clear errors here

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- Rubric: `docs/rubric/v0.md`
- Risk dimensions and personas: `docs/scoring/dimensions.md`
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-074: Expand golden vectors to 100 and add an invariant for each review issue
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-051

### Summary
Grow the golden scoring test cases in `packages/schema/golden/` from 30 to 100, covering every demo aisle and persona, and add an invariant test for every issue found in the score review (NOMI-073). All must pass in both Python and TypeScript.

### Why this matters
Every issue found in review should become a permanent test, so it can't quietly come back after the demo. Golden vectors also guard the promise that the phone and the pipeline compute the same score: with only 30 cases, whole aisles and personas aren't tested at all.

### What you will deliver
- 70 new golden vectors in `packages/schema/golden/`, for 100 in total
- New invariant tests in the pipeline's scoring tests (next to the NOMI-051 invariants, for example `pipeline/tests/score/`)
- A coverage table in the PR: number of vectors per aisle and per persona

### Before you start
- **Golden vector**: a test case of (product, profile, expected score). CI runs each one through the Python scorer and the TypeScript on-phone scorer and fails on any mismatch (NOMI-057). See the glossary in `docs/nomi-101.md`.
- **Invariant**: a rule that must always hold, written as a test. Examples from NOMI-051: NSAIDs are never green for 65+ with high blood pressure or kidney disease; salicylates are a hard stop for children; more risk can never raise a score (monotonicity, tested with Hypothesis).
- **Personas**: adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding.
- **Demo aisles**: pain/fever, digestive, allergy, sleep, cough/cold.
- Follow the format and file layout of the existing 30 vectors from NOMI-051.
- Issues come from the NOMI-073 review log (`pipeline/reports/score-review-top100.md`) during the week. Check it daily.
- If a vector's expected score comes straight from the Python scorer, the test only proves both sides agree, not that the score is right. So every new vector is checked by hand against `docs/rubric/v0.md`.

### Steps
1. Read the existing 30 vectors and list how many cover each aisle and persona.
2. Plan the 70 new vectors to fill gaps: at least 15 per demo aisle across the 100, every persona at least 8 times, at least 10 combination products (NyQuil, Tylenol PM, Advil PM, Excedrin), at least 10 hard stops, and at least 10 with a condition or medication modifier (for example high blood pressure, kidney disease, blood thinners).
3. For each vector, compute the expected score by hand from the knowledge base and `docs/rubric/v0.md`, and write a short `note` field with the points breakdown, for example "naproxen: GI bleeding 65+ -15, blood pressure modifier -10, kidney -10".
4. Run the Python scorer on the same case. If it disagrees with your hand calculation, find out which is wrong. Fix the vector, or report a scorer bug to the NOMI-051 owner.
5. Ask a second Data Analysis member to check 20 of the new vectors by hand.
6. For each issue in the NOMI-073 log, write an invariant that would have caught it, for example "a product with a 'do not use under 12' warning is a hard stop for child 6-11 and child 2-5". Give each test a name and a comment linking the issue.
7. Run `uv run pytest pipeline/tests/score` and fix failures.
8. Run the NOMI-057 parity check locally (or push and let CI run it) to confirm all 100 vectors pass in TypeScript too.
9. Add the coverage table to the PR.

### Done when
- [ ] 100 golden vectors in `packages/schema/golden/`, each with a `note` showing the points breakdown
- [ ] Coverage table in the PR meets the targets in step 2
- [ ] 20 new vectors checked by hand by a second person, noted in the PR
- [ ] One invariant test per NOMI-073 issue, each linking its issue
- [ ] All vectors pass in Python and TypeScript (NOMI-057 CI job green)
- [ ] All invariants pass in `pytest`

### How to check your work
Temporarily change one severity in a knowledge base file (for example raise naproxen's kidney severity for 65+) and run the tests. Several golden vectors should fail. Revert the change. Then break one rule from the review log on purpose and confirm its new invariant fails.

### Out of scope
- Reviewing scores (NOMI-073)
- Building the parity CI job (NOMI-057)
- Changing the rubric (NOMI-049, NOMI-051)

### Resources
- Hypothesis docs: https://hypothesis.readthedocs.io/
- Rubric: `docs/rubric/v0.md`
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-075: Add about 120 preliminary ingredients beyond the demo aisles
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-034, NOMI-035

### Summary
Extend the knowledge base to about 150 ingredients by adding the next most frequent OTC ingredients (topical, eye/nasal, first aid and others), with severities derived from mandated warnings and published criteria and marked preliminary until a person verifies them. Report how much this raises coverage on the ground-truth barcodes.

### Why this matters
A box from the audience might come from an aisle we haven't curated by hand. Without ratings, the app can only say "not found". Ingredients rated automatically from FDA-required warnings and published criteria can instead show a preliminary score, clearly labeled, which is more useful and still cited.

### What you will deliver
- About 120 new YAML files in `pipeline/knowledge/ingredients/`, each marked preliminary, for about 150 ingredients in total
- A derivation script, for example `pipeline/src/nomi_pipeline/score/derive_preliminary.py`, that drafts the files from label facts, mandated warnings and criteria
- `pipeline/reports/kb-coverage.md`: share of ground-truth barcodes whose ingredients are all covered, before and after, by aisle

### Before you start
- **Knowledge base**: one YAML file per ingredient with a 0-3 severity per risk dimension and persona, every value cited (NOMI-034, NOMI-035). Glossary in `docs/nomi-101.md`.
- **Mandated warning**: warning text FDA requires on certain products. `pipeline/knowledge/mandated_warnings.yaml` (NOMI-017) maps each one to a risk dimension.
- **Criteria**: STOPP/START and ACB in `pipeline/knowledge/criteria/` (NOMI-018), mainly for the 65+ persona.
- **Label facts**: the extracted Drug Facts fields per label, including "Do not use", "Ask a doctor" and age limits, in `data/silver/label_facts.parquet` (NOMI-045).
- **Preliminary**: the app shows a "preliminary" badge (NOMI-061). Use the review-status field in the `ingredient-dimensions` schema in `packages/schema/schemas/`. If it doesn't exist, add `review_status: preliminary | verified` in a small schema PR reviewed by Platform and Data Analysis.
- Missing evidence is not the same as no risk. Don't write 0 for a dimension unless a source supports it. Ask the rubric owner (NOMI-049) how `docs/rubric/v0.md` treats unrated dimensions for preliminary ingredients, and follow that.
- Likely candidates (confirm by frequency): hydrocortisone, lidocaine, benzocaine, pramoxine, bacitracin, neomycin, polymyxin B, menthol, camphor, topical diclofenac, clotrimazole, miconazole, terbinafine, tolnaftate, benzoyl peroxide, salicylic acid, tetrahydrozoline, naphazoline, ketotifen, olopatadine, fluticasone, triamcinolone, budesonide, meclizine, dimenhydrinate, nicotine, cimetidine, lansoprazole, esomeprazole.
- Files must merge by Nov 16 to reach the v1.0 dataset (NOMI-065).

### Steps
1. Count active ingredients (by UNII, FDA's ingredient ID) across in-scope products in `data/silver/product.parquet` and across the ground-truth barcodes. Remove those already in `pipeline/knowledge/ingredients/`.
2. Take the most frequent ones until the total reaches about 150. Write the ranked list into `pipeline/reports/kb-coverage.md`.
3. Measure "before" coverage: the share of ground-truth barcodes whose active ingredients all have a knowledge base file, overall and by aisle.
4. Write the derivation script. For each ingredient: collect mandated warnings on its labels and map them to dimensions with `mandated_warnings.yaml`; turn "Do not use" items and age limits from label facts into hard-stop or high-severity values for the matching persona; add STOPP/START and ACB entries for 65+; attach a citation (source, label set id, section, URL) to every value.
5. Set the review status to preliminary in every generated file.
6. Run the script and open five generated files next to their DailyMed labels. Fix any mapping rule that produced a wrong value, then rerun.
7. Run schema validation: `uv run pytest pipeline/tests/knowledge`.
8. Spot-check 20 random values across different ingredients against their sources and record the result in the PR.
9. Measure "after" coverage and write both numbers by aisle into `pipeline/reports/kb-coverage.md`.
10. Rebuild the dataset and confirm a product from a new aisle (for example a hydrocortisone cream) shows a preliminary score in the app instead of "not found".

### Done when
- [ ] About 150 ingredients in `pipeline/knowledge/ingredients/` in total
- [ ] Every new file marked preliminary and passing schema validation
- [ ] Every non-zero value has a citation; no 0 written without a source
- [ ] 20-value spot check done and recorded in the PR
- [ ] Coverage gain on the ground-truth barcodes reported in `pipeline/reports/kb-coverage.md`, overall and by aisle
- [ ] Merged by Nov 16

### How to check your work
Pick a topical product from the ground-truth barcodes, look up its ingredient file, and check that each non-zero value matches a warning on its DailyMed label. Then scan or search for it in a dev build with the new dataset and confirm it shows a score with the preliminary badge.

### Out of scope
- Verifying preliminary ratings by hand (post-demo, with the faculty partner)
- Changing how the rubric scores (NOMI-049, NOMI-051)
- Sunscreen, hand sanitizer and other out-of-scope products (flagged in NOMI-026)

### Resources
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
- FDA OTC monographs: https://www.fda.gov/drugs/over-counter-otc-nonprescription-drugs
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-076: Write the FAERS signal validation note
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-053

### Summary
Write `pipeline/docs/signals.md`: check whether our FAERS signals find well-known risks, document false positives and limitations, and plan a proper validation after the demo.

### Why this matters
Faculty and technical audiences will ask what our FAERS signals prove. An honest write-up that shows where they work, where they don't, and what we plan to do about it protects our credibility far more than overstating them. It's also the page the signal explorer (NOMI-071) and the methodology one-pager (NOMI-077) link to.

### What you will deliver
- `pipeline/docs/signals.md` with: method summary, known-risk checks with numbers, false positives found, limitations, and a post-demo validation plan
- The DuckDB queries used, included in the document so anyone can rerun them

### Before you start
- **FAERS**: FDA's Adverse Event Reporting System. It collects reports of bad reactions but has no denominator, so it shows what gets reported, not how often a reaction happens.
- **Signal / IC / IC025**: IC (information component, from the BCPNN method) measures how much more often a reaction is reported with an ingredient than expected, shrunk toward 0 for rare ingredients. IC025 is its lower confidence bound; IC025 above 0 counts as a signal. See the glossary in `docs/nomi-101.md`.
- **MedDRA**: the medical vocabulary FAERS uses for reactions. NOMI-044 groups MedDRA terms into event groups per risk dimension.
- Input: `data/gold/signal.parquet` (NOMI-053), with ingredient, dimension, age band, sex, IC, IC025 and report count.
- **Known risks to check**: acetaminophen and liver; NSAIDs (ibuprofen, naproxen, aspirin) and GI bleeding and kidney; first-generation antihistamines (diphenhydramine, doxylamine, chlorpheniramine, brompheniramine) and memory/thinking in adults 65+.
- If NOMI-053 hasn't merged, write the structure and limitations sections first, and fill in the numbers when the table lands.

### Steps
1. Write a short method section: data years, deduplication (latest case version per case, NOMI-024), suspect drugs only (NOMI-044), event groups, the IC and IC025 formulas in words, and the signal threshold (IC025 above 0).
2. For each known risk, query the table with DuckDB, for example `SELECT ingredient, dimension, age_band, ic, ic025, report_count FROM 'data/gold/signal.parquet' WHERE ingredient = 'acetaminophen' AND dimension = 'liver'`. Put a small table of results per risk in the document, by age band.
3. For each, state plainly whether a signal was found, and if not, the likely reason (for example too few reports in an age band, or masking).
4. Look for false positives: sort all signals by IC025 and read the top 30. Note ones that are probably not real drug effects, for example a reaction that is really the reason people took the drug (confounding by indication), and explain each in one line.
5. Write the limitations section: no denominator; under-reporting, especially for OTC products; masking; notoriety bias (warnings and news increase reporting); duplicate reports that survive deduplication; missing age and sex; reports don't prove cause.
6. Write the post-demo validation plan: test the signals against a published reference set of known positive and negative drug-event pairs (candidates include the OMOP and EU-ADR reference sets; confirm which cover OTC ingredients), report sensitivity and specificity, and name an owner and a target month.
7. Add a "How we use signals" note: signals support ratings in the knowledge base but never set a score on their own.
8. Ask a cofounder to review and merge.

### Done when
- [ ] `pipeline/docs/signals.md` merged
- [ ] Results for all three known-risk checks, with numbers by age band and the queries used
- [ ] At least 5 likely false positives documented, or a note explaining why fewer were found
- [ ] Limitations section covers no denominator, under-reporting, masking and notoriety bias
- [ ] Post-demo validation plan with a reference set, metrics, owner and target month
- [ ] Reviewed by a cofounder

### How to check your work
Rerun every query in the document and confirm the numbers match the tables. Ask someone outside Data Analysis to read the document and answer: "Does a signal mean the drug causes the reaction?" They should answer no and explain why.

### Out of scope
- Computing or changing the signals (NOMI-053)
- The signal explorer page (NOMI-071)
- Running the full validation against a reference set (post-demo)

### Resources
- openFDA FAERS: https://open.fda.gov/data/faers/
- DuckDB docs: https://duckdb.org/docs/
- Glossary and big picture: `docs/nomi-101.md`

---

## NOMI-077: Write the methodology one-pager
**Team:** data-analysis | **Priority:** P1 | **Sprint:** S5 | **Depends on:** NOMI-049

### Summary
Write `docs/methodology.md`, a one-page plain-language explanation of how Nomi's scores are made: data sources, risk dimensions, how a score is built, what is validated and what isn't yet, limitations, and the roadmap to the personalized evidence-synthesis model.

### Why this matters
The demo audience and faculty partners will ask how the scores are made. A single page they can read in five minutes answers that, sets honest expectations about what is and isn't validated, and shows the plan to improve. It's linked from the demo so people can read it afterwards.

### What you will deliver
- `docs/methodology.md`, about one printed page (600-900 words), readable by someone with no medical or data background
- A link to it from `docs/demo/script.md` and from the root `README.md`

### Before you start
- Sources to summarize, not copy: `docs/nomi-101.md`, `docs/adr/0001-architecture.md` and `docs/adr/0002-privacy.md` (NOMI-003), `docs/data-sources.md` (NOMI-006), `docs/scoring/dimensions.md` (NOMI-016), `docs/rubric/v0.md` (NOMI-049), `pipeline/docs/signals.md` (NOMI-076).
- Numbers to quote, from their reports: identity coverage (NOMI-037, NOMI-066), label extraction precision and recall (NOMI-045), golden-vector parity (NOMI-057), score review results (NOMI-073), knowledge base coverage (NOMI-075).
- **Rubric v0**: the written rules that turn ingredient severities into points and a 0-100 score. **Evidence-synthesis model**: the planned later model that will set those points from combined evidence, replacing the rubric's hand-set weights without changing the app.
- Terms like FAERS, STOPP/START, ACB and persona are in the glossary in `docs/nomi-101.md`. Explain each in a few words where you use it.
- If a number isn't available yet (for example NOMI-076 hasn't merged), write the sentence with a placeholder like `[TBD: NOMI-076]` and fill it in before review.

### Steps
1. Write "What Nomi does" in two sentences: scan a box, get a 0-100 score for the person who will take it, the reasons with sources, and a safer option.
2. Write "Where the data comes from": FDA's NDC directory and DailyMed labels, FAERS adverse event reports, RxNorm, and published criteria (STOPP/START, ACB). Say all drug data is public.
3. Write "What we rate": the risk dimensions and personas, in one short list.
4. Write "How a score is built" in 4-6 steps: identify the product, read the label, rate each ingredient per dimension and persona with a citation, apply the rubric to get points, the phone adds the points for the user's profile, hard stops override. Mention that LLMs only help read labels offline, their output is checked by rules and people, and they never produce scores.
5. Write "Privacy": health details stay on the phone and scoring runs there.
6. Write "What's validated": identity coverage, extraction accuracy, parity between pipeline and app, the internal score review, and faculty review status (say plainly if no clinical review has happened yet).
7. Write "What isn't validated yet and limitations": rubric weights are expert judgment, not tested against patient outcomes; FAERS has no denominator and signals aren't yet checked against a reference set; some ingredients are preliminary; Nomi is not medical advice and doesn't replace a pharmacist.
8. Write "What's next": the evidence-synthesis model, clinical validation with faculty partners, and signal validation.
9. Cut to one page. Read it aloud; rewrite any sentence a non-expert would stumble on.
10. Add links from `docs/demo/script.md` and `README.md`.
11. Ask both cofounders to review.

### Done when
- [ ] `docs/methodology.md` merged, 600-900 words, no `[TBD]` placeholders left
- [ ] Covers data sources, risk dimensions, how a score is built, what's validated, what isn't, limitations and roadmap
- [ ] Every number quoted links to the report or doc it comes from
- [ ] Includes the "not medical advice" statement
- [ ] Reviewed by both cofounders
- [ ] Linked from `docs/demo/script.md` and `README.md`

### How to check your work
Give the page to someone outside the team. After reading it, they should be able to answer: where the data comes from, why the same box can score differently for two people, and one thing that isn't validated yet. Run a word count (`wc -w docs/methodology.md`) to confirm the length.

### Out of scope
- Changing the rubric (NOMI-049)
- The detailed FAERS validation note (NOMI-076)
- A full academic paper (post-demo, with the faculty partner)

### Resources
- Glossary and big picture: `docs/nomi-101.md`
- Rubric: `docs/rubric/v0.md`
- openFDA: https://open.fda.gov/
- DailyMed: https://dailymed.nlm.nih.gov/dailymed/
