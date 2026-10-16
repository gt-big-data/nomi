# Nomi planning

New to the project? Start with `docs/nomi-101.md`. To write a new ticket, follow `planning/ticket-template.md`.

This folder is the source of truth for the initial backlog. `backlog.md` holds every ticket in a
format both people and `create_issues.py` can read; the script turns it into GitHub labels,
milestones and issues.

## Product direction (agreed so far)

- **Every OTC product, one framework.** Each ingredient is scored on the same ~15 risk dimensions
  (liver, GI bleeding, cardiovascular/BP, kidney, anticholinergic/cognitive, sedation/falls,
  interactions, pediatric, rebound/overuse, pregnancy, duplicate dosing, excipients, efficacy…),
  per persona and health condition. Products are benchmarked against others with the same use.
- **Evidence, not a black box:** FDA-mandated label warnings (rules + LLM extraction), FAERS
  Bayesian signals mapped to dimensions, STOPP/START and ACB, and later published effect sizes and
  pharmacist judgments. Not a classifier trained on FAERS labels.
- **Train centrally, infer on the device.** The pipeline exports the model as additive term tables
  in a versioned SQLite file; the phone computes the personalized score locally.
- **Health data never leaves the phone** (ADR-0002): profile, conditions, cabinet and scan history
  are on-device only. The backend is thin and holds no health data.
- **Identity chain:** barcode to NDC (embedded in drug UPC-A) to DailyMed SPL to ingredients/strengths.
  All public-domain sources.
- **LLMs only offline** (label extraction with human verification). Explanations are templated.
- **Bootstrapped:** free tiers, university resources, faculty partnership. No paid vendors.

## Sprints

Every ticket is one deliverable for one person in one 1-week sprint. GitHub milestones are sprints.
Team sizes assumed: Platform 4, Visualization 4, Data Analysis 5, plus 2 cofounders (15 total).

| Sprint | Dates | Exit criteria |
|---|---|---|
| **S1** | Oct 16 to Oct 22 | Repo, CI, contracts, ADRs merged; raw data mirrored; app scans on real phones; dimensions defined; demo script written |
| **S2** | Oct 23 to Oct 29 | Identity resolver with coverage number (checkpoint ≥90%); label sections; FAERS ingested; knowledge base for the four demo aisles; core app screens |
| **S3** | Oct 30 to Nov 5 | ≥95% identity coverage; label facts and uses for every in-scope product; rubric v0 spec; dataset v1 on the phone; encrypted profiles |
| **S4** | Nov 6 to Nov 12 | Scoring, benchmarks, alternatives, FAERS signals; personalized on-device scoring with parity in CI. **Feature freeze Nov 12** |
| **S5** | Nov 13 to Nov 19 | Dataset v1.0, performance and accessibility passes, blind test. **Code freeze Nov 17, demo Nov 20** |

Post-demo work lives in `post-demo.md` as epics, split into sprint tickets at the Nov 20 planning session.

## Teams

| Label | Owns |
|---|---|
| `team:platform` | Backend: raw data mirror, ingestion, identity resolution, contracts, pipeline CLI, dataset build and release |
| `team:visualization` | Frontend: Expo app, scanner, screens, on-device scoring engine, dashboards |
| `team:data-analysis` | Data analysis: label extraction, knowledge base, FAERS normalization and signals, uses, rubric, benchmarks, alternatives |
| `team:cofounders` | Scaffolding, ADRs, legal, faculty partnership, demo script and rehearsals |
| `team:all` | Barcode collection drive |

Priorities: **P0** blocks the demo, **P1** should land in its sprint.
Dependencies marked `(same sprint)` mean: build against the reference records (NOMI-015) or a fixture,
integrate when the upstream ticket merges.

## Conventions

- Every PR references its issue (`Closes #12`). Squash merge. One approving review.
- "Done" means merged with tests, documented in the relevant README, and demoable.
- Architecture decisions go in `docs/adr/NNNN-title.md` before code depends on them.
- Shared contracts live in `packages/schema`. Changing them needs a review from both teams.

## Creating the issues

```bash
python3 planning/create_issues.py --dry-run
```

```bash
python3 planning/create_issues.py
```

The script is idempotent: it skips labels, milestones and issues (matched by title) that already
exist. After creating issues it rewrites `NOMI-0xx` dependency references into `#issue` links.
