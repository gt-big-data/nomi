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
  - adverse-events
  - drug-labels
size_categories:
  - 10K<n<100K
---

<!--
Published as the README.md of https://huggingface.co/datasets/nomi-bdbi-gt/nomi-raw-data
(ADR-0003). Edit it in the Nomi repo and upload it again; do not edit it on Hugging Face.
-->

# Nomi raw sources

Snapshots of the public US government data that the Nomi pipeline reads. Nomi helps people compare
the safety of over-the-counter medicines. This dataset exists so every build uses identical inputs,
and so anyone can see exactly where our data comes from.

The files are unmodified copies of the sources below, except that DailyMed is stored as label XML
only (product packaging images removed).

## Sources

| Folder | Source | Publisher | Contents | Update cadence |
|---|---|---|---|---|
| `ndc/` | [openFDA NDC directory](https://open.fda.gov/apis/drug/ndc/) | US Food and Drug Administration | 1 JSON file, every listed drug product | Weekly |
| `dailymed-otc/` | [DailyMed human OTC label release](https://dailymed.nlm.nih.gov/dailymed/spl-resources-all-drug-labels.cfm) | US National Library of Medicine | 12 zips, 89,770 SPL label XMLs | Monthly |
| `faers/` | [FAERS quarterly data files](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html) | US Food and Drug Administration | 51 quarterly ASCII zips, 2014Q1 to 2026Q3 | Quarterly |

First mirrored November 2026. Each folder has a `manifest.json` listing every file with its
SHA-256 checksum and size; retrieval dates are in the commit history.

### DailyMed layout

Each `dm_spl_release_human_otc_partN.xml.zip` holds one `<date>_<setid>.xml` per label, taken from
the inner zips of NLM's `dm_spl_release_human_otc_partN.zip`. The XML is the full Structured
Product Labeling document; only the JPEG images bundled beside it were dropped.

## Using it

With the Nomi repo:

```bash
uv run pipeline fetch all
```

Or directly:

```python
from huggingface_hub import snapshot_download

snapshot_download("nomi-bdbi-gt/nomi-raw-data", repo_type="dataset", allow_patterns="ndc/*")
```

Pin a snapshot by passing `revision=<commit>`.

## License

These are works of the US federal government and are in the public domain in the United States.
openFDA data is published under a CC0 1.0 dedication, and this dataset is offered under the same
terms. Drug labels are submitted to FDA by their manufacturers; trademarks in them belong to their
owners.

## Disclaimers

- FDA and NLM do not endorse Nomi or this dataset.
- FAERS reports are unverified and cannot establish that a drug caused an adverse event.
- Nothing here is medical advice.
