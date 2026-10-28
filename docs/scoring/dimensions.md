# Define Risk Dimensions, Severity and Personas

## 1. Risk Dimensions

Every active ingredient in Nomi is scored across 15 standard risk dimensions. Each dimension has a stable, canonical ID matching `packages/schema/schemas/common.schema.json`, a consumer-facing display name, and documented clinical criteria.

### 1. `liver`

- **Display Name:** Liver Damage & Acute Toxicity
- **Active Ingredient & Product:** Acetaminophen (Tylenol Regular & Extra Strength)
- **Clinical Scope:** Intrinsic hepatotoxicity, toxic metabolite accumulation (NAPQI via CYP2E1), glutathione depletion, acute liver failure, and toxic synergy with alcohol or other acetaminophen-containing products.
- **Real Label Example:**
  > "Liver warning: This product contains acetaminophen. Severe liver damage may occur if you take: more than 4,000 mg of acetaminophen in 24 hours; with other drugs containing acetaminophen; 3 or more alcoholic drinks every day while using this product." (Tylenol Regular & Extra Strength / Acetaminophen)

### 2. `gi_bleeding`

- **Display Name:** Stomach Bleeding & Ulcers
- **Active Ingredient & Product:** Ibuprofen (Advil / Motrin IB)
- **Clinical Scope:** COX-1 inhibition in gastric mucosa causing reduced protective prostaglandins, gastric ulceration, microvascular erosion, perforation, and acute upper/lower GI hemorrhage.
- **Real Label Example:**
  > "Stomach bleeding warning: This product contains an NSAID, which may cause severe stomach bleeding. The chance is higher if you: are age 60 or older; have had stomach ulcers or bleeding problems; take a blood thinning (anticoagulant) or steroid drug; take other drugs containing prescription or nonprescription NSAIDs; have 3 or more alcoholic drinks every day while using this product; take more or for a longer time than directed." (Advil / Motrin IB / Ibuprofen)

### 3. `cardiovascular_bp`

- **Display Name:** Blood Pressure & Heart Stress
- **Active Ingredient & Product:** Pseudoephedrine HCl (Sudafed Congestion)
- **Clinical Scope:** Peripheral vasoconstriction via alpha-1 adrenergic agonism, positive chronotropic/inotropic cardiac stimulation, elevation of systemic vascular resistance and blood pressure, exacerbation of ischemic heart disease, arrhythmia risk, and NSAID-related fluid retention/hypertension.
- **Real Label Example:**
  > "Ask a doctor before use if you have: heart disease, high blood pressure, thyroid disease, diabetes, trouble urinating due to an enlarged prostate gland." (Sudafed Congestion / Pseudoephedrine HCl)

### 4. `kidney`

- **Display Name:** Kidney Damage & Fluid Retention
- **Active Ingredient & Product:** Naproxen Sodium (Aleve)
- **Clinical Scope:** Inhibition of renal vasodilatory prostaglandins ($PGE_2$, $PGI_2$), decreased renal blood flow and glomerular filtration rate (GFR), sodium and water retention, acute tubular necrosis, and acute interstitial nephritis.
- **Real Label Example:**
  > "Ask a doctor before use if: you have high blood pressure, heart disease, liver cirrhosis, kidney disease, asthma; you are taking a diuretic... Stop use and ask a doctor if: you have symptoms of kidney problems (such as urinating less, blood in urine, sudden swelling in legs or feet)." (Aleve / Naproxen Sodium)

### 5. `anticholinergic_cognitive`

- **Display Name:** Memory, Confusion & Anticholinergic Burden
- **Active Ingredient & Product:** Doxylamine Succinate (Unisom SleepTabs)
- **Clinical Scope:** Central and peripheral muscarinic receptor antagonism ($M_1$–$M_5$), blood-brain barrier penetration leading to acute delirium, cognitive decline, memory impairment, exacerbation of dementia, urinary retention, and increased intraocular pressure in closed-angle glaucoma.
- **Real Label Example:**
  > "Ask a doctor before use if you have: glaucoma; trouble urinating due to an enlarged prostate gland; a breathing problem such as emphysema or chronic bronchitis." (Unisom SleepTabs / Doxylamine Succinate)

### 6. `sedation_falls`

- **Display Name:** Drowsiness & Fall Risk
- **Active Ingredient & Product:** Diphenhydramine HCl (Benadryl Allergy / ZzzQuil)
- **Clinical Scope:** Central histamine $H_1$ receptor blockade producing sedation, impaired psychomotor performance, slowed reaction time, postural instability, ataxia, and heightened fall and fracture risks in older adults.
- **Real Label Example:**
  > "When using this product: marked drowsiness may occur; avoid alcoholic drinks; alcohol, sedatives, and tranquilizers may increase drowsiness; be careful when driving a motor vehicle or operating machinery." (Benadryl Allergy / Diphenhydramine HCl)

### 7. `serotonergic_interactions`

- **Display Name:** Serotonin Syndrome & MAOI Interactions
- **Active Ingredient & Product:** Dextromethorphan HBr (Robitussin / Delsym)
- **Clinical Scope:** Serotonin reuptake inhibition combined with prescription serotonergic agents (MAOIs, SSRIs, SNRIs, triptans), potentially triggering central and peripheral serotonin toxicity (hyperreflexia, clonus, autonomic instability, hyperthermia).
- **Real Label Example:**
  > "Do not use if you are now taking a prescription monoamine oxidase inhibitor (MAOI) (certain drugs for depression, psychiatric or emotional conditions, or Parkinson's disease), or for 2 weeks after stopping the MAOI drug. If you do not know if your prescription drug contains an MAOI, ask a doctor or pharmacist before taking this product." (Robitussin / Delsym / Dextromethorphan HBr)

### 8. `anticoagulant_bleeding`

