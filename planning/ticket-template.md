# How to write a Nomi ticket

A ticket must be doable by one person in one week, and understandable by someone who has only read
`docs/nomi-101.md`. If a reader would need to ask "what exactly do I hand in?" or "what does this term
mean?", the ticket isn't finished.

## Rules

- **One clear deliverable.** The Summary says exactly what exists when the ticket is done.
- **Explain every domain term** the first time it appears in the ticket, or point to the glossary in
  `docs/nomi-101.md`. Never assume the reader knows NDC, SPL, FAERS, UNII and so on.
- **Steps are actions, top to bottom.** Each starts with a verb. Include exact file paths, commands,
  field names and example values. Someone should be able to follow them in order.
- **Say what to do if a dependency isn't ready**, usually: start from the reference products in
  `packages/schema/examples/` or a small fixture you create.
- **"Done when" is checkable.** Numbers, tests, reviewers. No "works well" or "is good".
- **Out of scope** prevents scope creep and names the ticket that covers it.
- **Plain style.** Short sentences. No em dashes, no emojis, no hype. One paragraph or bullet per
  line (don't hard-wrap), so it renders well on GitHub.
- Only link resources you're sure exist. Prefer official sites.

## Format

```
## NOMI-XXX: Verb-first title that names the deliverable
**Team:** platform | **Priority:** P0 | **Sprint:** S1 | **Depends on:** NOMI-001 (same sprint)

### Summary
One or two sentences: what you will build and who uses it.

### Why this matters
Two to four sentences in plain language: where this fits in Nomi and what breaks without it.

### What you will deliver
- Concrete artifacts with exact paths: code, data files, screens, docs.

### Before you start
- Terms you need, each explained in one line.
- Inputs you start from and where they are.
- What to use if a dependency hasn't merged yet.

### Steps
1. Concrete action.
2. Next action.

### Done when
- [ ] Verifiable outcome.

### How to check your work
Commands to run or things to look at, and what you should see.

### Out of scope
- Thing not to do here (covered by NOMI-YYY).

### Resources
- Links.
```

---

## Example 1 (Platform)

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

## Example 2 (Data Analysis)

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
