# DailyMed SPL ingest (#11 / NOMI-010)

## Goal

Extract products and ingredients from every DailyMed OTC label, writing `spl_products.parquet` and
`spl_ingredients.parquet` to `data/bronze/`, with at least 98% of OTC labels parsing without error.

## Context

SPL (Structured Product Labeling) is the XML format FDA labels use. DailyMed publishes one XML file
per label (keyed by a stable `setid`), containing the label's products, their package NDCs, and their
active/inactive ingredients.

This ticket depends on `#9` (R2 mirror + `pipeline fetch`) and `#7` (pipeline CLI skeleton, merged).
`#7` is done; `#9` is not yet. The actual parsing logic and its fixture tests do not require `#9` to be
complete — they only need representative real SPL XML files, which this spec includes as fixtures.
Only the final 98%-across-the-real-corpus number (quoted in the eventual PR) requires `#9`'s mirrored
data to exist.

`packages/schema/schemas/product.schema.json` is the eventual **silver-layer** output (built later by
the identity stage, NOMI-025/026) that will consume this ticket's bronze tables. It is not what this
ticket produces directly, but its `active_ingredient`/`inactive_ingredient` shapes (`unii`, `name`,
`strength`, `unit`, optional `per_amount`/`per_unit`) tell us exactly what fields our bronze ingredient
rows must capture so that stage can build on them without re-parsing XML.

## Fixtures

Two real, verified SPL XML files from the DailyMed public API, saved under
`pipeline/tests/fixtures/spl/`:

- `ibuprofen_otc.xml` — AAA Pharmaceutical's ibuprofen tablet (setid `4aba1bf2-8146-04fa-e063-6294a90a8a21`).
  Confirmed `"HUMAN OTC DRUG LABEL"` doc type. 2 package NDCs (`57344-212-03`, `57344-212-05`), 1 active
  ingredient (IBUPROFEN, 200 mg, UNII `WK2XYI10QM`), 10 inactive ingredients.
- `acetaminophen_liquid_otc.xml` — Genexa Kids Pain and Fever suspension (setid
  `5130c695-a80e-2dd3-e063-6294a90a404f`). Confirmed OTC. Covers the liquid-dosage case: active
  ingredient strength is expressed as a ratio (numerator/denominator) — 160 mg per 5 mL.

A third fixture, deliberately malformed (missing `setId`), will be added during implementation to
exercise the failure path.

## Architecture

```
pipeline/src/nomi_pipeline/ingest/
├── __init__.py   # existing Typer sub-app; gets a real "spl" command added
├── spl.py        # parsing logic: parse_label(path) -> ParsedLabel, ParseError
└── _ndc.py       # shared NDC-normalization helper (also reusable by #10's eventual ndc.py)
```

`spl.py` exposes pure functions operating on one parsed XML file at a time. The `ingest spl` Typer
command (added inside `ingest/__init__.py`, alongside the existing placeholder) is the only piece that
touches the filesystem in bulk: it loops over every file in `data/raw/dailymed-otc/*.xml`, calls
`parse_label` on each, and aggregates results. Keeping parsing logic separate from CLI wiring means
`parse_label` can be unit-tested directly against fixtures with no Typer/CliRunner involved.

## Data model

Three output tables, written to `data/bronze/`.

### `spl_products.parquet` — one row per package NDC

| column | type | notes |
|---|---|---|
| `spl_set_id` | string | DailyMed's stable label id |
| `spl_version` | int | version number found in the file |
| `product_index` | int | 0-based index of the product within the file; almost always `0`, but some labels bundle multiple products ("kits") — this is the join key to ingredients |
| `product_name` | string | name from the label's product section |
| `ndc11` | string | normalized, 11 digits, no hyphens |
| `ndc_raw` | string | exactly as found in the XML, kept for debugging |

### `spl_ingredients.parquet` — one row per ingredient, joined via `spl_set_id` + `product_index`