- **Display Name:** Blood Thinner Interactions & Bleeding Risk
- **Active Ingredient & Product:** Aspirin (Bayer Aspirin 325 mg)
- **Clinical Scope:** Irreversible (aspirin) or reversible (other NSAIDs) platelet COX-1 inhibition and thromboxane $A_2$ suppression, interfering with hemostatic plug formation and potentiating bleeding when co-administered with anticoagulants (warfarin, DOACs) or antiplatelet therapies.
- **Real Label Example:**
  > "Ask a doctor before use if you are taking a prescription drug for: anticoagulation (blood thinning); diabetes, gout, or arthritis... Stop use and ask a doctor if: you feel faint, vomit blood, or have bloody or black stools." (Bayer Aspirin / Aspirin)

### 9. `pediatric`

- **Display Name:** Children & Teenager Specific Risks
- **Active Ingredient & Product:** Aspirin / Salicylates (Bayer Low Dose Aspirin)
- **Clinical Scope:** Age-specific contraindications and adverse reactions in pediatric populations, including Reye's syndrome from salicylates during viral illness, paradoxical CNS excitation from antihistamines, and respiratory suppression.
- **Real Label Example:**
  > "Reye's syndrome: Children and teenagers who have or are recovering from chicken pox or flu-like symptoms should not use this product. When using this product, if changes in behavior with nausea and vomiting occur, consult a doctor because these symptoms could be an early sign of Reye's syndrome, a rare but serious illness." (Bayer Low Dose Aspirin / Aspirin)

### 10. `rebound_overuse`

- **Display Name:** Rebound Symptoms & Dependence
- **Active Ingredient & Product:** Oxymetazoline HCl (Afrin 12 Hour Nasal Spray)
- **Clinical Scope:** Downregulation and desensitization of target receptors with continued administration, leading to rebound phenomenon upon drug clearance (e.g. rhinitis medicamentosa from topical vasoconstrictors, medication-overuse headaches from analgesics).
- **Real Label Example:**
  > "When using this product: do not use more than directed; do not use for more than 3 days. Use only as directed. Frequent or prolonged use may cause nasal congestion to recur or worsen." (Afrin 12 Hour Nasal Spray / Oxymetazoline HCl)

### 11. `pregnancy_lactation`

- **Display Name:** Pregnancy & Breastfeeding Warning
- **Active Ingredient & Product:** Ibuprofen (Motrin IB / Advil)
- **Clinical Scope:** Fetal harm, teratogenicity, adverse gestational outcomes (e.g. premature closure of the fetal ductus arteriosus, oligohydramnios and fetal renal dysfunction after 20 weeks gestation), and transfer into maternal milk with infant exposure.
- **Real Label Example:**
  > "If pregnant or breast-feeding, ask a health professional before use. It is especially important not to use ibuprofen at 20 weeks or later in pregnancy unless definitely directed to do so by a doctor because it may cause problems in the unborn child or complications during delivery." (Motrin IB / Advil / Ibuprofen)

### 12. `duplicate_dosing`

- **Display Name:** Accidental Duplicate Dosing & Multi-Drug Overlap
- **Active Ingredient & Product:** Acetaminophen combination products (Vicks DayQuil / NyQuil Severe)
- **Clinical Scope:** Risk of toxicity arising from multi-ingredient OTC combination preparations (e.g. cough, cold, flu, sleep formulations) where users unknowingly combine identical active ingredients (such as acetaminophen, first-generation antihistamines, or decongestants) across multiple products.
- **Real Label Example:**
  > "Do not use with any other drug containing acetaminophen (prescription or nonprescription). If you are not sure whether a drug contains acetaminophen, ask a doctor or pharmacist." (Vicks DayQuil / NyQuil Cold & Flu / Acetaminophen)

### 13. `excipients`

