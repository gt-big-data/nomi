# Scoring v1: evidence-based excess risk

Status: v1.0 locked on 2026-11-18, before any v1 score was computed. v1.1 (section 8) and v1.2
(section 9) were added on 2026-11-18 after the first and second independent evidence reviews,
v1.3 and v1.4 (sections 10 and 11) after the third, and v1.6 (section 12) on 2026-11-18 to keep
every v0 rating; see their change logs. Versions 1.0 to 1.2 were committed on their own, before the evidence
changes they govern, so the order can be checked in git. v1.3 and v1.4 are the exceptions: their rules
were written after the evidence changes and with their score effects known, and are pending
pharmacist sign-off (sections 10 and 11). Changing a rule in this file needs a new version number, and
the change log says why. No rule here may be changed because of the score it gives a particular
product.

v1 replaces the v0 severity ratings (`pipeline/knowledge/ingredients/`) as the source of a
product's score. A score is the published probability of serious harm from one course of the
product for this person, put on a fixed scale. Every number in it comes from a cited source or
from FDA data through code in this repository.

## 1. What is measured

For each risk dimension below, the outcome is a serious harm: one that leads to a hospital
admission, an emergency visit or death.

| Dimension | Outcome |
|---|---|
| `liver` | Acute liver injury or acute liver failure |
| `gi_bleeding` | Upper gastrointestinal bleeding or perforation |
| `kidney` | Acute kidney injury |
| `cardiovascular_bp` | Myocardial infarction, stroke or heart failure admission |
| `anticholinergic_cognitive` | Delirium or acute confusion |
| `sedation_falls` | Fall injury (fracture or fall needing care) |
| `serotonergic_interactions` | Serotonin syndrome |
| `anticoagulant_bleeding` | Major bleeding while on an anticoagulant or antiplatelet |
| `pregnancy_lactation` | The specific fetal or neonatal harm the source studies |

The other v0 dimensions (`pediatric`, `rebound_overuse`, `duplicate_dosing`, `excipients`,
`local_skin`, `efficacy_evidence`) are not outcomes, so they give no points. Label "do not use"
lines still make hard stops (section 5).

## 2. Inputs

Every input row cites its source: the document, the table or page, and the exact words or
numbers quoted. Research may not fill a value from memory. A pair with no usable source is
recorded as "insufficient evidence" and gives 0 points; the app says so.

1. **Relative risk** `RR(i, d)`: the risk of outcome `d` with ingredient `i` at OTC or standard
   doses, against no use, with its 95% confidence interval. Preference order: meta-analysis of
   observational studies or trials, then a large cohort or case-control study, then a
   regulatory review that states a pooled estimate.
2. **Effect modification** `RR(i, d | p or c or m)`: where a source reports the relative risk
   for a persona `p` (for example 65 and over), a condition `c` or a co-medication `m`, that
   value replaces `RR(i, d)` for profiles that have it. Where two apply, the larger is used.
3. **Baseline incidence** `b(d, p)`: the annual incidence of outcome `d` in the general
   population of persona `p`'s age band, per person-year. Where a source reports the incidence
   in people with condition `c`, `b(d, p, c)` replaces it for profiles with `c`.
4. **Hard stops** from labels, as in v0.

## 3. The formula

For a product with ingredients `I`, and a profile with persona `p`, conditions `C` and
co-medications `M`:

```
RR_d   = product over i in I of RR(i, d | the profile)   # log relative risks add (design 6.3)
EAR_d  = b(d, p, C) * max(0, RR_d - 1) * T / 365          # excess absolute risk for one course
E      = sum over d of EAR_d                              # chance of any serious harm
score  = clamp(100 - 25 * (log10(E) + 5), 0, 100)         # E = 0 gives 100
```

- `T`, the course, is 10 days for every product: the longest course OTC pain, fever and cold
  labels allow without a doctor.
- The scale is fixed by the CIOMS frequency bands that drug labelling uses, against the tier
  bands already in the design (green 75 and up, yellow 50 to 74, red below 50):

  | Excess risk per course | CIOMS band | Score | Tier |
  |---|---|---|---|
  | 1 in 100,000 or less | very rare | 100 | green |
  | 1 in 10,000 | very rare / rare boundary | 75 | green |
  | 1 in 1,000 | rare / uncommon boundary | 50 | yellow |
  | 1 in 100 | uncommon / common boundary | 25 | red |
  | 1 in 10 | common | 0 | red |