| column | type | notes |
|---|---|---|
| `spl_set_id`, `product_index` | — | join key back to products |
| `role` | string | `"active"` or `"inactive"`, from the XML's `classCode` (`ACTIB`/`ACTIM` vs `IACT`) |
| `unii` | string, nullable | nullable since inactive ingredients sometimes lack one |
| `name` | string | |
| `strength`, `unit` | float/string, nullable | active ingredients only |
| `per_amount`, `per_unit` | float/string, nullable | only set when the XML has a denominator != 1 (liquids etc.) |

### `spl_parse_failures.parquet` — one row per file that failed entirely

| column | type | notes |
|---|---|---|
| `file` | string | filename, e.g. `4aba1bf2-....xml` |
| `error` | string | exception message |

A file that fails never appears in the other two tables; a file that succeeds never appears here.

## NDC normalization

Both this ticket and `#10` (NDC directory ingest) need to normalize package NDCs to 11 digits with no
hyphens (raw NDCs appear in varying segment lengths: 4-4-2, 5-3-2, 5-4-1). This logic lives in
`ingest/_ndc.py` as a standalone pure function so `#10`'s eventual `ndc.py` can import and reuse it
instead of re-implementing normalization independently.

## Error handling

One bad file must never stop the whole run:

```python
try:
    label = parse_label(path)
    products.extend(label.products)
    ingredients.extend(label.ingredients)
except ParseError as e:
    failures.append({"file": path.name, "error": str(e)})
```

`parse_label` raises a single custom `ParseError` for anything that goes wrong — missing required
fields, malformed XML `lxml` can't open — rather than letting raw `lxml` exceptions or `KeyError`s leak
out. This keeps the failure-catching code to one `except` clause and keeps failure messages consistent
in `spl_parse_failures.parquet`.

The command prints a summary like `"1,847 / 1,883 labels parsed (98.1%)"`, computed as
`successful_files / total_files`, which becomes the number quoted in the eventual PR.

## Parsing approach

Using `lxml.etree` (the project's stated XML library per `pipeline/README.md`). SPL XML declares a
namespace (`xmlns="urn:hl7-org:v3"`), so every XPath/find query must include it explicitly — searching
without the namespace silently returns nothing, it does not error.

`parse_label(path: Path) -> ParsedLabel`:
1. Parse the file with `lxml.etree.parse`; wrap parse errors as `ParseError`.
2. Read `setId`/`root` and `versionNumber`/`value` from the document root; raise `ParseError` if
   either is missing — nothing else is salvageable without them.
3. Find every `manufacturedProduct` section (iterate, don't assume exactly one — handles the kit case).
4. For each, read its package NDC codes (normalize each via `_ndc.py`), and walk its `ingredient`
   elements, branching on `classCode` to build active/inactive ingredient rows.
5. Return a small dataclass bundling the product and ingredient rows for that file.

## CLI command

`uv run pipeline ingest spl`, no arguments — matches the ticket's deliverable exactly. Reads from
`settings.raw_dir / "dailymed-otc"`, writes to `settings.bronze_dir`. Both already exist as `Settings`
properties from `#7`. Tests redirect input/output by pointing `Settings`' `data_dir` at a `tmp_path`,
the same pattern `config.py`'s own tests already use — no extra CLI flags needed for testability.

## Testing strategy

1. **`_ndc.py` normalization** — pure-function unit tests across different NDC segment-length formats.
2. **`parse_label` against fixtures** — `ibuprofen_otc.xml` (2 products, 11 ingredients, plain strength),
   `acetaminophen_liquid_otc.xml` (per_amount/per_unit case), and a deliberately broken fixture
   (asserting `ParseError` is raised, not silently swallowed or crashing the test runner).
3. **Full `ingest spl` CLI command**, end to end — `Settings`' `data_dir` pointed at a `tmp_path`
   containing copies of a good and a broken fixture; assert all three Parquet files are written with
   correct row counts, including the broken file landing in `spl_parse_failures.parquet`.

Not automated: running against the full real DailyMed OTC corpus (thousands of files) isn't possible in
CI without `#9` mirroring real data first. The 98%-success number for the PR comes from a manual run
against real data once `#9` unblocks it; automated tests prove the parsing logic is correct on known
cases.