- **Display Name:** Inactive Ingredients & Hidden Additives
- **Active Ingredient & Product:** Formulations with Aspartame / Sodium / Alcohol (Children's Dimetapp / Alka-Seltzer)
- **Clinical Scope:** Inactive ingredient sensitivities and physiological hazards, including phenylalanine exposure in individuals with phenylketonuria (PKU), significant sodium load in hypertensive/cardiorenal patients, sugar content in diabetics, or alcohol/dye sensitivities.
- **Real Label Example:**
  > "Phenylketonurics: Contains phenylalanine 4.2 mg per tablet." (Children's Dimetapp Chewables / Aspartame)  
  > _(Also: "Ask a doctor before use if you have a sodium-restricted diet. Each tablet contains 568 mg sodium." — Alka-Seltzer Original)_

### 14. `local_skin`

- **Display Name:** Skin Irritation & Chemical Burns
- **Active Ingredient & Product:** Menthol / Methyl Salicylate / Capsaicin (Icy Hot / Bengay / Capsaicin)
- **Clinical Scope:** Severe cutaneous reactions from topical formulations, including contact dermatitis, erythema, localized chemical burns, blistering, and enhanced systemic absorption when applied to broken skin or occluded with heat pads.
- **Real Label Example:**
  > "When using this product: use only as directed; do not bandage tightly or apply local heat (such as heating pads) to the area of use; avoid contact with eyes and mucous membranes; do not apply to wounds or damaged, broken or irritated skin... Stop use and ask a doctor if: condition worsens; redness is present; irritation develops; symptoms persist for more than 7 days." (Icy Hot Medicated Patch / Bengay / Methyl Salicylate & Menthol)

### 15. `efficacy_evidence`

- **Display Name:** Questionable Clinical Efficacy vs. Risk
- **Active Ingredient & Product:** Oral Phenylephrine HCl (Sudafed PE / DayQuil Cold & Flu)
- **Clinical Scope:** Active ingredients where current regulatory, pharmacokinetic, or clinical trial consensus shows a lack of proven efficacy at OTC doses, subjecting consumers to systemic risks and delayed effective therapy with no therapeutic benefit.
- **Real Label Example:**
  > "Uses: temporarily relieves nasal congestion due to the common cold, hay fever or other upper respiratory allergies." (Sudafed PE / Oral Phenylephrine HCl)  
  > _(Clinical/Regulatory evidence: FDA Nonprescription Drugs Advisory Committee [NDAC] unanimous 2023 finding that oral phenylephrine is ineffective at standard OTC monograph dosages due to >99% first-pass gut/liver degradation)._

## 2. Severity Scale

The severity scale rates the intrinsic hazard of an active ingredient on a given risk dimension for a specific persona or modifier profile. It uses a 4-tier integer scale (`0` to `3`), where non-zero ratings require verifiable citations (`fda_label`, `otc_monograph`, `stopp_start`, `acb`, `publication`, or `pharmacist_review`). FAERS never sets a severity; see the FAERS rules in section 5.

```
Score 0 (Negligible / None)  ──>  0 points deducted     ──>  Green (>=75)
Score 1 (Low / Mild)         ──>  Minor deduction       ──>  Green / Borderline
Score 2 (Moderate / Caution) ──>  Substantial deduction ──>  Yellow (50-74)
Score 3 (High / Severe)      ──>  Critical deduction    ──>  Red (<50) / Hard Stop
```

---

### Score 0: Negligible / No Documented Risk

The active ingredient has no established biochemical mechanism, receptor affinity, or metabolic pathway capable of triggering this pathology at therapeutic OTC dosages.

#### 1. Clinical & Pharmacological Criteria

- No target receptor affinity or relevant enzyme inhibition (e.g. non-sedating second-generation antihistamines lack significant central $H_1$ receptor occupancy; non-NSAIDs lack COX-1 inhibition).
- Normal therapeutic doses do not challenge hepatic, renal, or cardiovascular reserve in the specified persona.
- **Anticholinergic Burden:** $\text{ACB} = 0$.
- **Geriatric Consensus:** Not listed in STOPP/START for this physiological category.

#### 2. FDA Label Indicators

- Complete absence of warnings, precautions, drug interactions, or "Ask a doctor before use" advisories for this physiological system.

#### 3. Concrete Examples

| Dimension           | Drug & Generic                         | Justification                                                                                                                            |
| ------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `gi_bleeding`       | **Tylenol** (Acetaminophen)            | Does not inhibit peripheral COX-1; does not erode gastric mucosal barrier or impair platelet thromboxane production.                     |
| `sedation_falls`    | **Claritin** (Loratadine)              | Peripheral selective $H_1$ antagonist with minimal blood-brain barrier permeability; no psychomotor impairment at recommended OTC doses. |
| `cardiovascular_bp` | **MiraLAX** (Polyethylene Glycol 3350) | Non-absorbable osmotic laxative acting purely intraluminally; zero systemic adrenergic or hemodynamic activity.                          |
| `kidney`            | **Mucinex** (Guaifenesin)              | Excreted without renal vasoconstriction or nephrotoxic tubular injury; no impairment of renal prostaglandin synthesis.                   |

---

### Score 1: Low / Mild / Incidental Risk

The active ingredient is associated with minor, self-limiting, or low-incidence adverse effects that do not result in organ damage, functional disability, or medical intervention in the target persona.

#### 1. Clinical & Pharmacological Criteria

- Minor or low-affinity receptor binding (e.g. slight cross-reactivity with peripheral muscarinic receptors or low-level blood-brain barrier penetration).
- Physiological changes are transient, reversible upon drug clearance, and well-tolerated by individuals without severe underlying organ failure.
- **Anticholinergic Burden:** $\text{ACB} = 1$ (weak anticholinergic activity).
- **Hemodynamics:** Transient blood pressure shifts $< 5\text{ mmHg}$ systolic without end-organ compromise.

#### 2. FDA Label Indicators

- Appears under **"When using this product"** as a common, non-critical advisory:
  - _"Drowsiness may occur."_
  - _"Mild stomach upset may occur."_
  - _"A transient burning or stinging sensation may occur."_
- Does **not** require an upfront "Ask a doctor before use" for healthy baseline adults.

#### 3. Concrete Examples

| Dimension           | Drug & Generic                            | Justification                                                                                                                                      |
| ------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sedation_falls`    | **Zyrtec** (Cetirizine HCl)               | 2nd-gen antihistamine with slight blood-brain barrier penetration; somnolence reported in ~10–14% of patients (vs. ~6% placebo); $\text{ACB} = 1$. |
| `local_skin`        | **Capsaicin 0.025% Cream**                | Transient substance P release produces local erythema and burning sensation upon initial application; self-resolving with continued use.           |
| `cardiovascular_bp` | **Afrin Nasal Spray** (Oxymetazoline HCl) | Local vasoconstriction with minimal systemic absorption if used strictly as directed ($\le 3$ days), causing negligible systemic pressor response. |
| `gi_bleeding`       | **Pepcid AC** (Famotidine)                | Rare, mild GI intolerance (diarrhea/constipation); no mucosal erosion or hemorrhagic risk.                                                         |

---

### Score 2: Moderate / Clinically Significant Precaution

The active ingredient exerts direct physiological stress, reduces organ reserve, or produces measurable functional impairment. Requires screening for pre-existing risk factors, co-medications, or strict dosage/duration limits.

#### 1. Clinical & Pharmacological Criteria

- Significant central or peripheral receptor occupancy (e.g. marked $H_1$ and muscarinic blockade, significant alpha-adrenergic vasoconstriction, or systemic COX-1 inhibition).
- Produces clinically meaningful functional degradation: psychomotor slowing, reaction time deficits, impaired renal perfusion under hypovolemic conditions, or blunting of antihypertensive therapy.
- **Anticholinergic Burden:** $\text{ACB} = 2$.
- **Geriatric Consensus:** Listed in STOPP/START with specific clinical caveats (e.g. short-term use only, avoid in fall-prone individuals).

#### 2. FDA Label Indicators

- Explicit **"Ask a doctor before use if you have [Condition]"** warnings:
  - _"Ask a doctor before use if you have high blood pressure, heart disease, thyroid disease, diabetes, or glaucoma."_
  - _"Ask a doctor before use if you have kidney disease or are taking a diuretic."_
- Explicit **"When using this product"** functional impairments:
  - _"Marked drowsiness may occur; be careful when driving a motor vehicle or operating machinery."_
- Explicit **Duration limits**:
  - _"Do not use for more than 3 days / 7 days."_

#### 3. Concrete Examples

| Dimension                   | Drug & Generic                                      | Justification                                                                                                                                                                                                   |
| --------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `cardiovascular_bp`         | **Sudafed** (Pseudoephedrine HCl) in `adult_18_64`  | Systemic sympathomimetic stimulates vascular $\alpha_1$ and cardiac $\beta_1$ receptors; raises SBP by $3–5\text{ mmHg}$ and heart rate by $3–6\text{ bpm}$ in normotensive adults; higher in unmanaged states. |
| `kidney`                    | **Advil** (Ibuprofen) in `adult_18_64`              | Reversible inhibition of renal prostaglandins ($PGE_2$/$PGI_2$); decreases compensatory renal blood flow; induces subclinical fluid and sodium retention.                                                       |
| `sedation_falls`            | **Benadryl** (Diphenhydramine HCl) in `adult_18_64` | High lipid solubility and central $H_1$ receptor occupancy ($>70\%$); causes objective psychomotor slowing equivalent to blood alcohol concentration of $0.05–0.08\%$.                                          |
| `rebound_overuse`           | **Afrin** (Oxymetazoline HCl)                       | Continued use $>72$ hours induces downregulation of $\alpha_2$ adrenergic receptors, leading to refractory rebound mucosal edema (rhinitis medicamentosa).                                                      |
| `anticholinergic_cognitive` | **Unisom** (Doxylamine Succinate) in `adult_18_64`  | Potent central muscarinic blockade ($\text{ACB} = 3$); causes dry mouth, blurred vision, pupillary dilation, and mild next-day grogginess/cognitive clouding.                                                   |

---

### Score 3: High / Severe Hazard or Contraindication

The active ingredient poses catastrophic risks: irreversible organ failure, severe hemorrhage, life-threatening toxicity, fetal injury/death, or severe neuropsychiatric collapse. Demands strict contraindication or absolute avoidance.

#### 1. Clinical & Pharmacological Criteria

- Toxic metabolite accumulation overwhelming protective reserves (e.g. acetaminophen NAPQI saturation depleting hepatic glutathione; extensive centrilobular necrosis).
- Direct disruption of essential survival physiology (complete suppression of gastric protective prostaglandins with simultaneous platelet inactivation; irreversible ductus arteriosus closure in utero).
- **Anticholinergic Burden:** $\text{ACB} = 3$ in geriatric populations (`adult_65_plus`).
- **Geriatric Consensus:** A STOPP criterion that applies without caveats (e.g. systemic NSAIDs in heart failure / stage 4–5 CKD; first-gen antihistamines in cognitive impairment/dementia).

#### 2. FDA Label Indicators

- **Required Organ-Specific Warnings** (Drug Facts "Warnings" section):
  - _"Liver warning: This product contains acetaminophen. Severe liver damage may occur..."_
  - _"Stomach bleeding warning: This product contains an NSAID, which may cause severe stomach bleeding..."_
  - _"Reye's syndrome: Children and teenagers who have or are recovering from chicken pox or flu-like symptoms should not use this product."_
- **Explicit Contraindications**:
  - _"Do not use if..."_
  - _"Do not use with any other drug containing [Ingredient]."_
  - _"Do not use at 20 weeks or later in pregnancy."_

#### 3. Concrete Examples

| Dimension                   | Drug & Generic                             | Persona / Condition              | Justification                                                                                                                                                           |
| --------------------------- | ------------------------------------------ | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `liver`                     | **Tylenol Extra Strength** (Acetaminophen) | Baseline / Heavy Alcohol Use     | Exceeding $4,000\text{ mg/day}$ or combining with $\ge 3$ alcoholic drinks depletes glutathione, causing hepatocellular necrosis, fulminant hepatic failure, and death. |
| `pediatric`                 | **Bayer Aspirin** (Aspirin)                | `child_6_11` / `teen_12_17`      | Mitochondrial toxicity in viral illnesses triggers Reye's syndrome: acute hepatic encephalopathy, cerebral edema, $>20\%$ mortality.                                    |
| `gi_bleeding`               | **Aleve** (Naproxen Sodium)                | `adult_65_plus` or Ulcer History | Synergistic ulcerogenic risk in elderly gastric mucosa; causes unheralded acute upper gastrointestinal hemorrhage, perforation, and shock.                              |
| `anticholinergic_cognitive` | **Benadryl** (Diphenhydramine)             | `adult_65_plus`                  | Crosses impaired blood-brain barrier; precipitates acute delirium, accelerates cognitive decline in dementia, causes acute urinary retention; STOPP D14 / ACB 3.          |
| `pregnancy_lactation`       | **Advil** (Ibuprofen)                      | `pregnant` ($\ge 20$ weeks)      | Inhibits fetal renal prostaglandins causing oligohydramnios; premature constriction of the fetal ductus arteriosus causing pulmonary hypertension.                      |
| `serotonergic_interactions` | **Delsym** (Dextromethorphan)              | Concurrent `maoi`                | Inhibits serotonin reuptake; combined with MAO inhibition triggers fatal hyperpyrexia, autonomic instability, and seizures.                                             |

---

### Comparison & Scoring Rubric Summary Table

| Metric                               | Score 0 (Negligible) | Score 1 (Low)                                     | Score 2 (Moderate)                          | Score 3 (High)                                          |
| ------------------------------------ | -------------------- | ------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------- |
| **Severity Meaning**                 | No documented risk   | Mild / incidental / transient                     | Precautionary / organ stress                | Severe / life-threatening hazard                        |
| **Typical FDA Label Wording**        | Absent               | _"When using: drowsiness / mild upset may occur"_ | _"Ask a doctor before use if you have [X]"_ | _"Liver warning"_, _"Stomach bleeding"_, _"Do not use"_ |
| **ACB Score**                        | 0                    | 1                                                 | 2 (or 3 in younger adults)                  | 3 in older adults (`adult_65_plus`)                     |
| **STOPP Category**                   | Not listed           | Not listed / Informational                        | "Use with caution"                          | "Avoid"                                                 |
| **Point Deduction**                  | 0 points             | 5 – 10 points                                     | 15 – 25 points                              | 35 – 50+ points (or Hard Stop)                          |
| **Default Product Tier**             | Green ($\ge 75$)     | Green ($\ge 75$)                                  | Yellow ($50–74$)                            | Red ($< 50$)                                            |


## 3. The 8 Target Personas

Nomi defines 8 canonical personas representing distinct age bands, pharmacokinetic profiles, and physiological stages. Every ingredient has a baseline rating (`0` to `3`) for each persona.

```
       Adult Personas                     Pediatric Personas             Reproductive Personas
  ┌───────────────────────┐          ┌───────────────────────────┐      ┌─────────────────────────┐
  │  adult_18_64 (Default)│          │  teen_12_17  (12-17 yrs)  │      │  pregnant               │
  │  adult_65_plus (Ger.) │          │  child_6_11  (6-11 yrs)   │      │  breastfeeding          │
  └───────────────────────┘          │  child_2_5   (2-5 yrs)    │      └─────────────────────────┘
                                     │  under_2     (< 24 mos)   │
                                     └───────────────────────────┘
```

---

### 1. `adult_18_64` (Standard Adult)
- **Age / Group:** 18 to 64 years old.
- **Physiology:** Fully mature hepatic cytochrome P450 enzymes and phase II conjugation; normal glomerular filtration rate ($\text{GFR} \ge 90\text{ mL/min/1.73m}^2$); intact blood-brain barrier; resilient gastric mucosal protection.
- **Scoring Function:** The default baseline persona. Risks reflect standard OTC monograph adult dosages.
- **Vulnerabilities:** Susceptible to dose-dependent hepatotoxicity (acetaminophen $>4\text{g/day}$), gastrointestinal toxicity with unmanaged NSAID use, and rebound dependence.

---

### 2. `adult_65_plus` (Older Adult / Geriatric)
- **Age / Group:** 65 years and older.
- **Physiology:** Age-related physiological decline: progressive reduction in renal clearance (GFR declining $\sim 1\text{ mL/min}$ per year after age 40); decreased hepatic blood flow; increased blood-brain barrier permeability; lower gastric prostaglandin synthesis; loss of total body water (higher volume of distribution for lipophilic drugs).
- **Consensus Standards:** Guided by the **STOPP/START** criteria (v3) and the **ACB** scale.
- **High-Risk Dimensions:**
  - `anticholinergic_cognitive`: High risk of acute delirium, accelerated cognitive decline, and urinary retention ($\text{ACB} \ge 2$ automatically scored 3 / Avoid).
  - `sedation_falls`: Heightened ataxia, motor slowing, orthostatic hypotension, and hip fracture risk.
  - `gi_bleeding` & `kidney`: Heightened risk of severe NSAID-induced peptic perforation and acute kidney injury.

---

### 3. `teen_12_17` (Adolescent)
- **Age / Group:** 12 to 17 years old.
- **Physiology:** Adult-approaching metabolic capacity and body surface area, but distinct neuropsychiatric vulnerability and vulnerability to specific viral-associated metabolic syndromes.
- **High-Risk Dimensions:**
  - `pediatric`: **Aspirin / Salicylate Contraindication** — exposure during viral illness (influenza, varicella) triggers **Reye’s syndrome** (hepatic failure + cerebral edema).
  - `rebound_overuse`: Heightened risk of misuse/abuse with dissociative cough suppressants (dextromethorphan recreational megadosing / "robotripping").

---

### 4. `child_6_11` (School-Age Child)
- **Age / Group:** 6 to 11 years old.
- **Physiology:** Active growth; body weight ranges $20–45\text{ kg}$; weight-based dosing is required; paradoxical excitation response to sedatives is common.
- **High-Risk Dimensions:**
  - `pediatric`: Absolute contraindication for salicylates; strict maximum daily dosages for acetaminophen ($75\text{ mg/kg/day}$ up to adult cap).
  - `sedation_falls` & `anticholinergic_cognitive`: Paradoxical excitation, agitation, insomnia, and tachycardia frequently occur with first-generation $H_1$ antihistamines.

---

### 5. `child_2_5` (Young Child / Toddler)
- **Age / Group:** 24 months to 5 years (under 6 years).
- **Physiology:** Rapidly changing hepatic enzymatic capacity; immature renal tubular secretion; highly sensitive airway reflex arc.
- **High-Risk Dimensions:**
  - `pediatric`: FDA Public Health Advisory warns against OTC cough and cold medications (decongestants, antihistamines, antitussives) due to life-threatening arrhythmia, seizure, and accidental overdose risk.
  - `duplicate_dosing`: High risk of caregiver administration errors combining multiple pediatric suspension formulas.

---

### 6. `under_2` (Infant / Neonate)
- **Age / Group:** 0 to 23 months.
- **Physiology:** Immature renal filtration and hepatic glucuronidation (e.g. UGT1A6/UGT1A9 deficiency in neonates); underdeveloped blood-brain barrier; highly variable absorption kinetics.
- **High-Risk Dimensions:**
  - **Universal Hard Stop:** OTC self-selection is contraindicated. All systemic OTC cough, cold, fever, and pain products require direct pediatrician guidance.
  - `pediatric`: Severe toxicity, respiratory depression, metabolic acidosis, and infant death risks from systemic sympathomimetics, antihistamines, or salicylates.

---

### 7. `pregnant` (Pregnancy)
- **Age / Group:** Pregnant individuals (all trimesters).
- **Physiology:** Expanded intravascular volume; altered plasma protein binding; transplacental drug transfer; fetal organogenesis in Trimester 1; fetal cardiovascular and renal development in Trimesters 2 and 3.
- **High-Risk Dimensions:**
  - `pregnancy_lactation`: 
    - **NSAIDs $\ge 20$ Weeks:** FDA-required label warning (2020) about the risk of premature constriction of the fetal ductus arteriosus causing neonatal pulmonary hypertension; fetal renal impairment causing **oligohydramnios** (low amniotic fluid).
    - **Decongestants (Oral Pseudoephedrine/Phenylephrine):** Risk of uterine artery vasoconstriction and fetal hypoperfusion.

---

### 8. `breastfeeding` (Lactating Parent)
- **Age / Group:** Actively breastfeeding or expressing milk.
- **Physiology:** Drug diffusion across the blood-milk barrier dependent on lipid solubility, molecular weight, protein binding, and milk/plasma ratio ($M/P$); immature clearance in the nursing infant.
- **High-Risk Dimensions:**
  - `pregnancy_lactation`: Sedating antihistamines (diphenhydramine, doxylamine) cause infant sedation, poor feeding, respiratory depression, and maternal prolactin/milk supply suppression.
  - `cardiovascular_bp`: Decongestants reduce serum prolactin, significantly suppressing lactation.


## 4. Modifiers (Conditions & Concurrent Medications)

Modifiers represent individual risk factors configured in a user's local phone profile. In the additive scoring model (`docs/system-design.md`), a modifier adds to the baseline severity:

$$\text{severity}_{\text{effective}} = \min\big(3, \;\text{severity}_{\text{baseline}} + \Delta\text{severity}\big)$$

If an interaction represents an absolute medical contraindication, the modifier triggers a **Hard Stop** (overriding arithmetic to lock the score in the Red tier, $<50$).

---

### Category A: Pre-existing Health Conditions (`condition`)

| # | Stable ID | Display Name | Affected Dimensions | Baseline Mechanism & Severity Change |
|---|---|---|---|---|
| 1 | `hypertension` | High Blood Pressure | `cardiovascular_bp`, `kidney` | Sympathomimetics (pseudoephedrine) stimulate $\alpha_1$ receptors, raising systemic vascular resistance (+2 severity); NSAIDs blunt endogenous vasodilatory prostaglandins, counteracting BP control (+1 severity). |
| 2 | `heart_disease` | Cardiovascular / Ischemic Heart Disease | `cardiovascular_bp` | Adrenergic agonists increase myocardial oxygen demand and induce arrhythmias (+2 severity); NSAIDs increase sodium retention and exacerbate heart failure (+2 severity / STOPP B19). |
| 3 | `kidney_disease` | Chronic Kidney Disease (CKD) | `kidney`, `cardiovascular_bp` | Impaired renal clearance. NSAID inhibition of $PGE_2$/$PGI_2$ triggers hemodynamic acute renal failure (+2 severity or Hard Stop if severe CKD). |
| 4 | `liver_disease` | Cirrhosis / Chronic Hepatic Impairment | `liver` | Impaired glucuronidation and depleted baseline glutathione stores. Lowers the threshold for acetaminophen hepatotoxicity (+2 severity). |
| 5 | `stomach_ulcer_or_bleeding` | Peptic Ulcer Disease / GI Bleeding | `gi_bleeding` | Systemic COX-1 inhibition destroys gastric mucous bicarbonate barrier. Pre-existing ulcers face high perforation and catastrophic hemorrhage risks (+2 severity / Hard Stop for NSAIDs). |
| 6 | `glaucoma` | Glaucoma (Closed-Angle) | `anticholinergic_cognitive` | Anticholinergic pupillary dilation (mydriasis) blocks aqueous humor outflow via trabecular meshwork, precipitating acute angle-closure glaucoma (+2 severity / Hard Stop). |
| 7 | `enlarged_prostate` | Benign Prostatic Hyperplasia (BPH) | `anticholinergic_cognitive` | Anticholinergic detrusor relaxation combined with $\alpha_1$-mediated bladder neck constriction precipitates acute urinary retention (+2 severity). |
| 8 | `asthma` | Asthma / Reactive Airway Disease | None (hard stop) | Aspirin-Exacerbated Respiratory Disease (AERD): COX-1 inhibition diverts arachidonic acid to leukotrienes, inducing severe bronchospasm in susceptible asthmatics. There is no respiratory dimension, so this is a hard stop on aspirin and NSAIDs driven by the label's allergy alert, not a severity change. |
| 9 | `diabetes` | Diabetes Mellitus | `cardiovascular_bp`, `excipients` | Sympathomimetics stimulate hepatic glycogenolysis; liquid/chewable formulas high in sugars can disrupt glycemic control (+1 severity). |
| 10 | `thyroid_disease` | Hyperthyroidism / Thyroid Disease | `cardiovascular_bp` | Increased beta-adrenergic receptor sensitivity in hyperthyroidism causes marked tachycardia and dysrhythmias with sympathomimetics (+2 severity). |
| 11 | `phenylketonuria` | Phenylketonuria (PKU) | `excipients` | Inability to metabolize phenylalanine. Any formulation containing aspartame excipients triggers toxic hyperphenylalaninemia (**Hard Stop**). |
| 12 | `heavy_alcohol_use` | Chronic Heavy Alcohol Use ($\ge 3$ drinks/day) | `liver`, `gi_bleeding` | Chronically induces CYP2E1 (multiplying toxic NAPQI production from acetaminophen) and causes gastric mucosal erosions with NSAIDs (+2 severity on `liver` & `gi_bleeding`). |

---

### Category B: Concurrent Prescription Medications (`medication_type`)

| # | Stable ID | Display Name | Affected Dimensions | Drug Interaction Mechanism & Severity Impact |
|---|---|---|---|---|
| 1 | `anticoagulants` | Blood Thinners (Warfarin, DOACs: Eliquis, Xarelto) | `anticoagulant_bleeding`, `gi_bleeding` | Synergistic suppression of hemostasis: NSAIDs inhibit platelet COX-1 while anticoagulants inhibit clotting cascade factors, multiplying GI bleed risk $>5\times$ (+2 severity / Red Tier). |
| 2 | `antiplatelets` | Antiplatelet Therapy (Plavix, Brilinta, daily ASA) | `anticoagulant_bleeding`, `gi_bleeding` | Compounding platelet aggregation blockade with nonsteroidal anti-inflammatories increases hemorrhagic stroke and GI bleed risk (+2 severity). |
| 3 | `maoi` | MAO Inhibitors (Nardil, Parnate, Selegiline) | `serotonergic_interactions`, `cardiovascular_bp` | **Universal Hard Stop:** Combined with dextromethorphan causes fatal Serotonin Syndrome (hyperthermia, coma); combined with pseudoephedrine prevents amine breakdown, triggering fatal Hypertensive Crisis. |
| 4 | `ssri_snri` | Antidepressants (Prozac, Zoloft, Lexapro, Cymbalta) | `serotonergic_interactions`, `gi_bleeding` | Combined with dextromethorphan elevates serotonin syndrome risk (+2 severity); combined with NSAIDs depletes platelet serotonin storage, increasing upper GI bleeding risk (+1 severity). |
| 5 | `sedatives` | CNS Depressants (Benzos, Ambien, Opioids, Muscle Relaxants) | `sedation_falls` | Pharmacodynamic synergism: additive GABA-ergic or histaminergic central depression causes profound somnolence, motor ataxia, respiratory depression, and severe fall risk (+2 severity). |
| 6 | `diuretics` | Water Pills (Furosemide, Hydrochlorothiazide) | `kidney`, `cardiovascular_bp` | NSAIDs block prostaglandin-mediated renal vasodilation, blunting diuretic and antihypertensive efficacy; in dehydrated patients, precipitates acute tubular necrosis (+2 severity). |
| 7 | `blood_pressure_medications` | ACEi, ARBs, CCBs, Beta-Blockers | `cardiovascular_bp`, `kidney` | NSAIDs cause fluid retention that attenuates BP control (+1 severity). The combination of ACEi/ARB + Diuretic + NSAID constitutes the **"Triple Whammy"**, acutely dropping GFR and triggering acute renal failure (+2 severity on `kidney`). |
| 8 | `corticosteroids` | Oral Steroids (Prednisone, Dexamethasone) | `gi_bleeding` | Synergistic ulcerogenesis: corticosteroids impair wound healing and prostaglandin synthesis, multiplying NSAID-induced peptic ulcer and perforation risk $>4\times$ (+2 severity). |


## 5. Allowed Evidence Sources per Dimension

Nomi enforces strict evidence grounding: **every non-zero severity rating (`1`, `2`, `3`) and modifier must link to a verified citation** defined in `packages/schema/schemas/common.schema.json`. No score deduction may be generated by black-box algorithms or ungrounded heuristics.

```
                     ┌─────────────────────────────────────────────────────────┐
                     │              Evidence Hierarchy in Nomi                 │
                     └─────────────────────────────────────────────────────────┘
                                                  │
       Level 1: Primary Regulatory Authority     ├──> fda_label (DailyMed SPL)
                                                 └──> otc_monograph (21 CFR / CARES Orders)
                                                  │
       Level 2: Clinical Consensus Guidelines     ├──> stopp_start (Version 3)
                                                 └──> acb (Anticholinergic Cognitive Burden)
                                                  │
       Level 3: Pharmacovigilance (review flag only) ─> faers (openFDA / BCPNN IC025 > 0)
                                                  │
       Level 4: Mechanistic & Clinical Literature ──> publication (PubMed / RCTs)
                                                  │
       Level 5: Clinical Expert Adjudication      └──> pharmacist_review (Peer-reviewed PR)
```

---

### 1. Dataset Roles & Identifiers

| Source Key in Schema | Dataset / Reference | Role in Nomi Pipeline | Required Document Identifier (`document_id`) |
|---|---|---|---|
| `fda_label` | **DailyMed (NLM) / openFDA** | Official Structured Product Labeling (SPL) Drug Facts text; warnings, contraindications, and "Ask a doctor" triggers. | SPL `set_id` (UUID) + LOINC Section Code (e.g. `34071-1` Warnings). |
| `otc_monograph` | **FDA OTC Drug Review / CARES Act** | Federal regulations defining allowed ingredients, dosages, and required warning wording. | Monograph ID or 21 CFR section (e.g. `21 CFR 343`, `M013`). |
| `stopp_start` | **STOPP/START Criteria** | Validated clinical consensus criteria for potentially inappropriate medications in older adults. | Edition + Section/Rule ID (e.g. `STOPP_v3_Section_B4`). |
| `acb` | **Anticholinergic Burden Scale** | Quantitative 0–3 scoring of anticholinergic cognitive impairment and delirium risk. | Scale citation + Version (e.g. `Boustani_2008_ACB_v2`). |
| `faers` | **FDA Adverse Event Reporting System** | Post-marketing surveillance measuring reporting disproportionality ($IC_{025} > 0$) across age bands. | Quarter + MedDRA PT/SMQ code (e.g. `FAERS_2024Q2_PT_10019699`). |
| `publication` | **Peer-Reviewed Journals** | Clinical trials, meta-analyses, pharmacokinetic profiles, and receptor affinities. | DOI (`10.xxxx/...`) or PubMed PMID. |
| `pharmacist_review` | **Nomi Clinical Panel Review** | Adjudicated clinical consensus from licensed faculty/pharmacists for ambiguous cases. | Review Queue Ticket ID + Reviewer Credential ID. |

*(Note: **RxNorm / UMLS** provides the normalization infrastructure mapping brand names and FAERS reported drugs to standard FDA `UNII` codes).*

---

### 2. Allowed Evidence Sources Matrix (All 15 Dimensions)

| Dimension | Primary Allowed Sources | Secondary / Supporting Sources | Expected Document Criteria / Signals |
|---|---|---|---|
| **`liver`** | `fda_label`, `otc_monograph` | `faers`, `publication` | DailyMed "Liver warning"; 21 CFR 201.326; FAERS MedDRA SMQ *Hepatic disorders* ($IC_{025} > 0$); CYP2E1 kinetics. |
| **`gi_bleeding`** | `fda_label`, `otc_monograph` | `stopp_start`, `faers`, `publication` | DailyMed "Stomach bleeding warning"; STOPP Sections F and H (GI, NSAIDs); FAERS SMQ *Gastrointestinal haemorrhage*. |
| **`cardiovascular_bp`** | `fda_label`, `otc_monograph` | `stopp_start`, `faers`, `publication` | DailyMed "Heart disease / high blood pressure"; STOPP Section B (Hypertension/Heart Failure); FAERS PT *Hypertension*, *Tachycardia*. |
| **`kidney`** | `fda_label`, `otc_monograph` | `stopp_start`, `faers`, `publication` | DailyMed "Kidney disease / taking a diuretic"; STOPP Section E (renal); FAERS SMQ *Acute renal failure*. |
| **`anticholinergic_cognitive`** | `acb`, `stopp_start` | `fda_label`, `publication` | ACB score 1–3; STOPP Sections D and M (CNS, antimuscarinic burden); DailyMed "glaucoma / enlarged prostate". |
| **`sedation_falls`** | `fda_label`, `otc_monograph` | `stopp_start`, `publication`, `faers` | DailyMed "marked drowsiness / driving warning"; STOPP Section K (Fall risk); psychomotor driving impairment studies. |
| **`serotonergic_interactions`** | `fda_label`, `otc_monograph` | `publication`, `faers`, `pharmacist_review` | DailyMed "Do not use with MAOI"; Boyer & Shannon diagnostic criteria; FAERS SMQ *Serotonin syndrome*. |
| **`anticoagulant_bleeding`** | `fda_label`, `otc_monograph` | `stopp_start`, `publication`, `faers` | DailyMed "Ask a doctor if taking blood thinning / anticoagulant drug"; STOPP Section C (antiplatelet / anticoagulant). |
| **`pediatric`** | `fda_label`, `otc_monograph` | `publication`, `faers` | DailyMed "Reye's syndrome", "Do not use under age X"; AAP Committee on Drugs policies; Age-stratified FAERS pediatric data. |
| **`rebound_overuse`** | `fda_label`, `otc_monograph` | `publication`, `faers` | DailyMed "Do not use for more than 3 days / rebound congestion"; ICHD-3 Medication-Overuse Headache criteria. |
| **`pregnancy_lactation`** | `fda_label`, `otc_monograph` | `publication`, `faers` | DailyMed "If pregnant or breast-feeding", FDA NSAID $\ge 20$ week warning; Briggs Drugs in Pregnancy; LactMed database. |
| **`duplicate_dosing`** | `fda_label`, `otc_monograph` | `publication`, `faers` | DailyMed "Do not use with any other drug containing [X]"; FDA Acetaminophen Overdose Guidance; FAERS PT *Accidental overdose*. |
| **`excipients`** | `fda_label`, `otc_monograph` | `publication` | DailyMed "Inactive ingredients", "Phenylketonurics: Contains phenylalanine", sodium disclosure (21 CFR 201.64); FDA IID database. |
| **`local_skin`** | `fda_label`, `otc_monograph` | `faers`, `publication` | DailyMed "Do not bandage tightly / apply heat"; FDA Counter-Irritant Burn Alert; FAERS SMQ *Severe cutaneous adverse reactions*. |
| **`efficacy_evidence`** | `publication`, `otc_monograph` | `fda_label`, `pharmacist_review` | FDA Advisory Committee Briefings (e.g. 2023 NDAC Phenylephrine Review); Cochrane Systematic Reviews; Double-blind placebo RCTs. |

---

### 3. FAERS Disproportionality Usage Rules

Because FAERS represents spontaneous reporting without a true population denominator (as emphasized in `docs/nomi-101.md` and `docs/system-design.md`), Nomi applies strict statistical safeguards:

1. **Information Component with Bayesian Shrinkage:**
   $$\text{IC} = \log_2\left(\frac{\text{Observed} + 0.5}{\text{Expected} + 0.5}\right)$$
   A statistical signal is recognized **only if the lower 95% confidence bound ($\text{IC}_{025}$) is strictly greater than 0**.
2. **Stratification:** FAERS counts are stratified by age band (`0-11`, `12-17`, `18-64`, `65+`, matching `signal.schema.json`) and sex to prevent confounding.
3. **Review flag only:** FAERS never sets or changes a severity. Reports are voluntary and have no denominator, so counts are not rates. A signal ($\text{IC}_{025} > 0$) only flags an ingredient and dimension for pharmacist review, and any severity change must then be cited to a label, monograph, criteria list, or publication.