- A dimension's row in the app shows its share of the points:
  `points_d = (100 - score) * EAR_d / E`.

## 4. FAERS

FAERS signals (BCPNN information component, `IC025 > 0` counts as a signal, per ingredient,
event group, age band and sex) are computed from the team's deduplicated FAERS pairs and shown
as supporting evidence. They give no points: FAERS has no denominator, so it cannot give a
risk (design 6.4). A pair where FAERS shows a signal and the literature has no estimate is
flagged for review.

## 5. Hard stops

A label line that says "do not use" for the profile's age, or for a condition the profile has,
makes the product red, as in v0. These come from the labels, not from the evidence table.

## 6. What needs a pharmacist

- The outcome chosen for each dimension.
- Whether a source's population and dose match OTC use.
- The single function from excess risk to score, which a pharmacist panel calibrates in a later
  version using pairwise judgments (design 6.3).

## 7. How the inputs are matched (fixed before any score was computed)

These rules settle what sections 2 and 3 leave open. They were written on 2026-11-18 while the
evidence table was still being collected, before any v1 score existed.

1. **Measures.** An odds ratio, hazard ratio or incidence rate ratio is used as the relative
   risk. Every v1 outcome is rare (well under 10% a year), where the three agree.
2. **Point estimates.** The point estimate is used, whatever its confidence interval. The
   interval is shown next to it in the app. An estimate at or below 1 gives no excess risk.
3. **Which relative risk applies.** A row applies to a profile when its persona is `all` or the
   profile's persona, its condition is absent or one the profile has, and its co-medication is
   absent or one the profile takes. If any row with a persona other than `all`, a condition or a
   co-medication applies, the largest of those is used; otherwise the largest general row.
4. **Ingredients without a row** for a dimension add nothing to `RR_d` (a factor of 1).
5. **Which baseline applies.** The same matching as rule 3, with one addition: `pregnant` and
   `breastfeeding` use the `adult_18_64` age band when no row names them. A baseline row with a
   condition or co-medication replaces the general one; where several apply, the largest.
6. **No baseline means no estimate.** If a dimension has an excess relative risk but no
   baseline applies, it gives 0 points and is listed as insufficient evidence.
7. **Insufficient evidence** rows whose reason names a persona, condition or co-medication
   (`applies_to persona X`, `condition X`, `medication_type X`) are listed only for profiles that
   have it; the others are listed for every profile.
8. **Rounding.** The score is rounded to a whole number. Row points are rounded so they add up to
   `100 - score` (largest remainder).
9. **Coverage.** A product is scored only when every active ingredient has been through the
   evidence review: each outcome dimension the v0 knowledge base rated above 0 for it has a
   relative-risk row or an insufficient-evidence entry. Otherwise it is unrated, as in v0.

## 8. Version 1.1: rules from the independent evidence review

Change log. The first independent review (2026-11-18) found inputs that did not measure what
sections 1 and 2 require: a kidney baseline counting mild blood-test AKI, a kidney risk for
chronic renal impairment, a single study used where a meta-analysis existed, risks measured
inside a subgroup multiplied by whole-population rates, multi-year and in-hospital exposures
standing in for a 10-day course, and bleeding counted twice for anticoagulant users. These rules
make sections 1 and 2 checkable on every row. They were written from the review's findings about
the inputs, not from any score, and apply to every ingredient alike.

10. **Outcome match.** Every relative-risk and baseline row records `outcome_match: true` only
    when its outcome is the dimension's outcome in section 1 at the serious level (hospital
    admission, emergency visit or death). A broader outcome (any AKI from blood tests, chronic
    kidney disease, any bleeding) or a different one (fracture for a fall-injury baseline) is
    `false`. Rows with `false` are not used; if nothing else applies the pair is insufficient
    evidence. A relative risk and its baseline must measure the same outcome.
