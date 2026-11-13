Closes #33

## What changed

- **Matching Cascade (`name_matcher.py`):** Added exact match -> RxNorm synonyms -> combination splitting (`/`, `+`, `and`) -> fuzzy matching (`rapidfuzz.token_set_ratio`).
- **Fuzzy Residual Tuning:** Refactored `tune_fuzzy_threshold` to evaluate non-exact/synonym residual queries; tuned optimal cutoff to `0.84` (100% precision, 98.4% recall on residuals).
- **Benchmark Dataset (`faers_names_labeled.csv`):** 
  - Naturalized 500 rows (250 tuning / 250 held-out, 55 double-labeled, 100% agreement).
  - Resolved `ADAVIL 10MG` ground-truth to Ibuprofen (`WK2XYI10QM`).
  - Replaced synthetic clones with diverse OTC typos and graded LASA prescription distractors.

## Blocked by Issue #20 (PR #95)

- Blocked on UMLS license to download `RXNCONSO.RRF` from R2 and build `data/silver/ingredient_crosswalk.parquet`.
- Currently runs on static `SAMPLE_CANONICAL` and `SAMPLE_SYNONYMS` fallback dictionaries. Downstream issue #46 is blocked until both land.

## Next steps when #20 merges

1. Rebase onto `main`.
2. **Switch vocabulary:** Switch the matcher instantiation in pipeline pipelines/CLI from `SAMPLE_CANONICAL`/`SAMPLE_SYNONYMS` to the live `ingredient_crosswalk.parquet` via `FaersNameMatcher.from_parquet()`.
3. Confirm `ingredient_crosswalk.parquet` column schema compatibility with `from_parquet()` (`name`, `unii`, `term_type`/`is_canonical`).
4. Re-run `tune_fuzzy_threshold` against the full RxNorm vocabulary to verify if the optimal cutoff remains `0.84`.

## How I tested it

- `uv run pytest pipeline/tests/test_name_matcher.py -v`: 6 passed (enforces >= 97% precision on held-out).
- `uv run pytest pipeline -v`: 65 passed.
- `uv run ruff check` & `uv run mypy`: 0 errors.

## Checklist
- [x] Tests added or updated
- [x] Pre-commit hooks pass
- [x] Type checking passes (`mypy`)
- [ ] Relevant README updated (N/A)
