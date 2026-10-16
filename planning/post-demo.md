# Post-demo epics

Not sprint tickets yet. At the Nov 20 planning session, split each epic into tickets that one person
can finish in one week, then move them into `backlog.md`.

| Epic | Team | Why |
|---|---|---|
| **Personalized risk model v1 (evidence synthesis).** Per dimension: baseline risk x relative-risk modifiers (age, sex, conditions, concurrent meds, dose, duration). Priors from published effect sizes, updated with stratified FAERS signals, calibrated to pharmacist judgments. Exported as the same term tables, so the app doesn't change. | data | Replaces rubric v0 weights with learned, evidence-based ones |
| **Evidence library of published effect sizes.** Ingredient/class x outcome x modifier to RR/OR with 95% CI and citation; LLM-assisted extraction from meta-analysis abstracts, every row human-verified. | data | Priors for the personalized model |
| **All of Us feasibility.** GT access to the Researcher Workbench, data use terms, one scoped study with a faculty partner (e.g. NSAIDs to acute kidney injury by age, CKD, BP meds). | data | Only route to learning personal risk from data with denominators |
| **Signal validation on a reference set.** OMOP / EU-ADR known drug and event pairs; AUC of IC025 vs raw ROR. | data | Headline ML result for the evidence layer |
| **Extraction gold set.** Annotation guideline, 300-label stratified sample, pharmacy-student annotators. | data + cofounders | Measures extraction accuracy properly |
| **Pharmacist review web app.** Next.js + Supabase auth; review queues, pairwise "which is riskier for this profile?" mode, immutable audit log. | platform + viz | Makes pharmacist time count; trains the personalized model |
| **Scheduled pipeline.** GitHub Actions: weekly DailyMed/NDC, quarterly FAERS; release gate with diff report and review queue. | platform | Keeps scores current without manual runs |
| **Dataset updates in the app.** Background download, hash check, atomic swap. | viz | Ship new scores without an app release |
| **Feedback and not-found reports.** Supabase tables with RLS, label-photo upload, no profile data. | platform + viz | Coverage gaps and disputes flow to review |
| **Medicine Cabinet.** On-device cabinet; duplicate-ingredient and interaction warnings from shipped tables. | viz + data | Premium feature; polypharmacy users |
| **Privacy policy, disclaimer, data inventory.** Law clinic review. | cofounders | Required before external testers |
| **External beta.** Apple/Google developer accounts, TestFlight and Play testing, first 50 testers. | platform + cofounders | First real users |