11. **Exposure match.** Every relative-risk row records `exposure: community_oral` (current or
    recent use outside hospital, any duration, oral or the product's route), `long_term`
    (exposure defined by months or years of continuous use) or `inpatient` (given in hospital,
    including intravenous). Only `community_oral` rows are used.
12. **Comparator.** Every relative-risk row records `comparator: non_use` or `within_group`. A
    `within_group` row (for example NSAID plus diuretic against diuretic alone) is used only with
    a baseline for that same group (same condition or co-medication). Without one, the pair is
    insufficient evidence for that profile; the general row is not used in its place.
13. **Preference order is strict.** A meta-analysis that reports a quotable pooled estimate for
    the outcome and exposure is used over any single study, whether or not its full text could
    be opened. Among meta-analyses, the most recent with the largest population.
14. **Dose strata.** Where a source reports dose strata, every stratum is recorded with its
    `dose_mg_per_day` range. The stratum used is set in section 8.1.
15. **Baselines.** A baseline that excludes users of the ingredient's class is used over one that
    does not, when the source reports both. Where a source reports a rate for the
    persona's whole age range (for example 65 and over), that rate is used. Otherwise the source's
    band that contains the median age of the persona's US population (US Census Bureau, cited
    once in baselines.yaml as `persona_median_ages`) is used. (Amended before any v1.1 score was
    computed: the first wording, "the band covering the largest share of the age range", picks
    an open-ended oldest band such as 85 and over for every older-adult baseline, which does not
    represent the persona.)
16. **No double counting.** When `anticoagulant_bleeding` has a term for a profile, its baseline
    already includes gastrointestinal bleeding, so the `gi_bleeding` term is dropped for that
    profile.
17. **Scoped notes** (supersedes the open part of rule 7). Insufficient-evidence notes for
    `pregnancy_lactation` are shown only to pregnant and breastfeeding profiles, and for
    `anticoagulant_bleeding` only to profiles on anticoagulants or antiplatelets.

### 8.1 Dose stratum (decided 2026-11-18, before any v1.1 score)

Where an ingredient has dose-stratified rows, the stratum used is the one whose
`dose_mg_per_day` range contains the most the ingredient may be taken per day for adults
without a doctor: the daily maximum in the FDA OTC monograph, or, for an ingredient sold OTC
under an NDA, its approved OTC label. That maximum is recorded once per ingredient as
`max_daily_dose_mg` with its citation. The score then covers any use the label permits. When no
stratum contains the maximum, the highest stratum below it is used.

### 8.2 How v1.1 is applied (fixed before any v1.1 score)

18. **Outcome ids.** Every relative-risk and baseline row carries an `outcome` id from a fixed list
    per dimension (for falls: `fall_injury`, `fracture` or `hip_fracture`). A relative risk is
    paired only with a baseline that has the same id. Within one dimension, ingredients whose
    rows measure different outcomes form separate terms, and the dimension counts the largest
    of them, since one outcome contains the other (a fracture is a fall injury) and adding them
    would count the same harm twice.
19. **What the build drops.** Relative-risk rows with `outcome_match: false` or an exposure
    other than `community_oral`, dose strata other than the one rule 8.1 picks, and baselines
    with `outcome_match: false` are left out of the app's table and listed in
    `pipeline/reports/evidence_coverage.md`. A pair left with no usable row becomes insufficient
    evidence for the profiles the dropped rows applied to.

## 9. Version 1.2: rules from the second independent evidence review

Change log. The second review (2026-11-18) found that most remaining errors came from pairing a
study's relative risk with a baseline from a different population or outcome definition, and from
dose strata settled by judgment rather than rule 8.1. It also noted that the rule 15 amendment was
committed with the evidence it governed, so its order could not be checked; from v1.2 on, rules are
committed first. These rules were written from the review's findings about the inputs, before any
v1.2 evidence or score, and apply to every ingredient alike.

20. **Same-study baseline first.** When a relative-risk source reports the incidence of the
    outcome in its own unexposed group (non-users, or the reference group of a within-group
    comparison), that incidence, converted to per person-year with the arithmetic shown, is the
    baseline for that row (`unexposed_incidence`, with its own quote). Only when the source
    reports none is an outside baseline used, and then it must use the same outcome definition
    (rule 10) and the same kind of population (general population, or the same group for a
    within-group row). Otherwise the pair is insufficient. When several ingredients in one term
    carry their own baselines, the baseline of the row with the largest relative risk is used.
21. **Dose at the label maximum beats an undosed pool.** Rule 8.1 applies to every source with
    dose strata, including a single study inside a meta-analysis paper. A stratum that contains
    the label maximum, from a cohort, case-control study or meta-analysis, is used over a pooled
    estimate that does not report dose, because the pooled estimate describes a mix of doses
    below the maximum the score covers. Otherwise rule 13 holds: a meta-analysis over a single
    study. The build enforces this order; curation does not decide it.
