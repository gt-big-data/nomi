# Nomi 101: read this before your first ticket

This page gives you enough context to pick up any Nomi ticket. It takes about 10 minutes to read.

## What Nomi is

Nomi is a phone app for over-the-counter (OTC) medicines, the ones you can buy without a
prescription: Tylenol, Advil, Aleve, Benadryl, NyQuil, Pepto-Bismol, Claritin and thousands more.

You point the camera at the barcode on the box. In under a second Nomi shows:

1. **A safety score from 0 to 100** for the person who will take it. The same box can score
   differently for a 30-year-old and a 75-year-old, or for someone with high blood pressure.
2. **Why it got that score**, broken into specific risks (for example "stomach bleeding" or
   "memory and thinking"), each with the source it came from.
3. **A safer option** used for the same purpose, or "ask your pharmacist" if there isn't one.

Think of it as Yuka (the food and cosmetics scanner) for medicine.

## The problem it solves

Important safety information exists but isn't on the box in a usable form. Example: diphenhydramine,
the active ingredient in Benadryl and most "PM" sleep aids, is strongly anticholinergic. Long-term
use in older adults has been linked to a higher risk of dementia. That's in medical journals, not on
the package. Nomi puts this kind of information in front of people at the moment they're choosing.

## How Nomi works, end to end

```
 Barcode on the box
        |
        v
 1. IDENTIFY   barcode -> NDC -> FDA label -> ingredients and strengths
        |
        v
 2. EXTRACT    read the label's Drug Facts panel: uses, warnings, age limits, max dose
        |
        v
 3. RATE       give each ingredient a severity on ~15 risk dimensions, per type of person,
               using FDA-required warnings, published expert criteria and FAERS reports
        |
        v
 4. SCORE      a transparent rubric turns ratings into points; exported as lookup tables
        |
        v
 5. SHIP       everything is packed into one SQLite file that ships inside the app
        |
        v
 6. ON PHONE   the app looks up the product and adds up the points for the user's profile
```

