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
scores use the provisional `NOMI-015-fixture-draft-5-15-51-points` convention:

- Apply matching modifiers, capping each ingredient/dimension severity at 3. A modifier on a
  dimension the ingredient does not rate starts from 0.
- Within each dimension, take the highest severity across active ingredients. This is a deliberate
  simplification: system design 6.2 also allows a stacking penalty when two ingredients hit the
  same dimension, which the rubric has not defined yet.
- Deduct 5, 15 or 51 points for severity 1, 2 or 3; clamp the total score to 0-100.
- Use the bands in `docs/system-design.md`: green 75+, yellow 50-74, red below 50.
- Leave out `duplicate_dosing`: the same ingredient in two products is flagged by the Medicine
  Cabinet, not the single-product score (`docs/system-design.md`, section 6.2).
- A label "do not use" at the profile's age (a pediatric severity 3) is a hard stop and forces red.
  Here this applies to ZzzQuil for the child profile. Its rule ID is local to this fixture until
  production hard-stop tables exist.

The points come from the summary table in `docs/scoring/dimensions.md`: the low end of the
severity 1 (5-10) and severity 2 (15-25) ranges, and 51 for severity 3 ("35-50+"), so that one
severity 3 is red as the table's tier column says. The table cannot be met exactly: no value in
15-25 makes a single severity 2 yellow. With these values every product here is yellow or red;
Tylenol is red (49) for a healthy adult because of its liver warning. That is what the rubric table
implies and needs a decision from the rubric owner. Change `POINTS` in `tests/test_examples.py`
and regenerate these records when the rubric is set. They are not production golden vectors.

Four questions for the rubric owner before #29 builds on these numbers:

- **Named label warnings.** The rubric lists both the liver warning and the stomach bleeding
  warning as severity 3 indicators. Tylenol's liver warning is rated 3 for everyone. Aleve's
  stomach bleeding warning is rated 2 for adults and children and 3 for adults 65+, following the
  rubric's own severity 3 example ("Aleve, `adult_65_plus` or ulcer history"); its heart attack and
  stroke warning is rated 2 for every profile and reaches 3 for adults 65+ only through the
  hypertension modifier. So Tylenol is red (49) for a healthy adult and Aleve is yellow (55).
- **Spread.** With 51 points for a severity 3, every adult 65+ record except Tylenol clamps to 0,
  so the fixtures cannot rank those products against each other.
- **NyQuil sedation for adults 65+.** Doxylamine's `sedation_falls` rating of 3 for adults 65+
  follows the knowledge base. The rubric asks for a STOPP criterion that applies without caveats,
  and none does for this profile: K6 needs recurrent falls and D25 is for insomnia. The record
  cites K6 and the label's "marked drowsiness may occur". The score does not change (it is 0
  either way), but the rating may be 2 under the rubric.
- **Modifier values.** The `sedatives` modifier on `sedation_falls` is +1 in the knowledge base
  and these fixtures, but the rubric's table says +2, and the rubric's table has no
  `heavy_alcohol_use` row for `sedation_falls`. Aleve's modifiers cite only its own label, so it
  has no `anticoagulant_bleeding` rating or modifier, and its `diuretics` and `kidney_disease`
  modifiers leave out `cardiovascular_bp`, all of which the rubric lists for NSAIDs. It also has
no `antiplatelets`, `ssri_snri` or `blood_pressure_medications` modifiers.

Pediatric ratings apply to the specific presentation and must not be generalized to every product
containing that ingredient. Dimensions not listed count as 0. The older-adult antihistamine ratings
of 3 rest on published criteria, not on the labels alone: `anticholinergic_cognitive` on the 2023
AGS Beers Criteria, and `sedation_falls` on STOPP v3 K6 ("first generation antihistamines in
patients with recurrent falls"), plus D24 (allergy) or D25 (insomnia) where the product fits. NyQuil
has no such fit; see the open question above. The `anticholinergic_cognitive` ratings of 2 for
adults and children cite the ACB scale (both antihistamines score 3), as the knowledge base does,
alongside the label. Modifiers cite each product's own label, except dextromethorphan's SSRI
modifier, which carries the knowledge base's citation of a published review of dextromethorphan
serotonin toxicity (Monte 2010); a source naming SSRIs directly would be better. For
diphenhydramine, doxylamine and dextromethorphan their values match the knowledge base. Aleve's
hypertension modifier applies to `cardiovascular_bp` and `kidney`, as the rubric's condition table
says for NSAIDs; the label line it cites names high blood pressure, not the kidneys.

## Consistency checks

`tests/test_examples.py` checks that:

- every label citation, in the ingredient ratings and the expected scores, points at this
  product's own label and version and names a known Drug Facts section, with its matching LOINC
  code where it gives one (Warnings subsections such as "Warnings / Liver warning" may omit it);
- every file validates against the #2 schemas;
- each expected score, contribution, tier and hard stop, and the citations of each scored
  dimension's explanation, follow from the ingredient ratings and modifiers under the convention
  above (explanation wording is not checked);
- ingredients that have a file in `pipeline/knowledge/ingredients` (all of them: acetaminophen,
  naproxen sodium, dextromethorphan, doxylamine, diphenhydramine) match it for the three profiles:
  rating severities, and each modifier's dimension, condition or medication, value and personas
  (citations are not compared). The exceptions come from the product's own label and are listed in
  `LABEL_OVERRIDES`: ZzzQuil says "children under 12 yrs do not use" (3), NyQuil says "children 4
  to under 12 yrs ask a doctor" (2, for doxylamine and acetaminophen), and Tylenol Extra Strength
  says "children under 12 years ask a doctor" (2). The knowledge base rates acetaminophen 0 for
  children 6 to 11 because children's liquids are dosed for that age. A test fails if an override
  stops being needed.

## Review

All records remain `unreviewed`. A second person still needs to check each value
against the named label version, approve the severity interpretations, and
confirm or replace the draft scoring convention. No second-person or pharmacist
review is claimed.

The schema CI job runs `tests/test_examples.py`, and also runs when the knowledge base changes.
