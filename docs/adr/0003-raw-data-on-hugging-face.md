# 0003: Mirror raw data to a Hugging Face dataset

**Status:** proposed
**Date:** 2026-11-06
**Deciders:** Shreyas Shrestha, platform team

## Context

NOMI-008 planned to mirror the raw sources to Cloudflare R2 so every developer and CI run builds
from the same files. Measured sizes:

| Source | Size |
|---|---|
| openFDA NDC directory | 26 MB |
| FAERS quarterly ASCII files, 2014 onward | about 2.8 GB, growing about 250 MB a year |
| DailyMed OTC release (11 parts) | about 34 GB, but label XML is under 1% of it |

R2's free tier is 10 GB and we have no budget. All three sources are US government works in the
public domain, so we do not need private storage for them.

## Decision

- Mirror raw sources to a Hugging Face dataset repo, starting private and made public once the
  license audit (NOMI-006) and the dataset card are done.
- Store DailyMed as label XML only (about 300 MB), stripped from the release zips by
  `pipeline/scripts/slim_dailymed.py`. Product images are dropped.
- `fetch` and `mirror` use fsspec, and the store location is one setting: `RAW_STORE`. Moving to
  R2, S3 or GCS later is a copy plus a one-line change.
- Each source keeps a checksum `manifest.json`; mirroring adds to it and never replaces it.
- Only unmodified public FDA and NLM files go in. Never RxNorm (UMLS license forbids
  redistribution), user data, or anything we produce.

This covers raw inputs only. Publishing the app's SQLite dataset (NOMI-038) still targets R2.

## Alternatives considered

- **Cloudflare R2 as planned.** The raw data is about 37 GB against a 10 GB free tier; even
  slimmed it would fit, but needs a payment method on file and token distribution to the team.
- **GitHub Releases.** No total size limit, but a 2 GiB per-file limit means splitting DailyMed
  parts, and scripting uploads is clunkier.
- **Download straight from FDA and NLM every time.** No storage at all, but NDC and DailyMed change
  weekly, so two teammates could build from different data.

## Consequences

- Free with no card, and public reads need no token once the dataset is public.
- Every mirror is a commit, so a build can pin an exact snapshot with `RAW_STORE=...@<commit>`.
- Our sources are publicly inspectable, which supports the "evidence, not a black box" goal.
- The SPL ingest (NOMI-010) must read XML from the slimmed `*.xml.zip` files.
- We depend on Hugging Face storage policy, which has changed before. The fsspec setting and the
  manifest of original URLs and checksums keep us able to move or rebuild.
- Anything published is effectively permanent, so the "public sources only" rule must hold.
