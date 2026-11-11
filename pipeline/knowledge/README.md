# Knowledge base

`ingredients/` holds one YAML file per ingredient UNII: a severity from 0 to 3 for each of the
15 risk dimensions and 8 personas, plus modifiers for conditions and medications. Every rating
above 0 and every modifier cites its source. The dimensions and severities are defined in
`docs/scoring/dimensions.md`; the file format is
`packages/schema/schemas/ingredient-dimensions.schema.json`. The rules below decide how a label
line becomes a rating, so that files rated by different people agree. Notes in the ingredient
files refer to them.

## Any label counts

A line counts when it is printed on any current single-ingredient OTC label for that UNII,
because a caregiver could be holding that product. Cite that label. Before rating an ingredient,
search all its single-ingredient labels on openFDA for lines that would raise a rating, not only
the best-known brand.

For a child persona, use the labels whose directions dose that age. A limit printed only on an
adult product (such as "children under 12 years: do not use" on adult tablets, when children's
products dose that age) is about that product, not the ingredient. When no label doses an age,
the strongest age line on any label counts.

Product-level differences go in the reference examples (`LABEL_OVERRIDES` in
`packages/schema/tests/test_examples.py`), not in the ingredient files.

## Ask a doctor organ lines

When the drug itself harms an organ, an "Ask a doctor before use if you have" line for a disease
of that organ gives a baseline of 2 plus a modifier. The harm must be stated by the label's own
warning or the monograph, as for NSAIDs and the kidney, and aspirin and decongestants and blood
pressure.

When the line is a clearance precaution (the organ only clears the drug), it is a modifier only,
with no baseline. Examples: kidney disease for magnesium hydroxide, calcium carbonate, famotidine
and cimetidine; liver disease for loperamide, cimetidine, loratadine and cetirizine.

Modifier values: +2 for "ask a doctor", +3 for "do not use".

## Duration limits (`rebound_overuse`)

- An explicit "do not use (take, give) for more than N days" limit, or "not more than N days", is
  2. This is the rubric's own severity 2 example.
- A stop-use line about needing the product for more than N days ("you need to use a laxative
  for more than 1 week") is 1.
- A line about symptoms lasting more than N days ("pain gets worse or lasts more than 10 days")
  is not rated.