Steps 1 to 5 happen in our **pipeline** (Python, runs on our machines). Step 6 happens in the
**app** (React Native, runs on the user's phone).

## Two rules that shape everything

1. **Health data never leaves the phone.** The user's age, conditions and medications are stored
   only on their device. That's why scoring runs on the phone and why the app never sends profile
   data anywhere, including analytics tools. (Details: `docs/adr/0002-privacy.md`.)
2. **Every number must be explainable and cited.** No black-box scores. Every point taken off traces
   to a source such as an FDA label section or a published criterion. LLMs are only used offline to
   help read labels, and their output is checked; they never produce scores.

## Glossary

| Term | Meaning |
|---|---|
| **OTC** | Over-the-counter: medicine sold without a prescription. |
| **Active ingredient** | The chemical that does the work (acetaminophen in Tylenol). A product can have several. |
| **Inactive ingredient** | Everything else in the product: dyes, fillers, flavors, alcohol. Matters for allergies. |
| **NDC** | National Drug Code. FDA's unique ID for a drug product and package. 10 digits on the box (e.g. `50580-0449-02`), normalized by us to 11 digits. |
| **UPC-A / EAN-13** | Retail barcode formats. For drugs, the UPC-A barcode usually contains the NDC. |
| **NDC directory** | FDA's public list of every marketed drug product and package. Downloaded from openFDA. |
| **openFDA** | FDA's public data site (open.fda.gov) with bulk downloads and APIs. |
| **DailyMed** | National Library of Medicine site with the full official label of every drug. |
| **SPL** | Structured Product Labeling: the XML format DailyMed labels come in. Each label has a **set id** (stable across versions) and a **version** number. |
| **Drug Facts panel** | The standard label on every OTC box: Active ingredient, Purpose, Uses, Warnings, Directions, Inactive ingredients. |
| **LOINC section code** | A code that marks each section inside an SPL file, e.g. `34071-1` means Warnings. Lets us split labels reliably. |
| **Mandated warning** | Warning text FDA requires on certain products, e.g. "Liver warning" on every acetaminophen product. Standard wording makes it easy to extract. |
| **Monograph** | FDA's rulebook for a category of OTC drugs (e.g. pain relievers): allowed ingredients, doses and required warnings. |
| **Marketing category** | How a product is legally sold: under an OTC monograph, under an NDA (a prescription drug switched to OTC, like Claritin), or as unapproved homeopathic. |
| **UNII** | FDA's unique ID for an ingredient. Labels use it, so it's our main ingredient key. |
| **RxNorm / RxCUI** | NLM's drug vocabulary and its IDs. We use it to match messy drug names (from FAERS) to ingredients. Needs a free **UMLS** license. |
| **FAERS** | FDA Adverse Event Reporting System: millions of reports of people having bad reactions. Shows what problems get reported, but has no denominator (we don't know how many people took the drug without problems). |
| **MedDRA** | The medical vocabulary FAERS uses for reactions (e.g. "Hepatic failure"). |
| **Signal / IC / IC025** | A signal means a reaction is reported with a drug more often than expected. The IC (information component) measures this with Bayesian shrinkage, which keeps rare drugs from producing noisy results. IC025 is its lower confidence bound; IC025 above 0 counts as a signal. |
| **Anticholinergic / ACB scale** | Drugs that block acetylcholine can cause confusion and memory problems, especially in older adults. The ACB (Anticholinergic Cognitive Burden) scale rates drugs 0 to 3. |
| **STOPP/START** | Published expert criteria listing medicines older adults should avoid in specific situations (e.g. NSAIDs with kidney disease). |
| **NSAID** | Non-steroidal anti-inflammatory drug: ibuprofen (Advil), naproxen (Aleve), aspirin. Risks include stomach bleeding, kidney problems and raised blood pressure. |
| **Persona** | A type of person we score for: adult 18-64, 65+, teen 12-17, child 6-11, child 2-5, under 2, pregnant, breastfeeding. |
| **Profile** | A specific user's details on their phone: persona plus optional conditions (e.g. high blood pressure) and medication types (e.g. blood thinners). |
| **Risk dimension** | One kind of risk we rate every ingredient on: liver, GI bleeding, blood pressure, kidney, memory/thinking, sedation/falls, interactions, and so on. Defined in `docs/scoring/dimensions.md`. |
| **Severity** | 0 to 3 rating of an ingredient on one risk dimension for one persona. |
| **Hard stop** | A rule that makes a product red no matter what, e.g. the label says "do not use" for this persona. |
| **Rubric** | The written rules that turn severities into points and a 0-100 score. Version 0 is in `docs/rubric/v0.md`. |
| **Term tables** | The rubric exported as lookup tables: "this ingredient, this dimension, this persona costs N points." The phone adds them up. |
| **Golden vectors** | Test cases of (product, profile, expected score) used to check Python and the app compute the same answer. |
| **Knowledge base** | Our curated, cited ratings per ingredient, stored as YAML in `pipeline/knowledge/`. Reviewed like code. |
| **Benchmark** | "Better than 82% of pain relievers for you": a product's rank among products with the same use. |
| **Uses** | What a product is for (pain, sleep, nasal allergy, heartburn...). Alternatives must share a use. |
| **Bronze / silver / gold** | Pipeline data layers: bronze is raw data in tables, silver is cleaned and joined, gold is final outputs. All under `data/` and never committed. |
| **Parquet / DuckDB / Polars** | Parquet is the table file format we use. Polars is the Python dataframe library. DuckDB lets you run SQL over Parquet files. |
| **R2** | Cloudflare's file storage (free tier) where we mirror raw data and publish datasets. |
| **Expo / dev build** | Expo is the React Native framework for the app. A dev build is a custom build installed on your phone (needed because our camera library doesn't run in the Expo Go app). |
| **ADR** | Architecture Decision Record: a short doc recording a decision and why. In `docs/adr/`. |

## Where things live

| Folder | What's there |
|---|---|
| `apps/mobile` | The phone app |
| `apps/dashboard` | Internal data dashboard |
| `packages/schema` | Shared data formats, example products and test vectors |
| `pipeline/src/nomi_pipeline` | Pipeline code, one folder per stage |
| `pipeline/knowledge` | Curated ratings, criteria and explanation templates |
| `docs/` | Decisions, scoring definitions, rubric, demo script |
| `planning/` | Backlog and sprint plan |
| `data/` | Your local pipeline data (gitignored) |

## Teams

- **Platform**: gets data in and ships it out. Downloads, parsing, barcode resolution, dataset builds.
- **Visualization**: everything in the app and dashboards. Camera, screens, on-device scoring.
- **Data Analysis**: turns data into ratings and scores. Label extraction, knowledge base, FAERS signals, rubric.
- **Cofounders**: setup, decisions, legal, faculty partnership, demo.

## How to work a ticket

1. Read the whole ticket, including "Before you start" and "Out of scope".
2. If a dependency hasn't merged yet, check whether the ticket says to start against a fixture or the
   reference products in `packages/schema/examples/`.
3. Create a branch: `<your-name>/<issue-number>-short-slug`.
4. Open a draft PR early and link the issue (`Closes #12`).
5. Work through the steps. Ask in your team channel if something is unclear; don't guess on medical facts.
6. Check every box under "Done when", then mark the PR ready for review.

## Going deeper

For the full architecture, data formats, scoring model and roadmap, read `docs/system-design.md`.

## The demo

Everything before Nov 20 serves one demo: someone hands us a box, we scan it in airplane mode, and
Nomi shows a personalized score, the reasons, and a safer option. Script: `docs/demo/script.md`.
