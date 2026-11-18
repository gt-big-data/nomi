# Scoring v1: evidence-based excess risk

Status: locked on 2026-11-18, before any v1 score was computed. Changing a rule in this file
needs a new version number, and the change log says why. No rule here may be changed because of
the score it gives a particular product.

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
