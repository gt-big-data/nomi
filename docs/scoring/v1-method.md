# Scoring v1: evidence-based excess risk

Status: v1.0 locked on 2026-11-18, before any v1 score was computed. v1.1 (section 8) and v1.2
(section 9) were added on 2026-11-18 after the first and second independent evidence reviews,
and v1.3 (section 10) after the third; see their change logs. Versions 1.0 to 1.2 were committed on their own, before the evidence
changes they govern, so the order can be checked in git. v1.3 is the one exception: its rule
was written after the evidence change and with its score effect known, and is pending
pharmacist sign-off (section 10). Changing a rule in this file needs a new version number, and
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

29. **Stated comparator.** A row's comparator is `non_use` when the source's reference group is
    non-users of the ingredient or of its class, or when the source states no reference group
    (the usual non-user reference of a cohort or case-control study). When the source states a
    reference group that does not exclude users of the ingredient or its class (for example
    "relative to nonuse of any NANSAID or aspirin" for paracetamol), the row is recorded with
    `comparator: other` and the build drops it. Only a stated reference group decides this, so
    rows whose full text was not opened are not dropped for silence.