22. **Exposure measured in other units.** Strata in days a month or tablets a week are recorded
    with `dose_mg_per_day` only when the source states the tablet strength; otherwise they are
    recorded with `dose_mg_per_day: null` and a note, and the pair uses the source's overall
    estimate. Exposure assessed as habitual use over years (questionnaires repeated every few
    years) is `long_term`.
23. **Joint exposure is not the ingredient's risk.** An estimate for the ingredient and a
    co-medication together, against neither, includes the co-medication's own risk. It is used
    only as `within_group` against the co-medication alone, with that group's baseline; otherwise
    the pair is insufficient.
24. **Outcome ids for heart outcomes.** `cardiovascular_bp` rows use `mi`, `stroke` or
    `mi_stroke`, and pair only with a baseline of the same id (rule 18).
25. **Stratum matching the baseline's population.** When a source reports the relative risk
    separately for subgroups (for example vitamin K antagonist and direct oral anticoagulant
    users), the stratum whose population matches the baseline's is used, not the larger.
26. **Baseline preference order.** Same-study (rule 20); then a rate that excludes users of the
    ingredient's class; then the age rule (rule 15); then, between two rates for the same whole
    range, the one from the larger population-based source. A rate age-standardised to all ages
    is not used for an age-band persona.
27. **Interval type.** Rows record `interval: confidence` or `interval: credible`, and the app
    labels them that way.
28. **Notes say what was used.** An insufficient-evidence entry for a subgroup the general
    estimate still covers reads, in the app, "no estimate specific to X; the general estimate is
    used". A rule 19 entry made for a dropped row applies only to profiles with every attribute
    of that row (persona, condition and co-medication together), and only when no usable row
    covers them.

## 10. Version 1.3: the comparator rule

Change log. The third independent review (2026-11-18) found that commit 6efc214 dropped Lewis
2002's paracetamol rows for their reference group under a criterion that was not written here,
and so was not applied to every row. Rule 29 writes the criterion down. Unlike earlier versions,
it is committed after the evidence change it governs, and after its effect on the acetaminophen
scores was known: with Lewis dropped, Gonzalez-Perez 2006 sets acetaminophen's stomach-bleeding
term. The alternative reading, dropping rows whose source states no reference group, was also
open and would have changed more scores: it would drop Gonzalez-Perez 2006 (acetaminophen
stomach bleeding), Cho 2018 (diphenhydramine and doxylamine falls, 65 and over) and Schneider
2006 (naproxen kidney, 65 and over), since their abstracts state no reference group. Rule 29
takes the usual default that an unstated reference is non-use. That order and choice are
recorded here so they can be judged. Until a pharmacist signs off on rule 29, the scores that
depend on it are provisional.

Later on 2026-11-18 the Gonzalez-Perez 2006 full text was opened. Its reference group is stated
("non-users of each respective drug group"), so it is non-use under either reading. Its Table 1
reports five dose strata, which are now recorded as rule 22 requires; the stratum holding the
4,000 mg label maximum (4,000 mg or more, RR 6.5) is the one rules 8.1 and 21 select. Rule 29
still decides whether Lewis 2002's paracetamol rows, a meta-analysis that rule 13 would otherwise
prefer, are used.

29. **Stated comparator.** A row's comparator is `non_use` when the source's reference group is
    non-users of the ingredient or of its class, or when the source states no reference group
    (the usual non-user reference of a cohort or case-control study). When the source states a
    reference group that does not exclude users of the ingredient or its class (for example
    "relative to nonuse of any NANSAID or aspirin" for paracetamol), the row is recorded with
    `comparator: other` and the build drops it. Only a stated reference group decides this, so
    rows whose full text was not opened are not dropped for silence.

## 11. Version 1.4: nested dose strata

Change log. The third review found that Gonzalez-Perez 2006 reports three estimates that all
contain the 4,000 mg label maximum: more than 2 g a day (RR 3.6), 4,000 mg or more (6.5), and
more than 2 g a day for under 3 months (10.5). No rule chose between them, and the build's
tie-break (the stratum with the lowest floor) was undocumented. The user chose rule 30 on
2026-11-18 from three written options, knowing their effects on acetaminophen (82, 75 or about
69); it is recorded here so it can be judged. No other source in the table has nested strata
that contain the label maximum, so the rule changes no other score.

