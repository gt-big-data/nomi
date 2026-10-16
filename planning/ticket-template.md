# How to write a Nomi ticket

Short and clear beats complete. Someone should understand the ticket in under a minute.

## Rules

- **Goal:** one sentence, plain English. What and why.
- **Deliverable:** the thing you hand in. A file path, a screen, a document.
- **Tasks:** 3 to 5 short checkboxes. Each starts with a verb. One line each.
- **Done when:** one or two measurable checks.
- **Notes:** optional, at most 2 lines. Use for a key term or "if X isn't ready, use Y".
- Explain jargon in Notes or rely on the glossary in `docs/nomi-101.md`. Don't write paragraphs.
- No em dashes, no emojis. One bullet per line.
- Aim for 10 to 15 lines per ticket.

## Format

```
## NOMI-XXX: Short verb-first title
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-007, NOMI-009

**Goal:** One sentence.

**Deliverable:** `path/to/output`

**Tasks**
- [ ] Do this
- [ ] Do that
- [ ] Do the other thing

**Done when:** Measurable check.

**Notes:** Optional. Key term or fallback.
```

## Example

```
## NOMI-025: Resolve barcodes to products
**Team:** platform | **Priority:** P0 | **Sprint:** S2 | **Depends on:** NOMI-007, NOMI-009, NOMI-010, NOMI-020

**Goal:** Turn a scanned barcode into the exact product and its ingredients, so the app knows what was scanned.

**Deliverable:** `data/silver/product.parquet` and a coverage report in `pipeline/reports/identity_coverage.md`

**Tasks**
- [ ] Look up each barcode's NDC candidates in the NDC directory
- [ ] Join the match to its DailyMed label to get ingredients and strengths
- [ ] Flag barcodes with zero or multiple matches
- [ ] Run on the collected barcodes and list every miss with its reason

**Done when:** At least 90% of collected barcodes resolve correctly by Oct 29.

**Notes:** NDC is FDA's product code; drug barcodes usually contain it (see NOMI-007).
```
