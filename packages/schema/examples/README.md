# Reference products (NOMI-015)

Each folder contains one `product.json`, an `ingredient-dimensions.json` array
(one schema-valid entry per active ingredient), and an `expected-scores.json`
array (one schema-valid score record per profile).

The profiles are adult 18-64, adult 65+ with hypertension, and child 6-11.
No profile takes other medications. Strengths are per tablet/capsule, except
ZzzQuil liquid, which is per 30 mL. Product IDs and label versions come from
the cited DailyMed SPLs. Uses and OTC categories are Nomi groupings.

## Draft scoring convention

`docs/rubric/v0.md` and production term tables have not been added to the
repository. These expected scores therefore use the explicitly provisional
`NOMI-015-fixture-draft-6-points-per-severity` convention:

- Apply matching modifiers, capping each ingredient/dimension severity at 3.
- Within each dimension, take the maximum severity across active ingredients.
- Deduct six points per severity level; clamp the total score to 0-100.
- Use the bands in `docs/system-design.md`: green 75+, yellow 50-74, red below 50.
- An explicit label prohibition forces a red tier without changing the score.
  Here this applies to ZzzQuil for the child profile. Its rule ID is local to
  this fixture until production hard-stop tables exist.

Six points is a fixture assumption, not an FDA value or an approved Nomi rubric.
These records must be recalculated when the team supplies the official rubric;
they are not production golden vectors. Numeric severities are also draft
interpretations. Unlisted dimensions are unassessed, not zero. Pediatric
ratings apply to the specific presentation; they must not be generalized to
every product containing that ingredient. The cited Beers publication supports
older-adult antihistamine ratings; labels alone do not establish that escalation.

## Review

All records remain `unreviewed`. A second person still needs to check each value
against the named label version, approve the severity interpretations, and
confirm or replace the draft scoring convention. No second-person or pharmacist
review is claimed.

The existing schema CI job discovers `tests/test_examples.py`, which validates
each product, ingredient entry, and score record against the unchanged #2 schemas.