30. **Nested strata.** When several dose strata from one source contain the label maximum, the
    narrowest is used: the highest floor, then the lowest ceiling. Every stratum is still
    recorded with its stated range (rule 14). A stratum defined by duration as well as dose is
    not a dose stratum; it is recorded with `dose_mg_per_day: null` and a note, and rule 21
    gives way to the dose stratum that contains the maximum.

## 12. Version 1.6: one rating from the label ratings and the studies

Change log. Up to v1.4, a risk with no usable study counted as zero, so v1 dropped every v0
rating that came from FDA labels, OTC monographs, the ACB scale, Beers, STOPP/START or LactMed
whenever no study passed rules 1 to 30, and a product whose label warns about a harm could score
100. A first fix (v1.5, commit 1bad48f) added v0's uncalibrated points on top of v1's scale and was
withdrawn (revert da87c62); v1.5 is not used. v1.6 puts every v0 rating on v1's scale instead: a
v0 severity is turned into an excess risk per course by a mapping fitted, by the fixed rule below,
to the risks where v0 and a study rate the same thing. Rules 31 to 36 were written and committed
on 2026-11-18 before the mapping's values or any v1.6 score were computed. They apply to every
ingredient alike. Section 1's limit to outcome dimensions is replaced by rule 31; everything else
in sections 1 to 11 still governs the study terms.

31. **Every v0 rating counts.** For a product and profile, the v0 severity of each ingredient on
    each dimension is the one `engine.ts` computes: the persona rating, or the label's where the
    label was checked, plus the modifiers that match the profile, capped at 3. Every dimension v0
    scores counts (all of section 1 of `dimensions.md` except `duplicate_dosing`, which v0 leaves
    to the Medicine Cabinet), including those with no outcome in section 1 above.
32. **What a study covers.** An ingredient is covered on a dimension for a profile when a
    relative-risk row of its applies (rule 3), and either the relative risks of that outcome
    multiply to 1 or less (a study that finds no excess risk) or that outcome has a baseline
    (rules 6, 12, 20 and 25), and every v0 modifier that raised its severity for this profile
    (a condition or co-medication) is the row's own condition or co-medication. A study measured
    without the profile's condition does not cover the extra risk the label gives for it.
33. **Calibration pairs.** A pair is an ingredient, outcome dimension and persona that v0 rates
    above 0 (ingredient rating, no label or modifier) and that a study covers for a profile with
    that persona and no condition or co-medication, with the study term's excess risk for that
    ingredient alone (0 when the relative risk is 1 or less). Pairs with the same dimension,
    severity, study rows and excess risk (salts of one ingredient, or personas that share a row
    and a baseline) count once.
34. **What a severity means.** `L(s)`, the excess risk per course for v0 severity `s` of 1, 2 or
    3, is the arithmetic mean of the excess risk of the pairs at severity `s`. The mean is used,
    not the median, because the score adds probabilities (section 3): for a rating with no
    study, the best estimate of its excess risk is the average excess risk measured where that
    severity was studied, zeros included. The three means are then made non-decreasing by
    isotonic regression (pool adjacent violators, each level weighted by its number of pairs):
    "the fitted line is non-decreasing ... [and] lies as close to the observations as possible"
    (Wikipedia, Isotonic regression, opened 2026-11-18). A severity with no pair takes the mean
    of the fitted values of the nearest severities above and below that have pairs, or the one
    such value at an end. With no pair at all, `L(s)` is 0 and every rating is listed as not
    yet calibrated. The pairs and the three values are printed in this file after they are
    computed, and a test pins them.
35. **One harm, one term.** For each dimension, the study term is computed by rules 1 to 30.
    Each rated ingredient (severity above 0) not covered by rule 32 gives a rating term
    `L(severity)`. The dimension counts the largest of its study term and its rating terms,
    never their sum, as rule 18 does for outcomes: they describe the same harm. Rule 16 applies
    to the result: when `anticoagulant_bleeding` counts for a profile, `gi_bleeding` is dropped.
    Then section 3 as before: `E` is the sum over dimensions, the score is `100 - 25 *
    (log10(E) + 5)` clamped to 0 to 100, and row points are shared by excess risk (rule 8).
    Hard stops and the child-label rule are v0's, unchanged.
