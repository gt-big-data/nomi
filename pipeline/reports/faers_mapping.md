# FAERS Ingredient Mapping Report (NOMI-046)

## Status & Upstream Dependency
- **Pipeline Stage:** Implemented via `uv run pipeline evidence map-drugs`.
- **Name Matcher:** Evaluated on the 500 hand-labeled FAERS drug names benchmark (`pipeline/tests/fixtures/faers_names_labeled.csv`), achieving $\ge 97\%$ precision on the held-out partition.
- **Dependency Status:** Full dataset run ($\ge 90\%$ coverage across all 62.8M bronze rows) will be executed once the complete RxNorm-to-UNII crosswalk (`data/silver/ingredient_crosswalk.parquet` from NOMI-019) is available.

---

## Mapping Pipeline Specifications
- **Input Table:** `data/bronze/faers/drug.parquet` (62,894,398 rows after NOMI-024 deduplication).
- **Output Table:** `data/silver/faers_drug_ingredient.parquet`.
- **Combination Handling:** Products matching multiple active ingredients (e.g., *Advil PM* $\to$ Ibuprofen + Diphenhydramine) explode into distinct rows with identical report identifiers (`primaryid`, `caseid`, `drug_seq`).
- **Matching Priority:** Exact match $\to$ RxNorm brand/synonym $\to$ Multi-ingredient combination $\to$ Tuned fuzzy match (threshold = 0.85).

---

## Acceptance Criteria Checklist (NOMI-046)
- [x] **Name Matcher Pipeline:** Core matcher scans unique drug names with caching and batch processing.
- [x] **Combination Splitting:** Verified by unit tests to produce one row per constituent active ingredient.
- [x] **Precision Threshold:** $\ge 97\%$ precision enforced by `test_held_out()` on held-out partition.
- [ ] **Full Bronze Coverage ($\ge 90\%$):** Pending NOMI-019 full crosswalk integration.
- [ ] **500 Unmapped Review:** Pending full bronze execution.
- [ ] **200 Spot Check Sample:** Template generated; awaiting full crosswalk generation.
