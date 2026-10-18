# Risk dimensions, severity, personas and modifiers

**Status:** draft for review (NOMI-016)

## How to use this doc

This is the shared vocabulary for scoring. Every ingredient in the knowledge base
(`pipeline/knowledge/ingredients/`) gets a **severity** from 0 to 3 on each **risk dimension**, for
each **persona**. **Modifiers** raise a severity when the user has a condition or takes a type of
medication. The rubric (`docs/rubric/v0.md`, NOMI-049) turns severities into points.

The ids in this doc are the ones in `packages/schema/schemas/common.schema.json`. This doc owns them:
change them here first, then in the schema, in the same PR. Ids are never renamed, only deprecated
(see the change log at the bottom).

Label wording below is typical Drug Facts text. Exact wording varies by product, so always cite the
specific DailyMed label (set id and section) you used, never this doc.

## 1. Risk dimensions

| id | Name | Shown to users as | What it covers | Example ingredients | Example label wording |
|---|---|---|---|---|---|
| `liver` | Liver | Liver damage | Liver injury, mostly from too much acetaminophen or combining it with alcohol | acetaminophen | "Liver warning: This product contains acetaminophen. Severe liver damage may occur if you take more than [the maximum] in 24 hours, with other drugs containing acetaminophen, or 3 or more alcoholic drinks every day while using this product." |
| `gi_bleeding` | GI bleeding | Stomach bleeding | Stomach ulcers and bleeding | ibuprofen, naproxen, aspirin | "Stomach bleeding warning: This product contains an NSAID, which may cause severe stomach bleeding. The chance is higher if you are age 60 or older..." |
| `cardiovascular_bp` | Heart and blood pressure | Heart and blood pressure | Heart attack, stroke, heart failure, raised blood pressure | NSAIDs except aspirin, pseudoephedrine, phenylephrine | NSAIDs: "Heart attack and stroke warning: NSAIDs, except aspirin, increase the risk of heart attack, heart failure, and stroke." Decongestants: "Ask a doctor before use if you have heart disease, high blood pressure..." |
| `kidney` | Kidney | Kidney problems | Kidney injury, or build-up of drugs and minerals when kidneys work poorly | NSAIDs, magnesium and aluminum antacids and laxatives | NSAIDs: "Ask a doctor before use if... you have kidney disease." Magnesium laxatives: "Ask a doctor before use if you have kidney disease." |
| `anticholinergic_cognitive` | Memory and thinking | Memory and thinking | Confusion, memory problems, and long-term cognitive risk from anticholinergic drugs, mainly in older adults | diphenhydramine, doxylamine, chlorpheniramine | Usually no label wording. Set from the ACB scale and STOPP/START, not the label. |
| `sedation_falls` | Drowsiness and falls | Drowsiness and falls | Drowsiness, slowed reactions, falls, impaired driving | diphenhydramine, doxylamine, chlorpheniramine | "When using this product: marked drowsiness may occur; avoid alcoholic drinks; alcohol, sedatives, and tranquilizers may increase drowsiness; be careful when driving a motor vehicle or operating machinery." |
| `serotonergic_interactions` | Dangerous drug combinations | Dangerous drug combinations | Serious interactions with other medications, such as serotonin syndrome | dextromethorphan | "Do not use if you are now taking a prescription monoamine oxidase inhibitor (MAOI)... or for 2 weeks after stopping the MAOI drug." |
| `anticoagulant_bleeding` | Bleeding with blood thinners | Bleeding with blood thinners | Extra bleeding risk when combined with anticoagulant or antiplatelet drugs | aspirin, NSAIDs, bismuth subsalicylate | "Ask a doctor or pharmacist before use if you are taking a prescription drug for anticoagulation (thinning the blood)." |
| `pediatric` | Risks for children | Not safe for this age | Child-specific dangers and age limits | aspirin and other salicylates (Reye's syndrome), cough and cold products under 4 | "Reye's syndrome: Children and teenagers who have or are recovering from chicken pox or flu-like symptoms should not use this product." Cough/cold: "do not use in children under 4 years of age." |
| `rebound_overuse` | Rebound and overuse | Gets worse with overuse | Symptoms that return or worsen with frequent or prolonged use, and misuse potential | oxymetazoline and other nasal decongestant sprays, tetrahydrozoline eye drops, stimulant laxatives | "Do not use for more than 3 days... Frequent or prolonged use may cause nasal congestion to recur or worsen." |
| `pregnancy_lactation` | Pregnancy and breastfeeding | Pregnancy and breastfeeding | Risk to a pregnancy or a breastfed baby | NSAIDs late in pregnancy | "It is especially important not to use [the NSAID] during the last 3 months of pregnancy unless definitely directed to do so by a doctor because it may cause problems in the unborn child or complications during delivery." |
| `duplicate_dosing` | Accidental double dosing | Same ingredient in other products | Taking the same ingredient twice from two products | acetaminophen, diphenhydramine | "Do not use with any other drug containing acetaminophen (prescription or nonprescription)." Diphenhydramine: "Do not use with any other product containing diphenhydramine, even one used on skin." |
| `excipients` | Inactive ingredients | Problem inactive ingredients | Dyes, alcohol, sugar, sodium, phenylalanine and other inactive ingredients that matter for some people | aspartame-sweetened chewables, alcohol-containing liquids, colored products | "Phenylketonurics: contains phenylalanine [amount] per tablet." Sodium content statements. Dyes listed under Inactive ingredients. |
| `local_skin` | Skin and local effects | Skin irritation | Irritation, sun sensitivity and absorption risks from products applied to skin, eyes or nose | benzoyl peroxide, topical diphenhydramine, hydrocortisone | Benzoyl peroxide: skin irritation and dryness warnings. Topical diphenhydramine: "Do not use on large areas of the body." |
| `efficacy_evidence` | Does it work | Weak evidence it works | Ingredients with poor or no evidence of effectiveness, so the risk buys little benefit | oral phenylephrine, homeopathic products | No label wording. FDA proposed in 2024 to remove oral phenylephrine from the OTC monograph after an advisory committee found it ineffective as a decongestant; confirm current status before citing. Homeopathic products are not evaluated by FDA. |

## 2. Severity scale

One severity per ingredient, dimension and persona. Pick the **highest** level whose criteria are met.

| Level | Meaning | Criteria (any one is enough) |
|---|---|---|
| **0** | No meaningful risk | No relevant warning, criterion or published evidence for this dimension and persona. Write 0 explicitly so reviewers know it was considered. |
| **1** | Minor or conditional risk | Risk only if the product is misused (over the maximum dose, too long, with alcohol); a general caution that applies to everyone ("If pregnant or breast-feeding, ask a health professional"); ACB score 1. |
| **2** | Meaningful risk | A label "Ask a doctor before use" or "Stop use" item that applies to this persona; a mandated warning that applies at the labeled dose (for example the NSAID stomach bleeding warning for adults); "marked drowsiness" wording; ACB score 2; a STOPP/START "use with caution" criterion. |
| **3** | Serious risk | A label "Do not use" that applies to this persona; a mandated warning that names this persona as higher risk (for example "age 60 or older" for older adults); ACB score 3 for older adults; a STOPP/START "avoid" criterion. |

Rules:

- **Label "Do not use" for a persona or condition is also a hard stop** in the rubric (the product shows red), on top of severity 3.
- **FAERS can support a rating but not set one.** A FAERS signal (IC025 above 0) can justify the higher of two levels you're choosing between. It can't move a rating up from 0 on its own.
- **When in doubt between two levels, choose the higher one** and note why in the citation `quote` or the file's `notes`.

Worked examples:

| Level | Example | Why |
|---|---|---|
| 0 | acetaminophen, `gi_bleeding`, `adult_18_64` | No stomach bleeding warning on acetaminophen labels; not an NSAID. |
| 1 | acetaminophen, `liver`, `adult_18_64` | The Liver warning applies only above the maximum dose, with other acetaminophen products, or with heavy drinking. Modifiers `liver_disease` and `heavy_alcohol_use` raise it. |
| 2 | naproxen, `gi_bleeding`, `adult_18_64` | The mandated Stomach bleeding warning applies to every adult at the labeled dose. |
| 3 | naproxen, `gi_bleeding`, `adult_65_plus` | The same warning says the chance is higher at age 60 or older; STOPP/START also flags NSAIDs in older adults. |
| 3 | diphenhydramine, `anticholinergic_cognitive`, `adult_65_plus` | ACB score 3 and a STOPP/START "avoid" criterion for strongly anticholinergic drugs in older adults. |

## 3. Personas

A profile has exactly one persona.

| id | Who | Age range | Notes |
|---|---|---|---|
| `adult_18_64` | Adult | 18 to 64 | Default if the user skips onboarding |
| `adult_65_plus` | Older adult | 65 and over | Labels often say "age 60 or older"; ages 60 to 64 fall in `adult_18_64`, so rate those label statements on `adult_65_plus` and mention the age-60 threshold in the explanation |
| `teen_12_17` | Teen | 12 to 17 | Most adult OTC directions say "adults and children 12 years and over", which covers this band; Reye's syndrome warnings also apply |
| `child_6_11` | Child | 6 to 11 | Label band "children 6 to under 12 years" |
| `child_2_5` | Young child | 2 to 5 | Label band "children 2 to under 6 years" |
| `under_2` | Baby | Under 2 | Most OTC labels say "children under 2 years: ask a doctor" or "do not use" |
| `pregnant` | Pregnant | Adult | Replaces the age persona while pregnant |
| `breastfeeding` | Breastfeeding | Adult | Replaces the age persona while breastfeeding |

Mapping label age bands onto personas: if a label rule covers **any part** of a persona's age range,
apply it to the whole persona. Example: "do not use in children under 4 years" applies to all of
`child_2_5`, even though 4 and 5 year olds are allowed. This errs on the side of caution.

## 4. Modifiers

Modifiers raise severity on specific dimensions when the user has the condition or takes the
medication type. Each modifier row in the knowledge base needs its own citation.

| id | Shown to users as | Type | Dimensions it affects | Typical label source |
|---|---|---|---|---|
| `hypertension` | High blood pressure | condition | `cardiovascular_bp`, `kidney` | NSAIDs and decongestants: "Ask a doctor before use if you have high blood pressure" |
| `heart_disease` | Heart disease | condition | `cardiovascular_bp` | NSAIDs and decongestants: "Ask a doctor before use if you have heart disease" |
| `kidney_disease` | Kidney disease | condition | `kidney` | NSAIDs, magnesium antacids and laxatives: "Ask a doctor before use if you have kidney disease" |
| `liver_disease` | Liver disease | condition | `liver` | Acetaminophen: "Ask a doctor before use if you have liver disease" |
| `stomach_ulcer_or_bleeding` | Stomach ulcers or bleeding | condition | `gi_bleeding` | NSAIDs: "The chance is higher if you have had stomach ulcers or bleeding problems" |
| `glaucoma` | Glaucoma | condition | `anticholinergic_cognitive` | First-generation antihistamines: "Ask a doctor before use if you have glaucoma" |
| `enlarged_prostate` | Enlarged prostate or trouble urinating | condition | `anticholinergic_cognitive`, `cardiovascular_bp` | Antihistamines and decongestants: "trouble urinating due to an enlarged prostate gland" |
| `asthma` | Asthma or breathing problems | condition | `cardiovascular_bp` | NSAIDs list asthma; antihistamines list "a breathing problem such as emphysema or chronic bronchitis". Confirm on labels which dimension fits best and note it in the PR. |
| `diabetes` | Diabetes | condition | `cardiovascular_bp`, `excipients` | Decongestants: "Ask a doctor before use if you have diabetes"; sugar content in liquids |
| `thyroid_disease` | Thyroid disease | condition | `cardiovascular_bp` | Decongestants: "Ask a doctor before use if you have thyroid disease" |
| `phenylketonuria` | Phenylketonuria (PKU) | condition | `excipients` | "Phenylketonurics: contains phenylalanine" |
| `heavy_alcohol_use` | 3 or more alcoholic drinks a day | condition | `liver`, `gi_bleeding`, `sedation_falls` | Acetaminophen Liver warning and NSAID Stomach bleeding warning mention 3 or more drinks every day |
| `anticoagulants` | Blood thinners | medication | `anticoagulant_bleeding`, `gi_bleeding` | NSAIDs, aspirin, bismuth subsalicylate: "taking a prescription drug for anticoagulation (thinning the blood)" |
| `antiplatelets` | Antiplatelet drugs (e.g. clopidogrel) | medication | `anticoagulant_bleeding`, `gi_bleeding` | Usually not on OTC labels. Set from published evidence and cite it |
| `maoi` | MAOI antidepressants | medication | `serotonergic_interactions`, `cardiovascular_bp` | Dextromethorphan and decongestants: "Do not use if you are now taking a prescription MAOI" (hard stop) |
| `ssri_snri` | SSRI or SNRI antidepressants | medication | `serotonergic_interactions` | Not on most OTC labels. Set from published evidence on serotonin syndrome and cite it |
| `sedatives` | Sedatives or sleep medicines | medication | `sedation_falls`, `duplicate_dosing` | Antihistamines: "alcohol, sedatives, and tranquilizers may increase drowsiness" |
| `diuretics` | Water pills (diuretics) | medication | `kidney` | NSAIDs: "Ask a doctor before use if you are taking a diuretic" |
| `blood_pressure_medications` | Blood pressure medicines | medication | `kidney`, `cardiovascular_bp` | NSAIDs can reduce the effect of some blood pressure medicines; confirm label wording |
| `corticosteroids` | Steroid medicines (e.g. prednisone) | medication | `gi_bleeding` | NSAIDs: "The chance is higher if you take a blood thinning (anticoagulant) or steroid drug" |

## 5. Evidence sources

| Source | What it is | May set severity | Notes |
|---|---|---|---|
| FDA label (Drug Facts) | The product's DailyMed label | Yes, all dimensions | Primary source. Cite set id and section |
| Mandated warning / OTC monograph | FDA-required warning text and rules for a product category | Yes, all dimensions | Catalogue in `pipeline/knowledge/mandated_warnings.yaml` (NOMI-017) |
| STOPP/START | Expert criteria for older adults | Yes, for `adult_65_plus` | Digitized in `pipeline/knowledge/criteria/` (NOMI-018) |
| ACB scale | Anticholinergic burden score 0 to 3 | Yes, for `anticholinergic_cognitive` | ACB 1, 2, 3 map to severity 1, 2, 3 for `adult_65_plus` |
| Published studies | Peer-reviewed studies and meta-analyses | Yes, with a citation to the paper | Needed where labels are silent (`antiplatelets`, `ssri_snri`, `efficacy_evidence`) |
| FAERS signals | FDA adverse event reports, IC/IC025 | No, supporting only | Can justify the higher of two levels; can't set a rating alone (no denominator, reporting bias) |
| Pharmacist review | A licensed pharmacist's judgment | Yes, recorded in the review tool | Must be logged with the reviewer's credentials |

Allowed sources per dimension:

| Dimension | Label | Monograph | STOPP/START | ACB | Studies | FAERS (support only) |
|---|---|---|---|---|---|---|
| `liver` | yes | yes | yes | no | yes | yes |
| `gi_bleeding` | yes | yes | yes | no | yes | yes |
| `cardiovascular_bp` | yes | yes | yes | no | yes | yes |
| `kidney` | yes | yes | yes | no | yes | yes |
| `anticholinergic_cognitive` | yes | no | yes | yes | yes | yes |
| `sedation_falls` | yes | yes | yes | no | yes | yes |
| `serotonergic_interactions` | yes | yes | yes | no | yes | yes |
| `anticoagulant_bleeding` | yes | yes | yes | no | yes | yes |
| `pediatric` | yes | yes | no | no | yes | yes |
| `rebound_overuse` | yes | yes | no | no | yes | yes |
| `pregnancy_lactation` | yes | yes | no | no | yes | yes |
| `duplicate_dosing` | yes | yes | no | no | no | no |
| `excipients` | yes | yes | no | no | yes | no |
| `local_skin` | yes | yes | no | no | yes | yes |
| `efficacy_evidence` | no | yes | no | no | yes | no |

## Review checklist

Before this doc is approved:

- [ ] Each example label wording above checked against a real DailyMed label, with the set id noted in the PR
- [ ] Current FDA status of oral phenylephrine confirmed
- [ ] A teammate who hasn't seen this doc rates naproxen for `adult_65_plus` on `gi_bleeding`, `kidney` and `cardiovascular_bp` using only this doc and the Aleve label; ratings within 1 level of ours
- [ ] Approved by both cofounders and two Data Analysis members

## Change log

Ids are never renamed. To retire one, mark it deprecated here, stop using it in new data, and remove
it from the schema only in a major schema version.

| Date | Change |
|---|---|
| 2026-10-18 | First draft: 15 dimensions, 4-level severity scale, 8 personas, 20 modifiers, evidence rules |