36. **What the app says.** A row whose larger term is a study keeps the v1 sentence. A row whose
    larger term is a rating says which ingredients are rated what for this profile, what raised
    it, that no study passed the rules for it, and the excess risk `L(s)` that rating stands for,
    with v0's citations and quote. Both use `template_id` `engine_v1_<dimension>`. An
    insufficient-evidence note is not shown for a dimension that a rating term fills.

### 12.1 What is still judgment in v1.6

- That one severity scale means the same excess risk across dimensions. `dimensions.md` section 2
  defines one 0 to 3 scale for all dimensions; the pairs are pooled across dimensions because no
  dimension has enough of its own.
- That non-outcome dimensions (`pediatric`, `rebound_overuse`, `excipients`, `local_skin`,
  `efficacy_evidence`) take the same `L(s)`: their ratings are not risks of a serious harm in
  section 1's sense, but the requirement is that every v0 rating counts, and the shared scale is
  the only one with a fitted value.
- The pairs come only from the risks the evidence review has studied, mostly NSAIDs, decongestants,
  acetaminophen and first-generation antihistamines in older adults.
- Section 6's open items still need a pharmacist.

### 12.2 The fitted values (computed 2026-11-18 by rule 34, after rules 31 to 36 were committed)

`calibrate()` in `apps/mobile/src/scoring/engineV1.ts`, on the bundled `ratings.json` and
`evidence.json`, finds 17 pairs (rule 33). Excess risk is per 10-day course; each comes from the
cited relative risk and baseline in `evidence.json`.

| Severity | Ingredient (the others that repeat the pair) | Dimension | Persona | Excess risk |
|---|---|---|---|---|
| 1 | oxymetazoline | cardiovascular_bp | adult_18_64 | 0 (RR 0.69) |
| 2 | phenylephrine (and pseudoephedrine) | cardiovascular_bp | adult_18_64 | 0 (RR 0.69) |
| 2 | acetaminophen | pregnancy_lactation | pregnant | 0 (RR 0.95) |
| 2 | naproxen | gi_bleeding | adult_18_64 | 7.558e-5 |
| 2 | naproxen | cardiovascular_bp | adult_18_64 | 3.585e-6 |
| 2 | naproxen | cardiovascular_bp | adult_65_plus | 1.886e-5 |
| 2 | naproxen | kidney | adult_65_plus | 2.451e-4 |
| 2 | aspirin | gi_bleeding | adult_18_64 | 3.470e-4 |
| 2 | ibuprofen sodium (and ibuprofen) | gi_bleeding | adult_18_64 | 1.975e-5 |
| 2 | ibuprofen sodium (and ibuprofen) | cardiovascular_bp | adult_18_64 | 6.236e-7 |
| 2 | ibuprofen sodium (and ibuprofen) | cardiovascular_bp | adult_65_plus | 3.280e-6 |
| 2 | ibuprofen sodium (and ibuprofen) | kidney | adult_65_plus | 2.244e-4 |
| 3 | acetaminophen | liver | adult_18_64 | 6.372e-6 |
| 3 | naproxen | gi_bleeding | adult_65_plus | 7.558e-5 |
| 3 | aspirin | gi_bleeding | adult_65_plus | 3.470e-4 |
| 3 | ibuprofen sodium (and ibuprofen) | gi_bleeding | adult_65_plus | 1.975e-5 |
| 3 | diphenhydramine (and the other first-generation antihistamines) | sedation_falls | adult_65_plus | 1.599e-3 |

The means are already non-decreasing, so pooling changes nothing:

| Severity | Pairs | `L(s)`, excess risk per course | About | Score of that risk alone |
|---|---|---|---|---|
| 1 | 1 | 0 | none | 100 |
| 2 | 11 | 8.529e-5 | 1 in 12,000 | 77 |
| 3 | 5 | 4.096e-4 | 1 in 2,400 | 60 |

Severity 1 rests on one pair. It agrees with `dimensions.md`, which defines severity 1 as effects
that "do not result in organ damage, functional disability, or medical intervention", but it is
the weakest of the three values. `engineV1.test.ts` pins these values, so a change in the
evidence that moves them shows up as a deliberate update.
