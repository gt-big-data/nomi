---
license: cc0-1.0
pretty_name: Nomi raw sources
language:
  - en
tags:
  - medical
  - pharmacy
  - fda
  - otc
---

<!--
Draft dataset card for the Hugging Face raw dataset (ADR-0003). Upload it as the dataset's README.md
once the license audit (NOMI-006) signs off and before making the dataset public.
-->

# Nomi raw sources

Snapshots of the public US government data that the Nomi pipeline reads. Nomi helps people compare
the safety of over-the-counter medicines. This dataset exists so every build uses identical inputs.

The files are unmodified copies of the sources below, except that DailyMed is stored as label XML
only (product images removed).

## Sources

| Folder | Source | Publisher | Update cadence |
|---|---|---|---|
| `ndc/` | [openFDA NDC directory](https://open.fda.gov/apis/drug/ndc/) | US Food and Drug Administration | Daily |
| `dailymed-otc/` | [DailyMed human OTC label release](https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm), XML only | US National Library of Medicine | Monthly |
| `faers/` | [FAERS quarterly data files](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html), 2014 onward | US Food and Drug Administration | Quarterly |

Each folder has a `manifest.json` listing every file with its SHA-256 checksum and size. Retrieval
dates are in the commit history.

## License

These are works of the US federal government and are in the public domain in the United States.
openFDA data is published under a CC0 1.0 dedication. Drug labels are submitted to FDA by their
manufacturers; trademarks in them belong to their owners.

## Disclaimers

- FDA and NLM do not endorse Nomi or this dataset.
- FAERS reports are unverified and cannot establish that a drug caused an adverse event.
- Nothing here is medical advice.
