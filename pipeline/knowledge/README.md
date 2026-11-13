# Knowledge base

`ingredients/` holds one YAML file per ingredient UNII: a severity from 0 to 3 for each of the
15 risk dimensions and 8 personas, plus modifiers for conditions and medications. Every rating
above 0 and every modifier cites its source. The dimensions and severities are defined in
`docs/scoring/dimensions.md`; the file format is
`packages/schema/schemas/ingredient-dimensions.schema.json`. The rules below decide how a label
line becomes a rating, so that files rated by different people agree. Notes in the ingredient
files refer to them.

## Any label counts

A line counts when it is printed on any current single-ingredient OTC label for that UNII, by
any route (tablets, liquids, suppositories), because a caregiver could be holding that product. Cite that label. Before rating an ingredient,
search all its single-ingredient labels on openFDA for lines that would raise a rating, not only
the best-known brand.

For a child persona, use the labels whose directions dose that age; duration limits are read
the same way. A limit printed only on one product (such as "children under 12 years: do not use"
on adult tablets) is about that product when another label doses the whole age band. When no
label doses an age, or only part of the band, the strongest line for the undosed ages counts (for
example "under 6 months" on an infants' label that doses 6 months and up sets `under_2`). A line
tied to one use applies only to the ages that use is dosed for: the sore throat warning's
"administer to children under 3 years of age unless directed by doctor" does not set `pediatric`
when a label doses that age, and a limit printed "As an antacid" does not apply to children dosed
only as a laxative. An age that no label doses for any use still falls under the undosed rule above.

In pediatric age lines and duration lines only, "do not use unless directed by a doctor" has
ask-a-doctor strength (2); a plain "do not use" is 3. Elsewhere the wording keeps its rubric
value: examples the rubric names stay 3, such as the NSAID line "not to use ... at 20 weeks or
later in pregnancy unless definitely directed to do so by a doctor". The famotidine and
polyethylene glycol 3350 line "Do not use if you have kidney disease, except under the advice
and supervision of a doctor" is a +3 modifier because it is printed as do not use, which is the
safe side; it stays open for the rubric owner.

Hard stops are not ingredient ratings. They belong in the `hard_stops` table of the term tables
(`packages/schema/schemas/term-tables.schema.json`, `docs/system-design.md`), which scoring
(NOMI-051) will build; nothing builds them yet. The universal `under_2` hard stop for systemic
OTC cough, cold, fever and pain products (`docs/scoring/dimensions.md`, section 3, persona 6) is
therefore open.

Lines about the drug's pharmacology (drug interactions, organ harm) apply to every salt file of
the same moiety, because the salt does not change the pharmacology: a warfarin line on an
omeprazole magnesium label also counts for omeprazole. Product-level lines (ages, dosing,
duration, excipients) stay with the UNII whose labels print them.

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

Some label conditions have no dimension of their own. "Liver cirrhosis" in the NSAID Ask a
doctor line is a `liver_disease` +2 modifier on `kidney`, the main NSAID risk in cirrhosis
(open for the rubric owner: section 4 of `docs/scoring/dimensions.md` maps `liver_disease` only
to `liver`).

Modifier values: by default +2 for "ask a doctor" and +3 for "do not use", unless section 4 of
`docs/scoring/dimensions.md` gives a value for that modifier and drug class (for example
hypertension +1 for NSAIDs).

## Duration limits (`rebound_overuse`)

- An explicit "do not use (take, give) for more than N days" limit, or "not more than N days", is
  2. This is the rubric's own severity 2 example.
- A stop-use line about needing the product for more than N days ("you need to use a laxative
  for more than 1 week") is 1.
- A line about symptoms lasting more than N days ("pain gets worse or lasts more than 10 days")
  is not rated.
