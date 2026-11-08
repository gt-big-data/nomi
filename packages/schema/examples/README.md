# Reference products (NOMI-015)

Each folder contains one `product.json`, an `ingredient-dimensions.json` array
(one schema-valid entry per active ingredient), and an `expected-scores.json`
array (one schema-valid score record per profile).

The profiles are adult 18-64, adult 65+ with hypertension, and child 6-11.
No profile takes other medications. Strengths are per tablet/capsule, except
ZzzQuil liquid, which is per 30 mL. Product IDs and label versions come from
the cited DailyMed SPLs. Uses and OTC categories are Nomi groupings.

## Draft scoring convention

The rubric (`docs/rubric/v0.md`) and term tables are not in the repository yet. These expected
scores use the provisional `NOMI-015-fixture-draft-6-points-per-severity` convention:

- Apply matching modifiers, capping each ingredient/dimension severity at 3.
- Within each dimension, take the maximum severity across active ingredients.
- Deduct six points per severity level; clamp the total score to 0-100.
- Use the bands in `docs/system-design.md`: green 75+, yellow 50-74, red below 50.
- Leave out `duplicate_dosing`: the same ingredient in two products is flagged by the Medicine
  Cabinet, not the single-product score (`docs/system-design.md`, section 6.2).
- An explicit label prohibition forces a red tier without changing the score.
  Here this applies to ZzzQuil for the child profile. Its rule ID is local to
  this fixture until production hard-stop tables exist.

Six points is a fixture assumption, not an FDA value or an approved Nomi rubric. The point ranges in
`docs/scoring/dimensions.md` (5-10, 15-25 and 35-50+ per severity) were not used because they
conflict with that file's own tier column: one severity 3 at 35 points scores 65, which is yellow,
not red. Settle that in the rubric, then change `POINTS_PER_SEVERITY` in `tests/test_examples.py`
and regenerate these records. They are not production golden vectors.

Pediatric ratings apply to the specific presentation and must not be generalized to every product
containing that ingredient. Unlisted dimensions count as 0. The older-adult antihistamine ratings
of 3 rest on the 2023 AGS Beers Criteria (first-generation antihistamines), not on the labels alone.

## Consistency checks

`tests/test_examples.py` checks that:

- every file validates against the #2 schemas;
- each expected score follows from the ingredient ratings under the convention above;
- ingredients that have a file in `pipeline/knowledge/ingredients` (dextromethorphan, doxylamine,
  diphenhydramine) match it for the three profiles. The two exceptions come from the product's own
  label and are listed in `LABEL_OVERRIDES`: ZzzQuil says "children under 12 yrs do not use" (3),
  and NyQuil says "children 4 to under 12 yrs ask a doctor" (2).

Acetaminophen and naproxen are not in the knowledge base yet (NOMI-034); add them to the check once
they are.

## Review

All records remain `unreviewed`. A second person still needs to check each value
against the named label version, approve the severity interpretations, and
confirm or replace the draft scoring convention. No second-person or pharmacist
review is claimed.

The schema CI job runs `tests/test_examples.py`, and also runs when the knowledge base changes.
