# Score visualization

**Status:** proposed
**Date:** 2026-10-28
**Deciders:** @spandan972 (Visualization)
**Issue:** #15 (NOMI-014) · Blocks #41

## Context

The result screen has to answer two questions in a few seconds: is this product OK for this person,
and why. We designed three ways to show the score and three ways to show the breakdown, then tested
them with 5 people to pick the clearest.

Figma: [Score card and risk row](https://www.figma.com/design/TG1HUhuo037wkCLmFGxcLf/NOMI-014-Score-card---Risk-row--for-Nomi-Library-?node-id=0-1)

## Decision

- **Score: Verdict (B), with a larger number.** Lead with the tier word and who it's for ("Use with
  caution for a 72-year-old with high blood pressure"), and show the 0-100 score clearly next to it
  rather than in small text.
- **Breakdown: Plain list (2).** One plain-language sentence per risk, a High/Moderate/Low label, and
  the source visible without tapping.
- **Benchmark (C) and From 100 (3) are dropped** as primary views.

## Concepts

All six concepts use the same example data, so participants compared designs rather than products.

| Scenario | Product                       | Who                            | Score | Tier           |
| -------- | ----------------------------- | ------------------------------ | ----- | -------------- |
| S1       | Acetaminophen 500 mg          | Adult, 30, no conditions       | 88    | green          |
| S2       | Ibuprofen 200 mg              | Adult 65+, high blood pressure | 54    | yellow         |
| S3       | Diphenhydramine 25 mg (sleep) | Adult 65+                      | 22    | red, hard stop |

The data is illustrative and not output from the rubric.

### Score

| ID  | Concept   | What it shows                                                              |
| --- | --------- | -------------------------------------------------------------------------- |
| A   | Dial      | The 0-100 number inside a ring colored by tier, with the tier word below   |
| B   | Verdict   | The tier word first ("Use with caution"), who it's for, the number small   |
| C   | Benchmark | Percentile against similar products, with this product on a strip of peers |

### Breakdown

| ID  | Concept    | What it shows                                                                  |
| --- | ---------- | ------------------------------------------------------------------------------ |
| 1   | Bars       | Points lost per risk dimension as horizontal bars; tap a bar for the source    |
| 2   | Plain list | One plain-language sentence per risk with a High/Moderate/Low label and source |
| 3   | From 100   | One stacked bar: points kept vs. points lost to each risk, with a legend       |

## Method

- 5 participants (P1-P5), about 10 minutes each. No names or health details recorded.
- Each participant saw all three scenarios, each with a different score and breakdown concept.
  Concept order rotated per participant so no concept always came first.
- After each screen we asked: Would you buy this for them? What's the biggest risk? What score did
  it get? How sure are you (1-5)? We timed how long each person took to decide.
- At the end: which view was clearest, and which did you trust most?
- Raw notes are in the comments on #15.

## Results

Each concept was seen 5 times (once per participant), for 15 screens in total. Every participant
made a sensible buy decision on every screen, so the concepts differ on understanding, speed and
confidence rather than on the final call.

"Main risk" counts as correct when the participant named the top item in the breakdown. "Score"
counts as correct when they gave the score or a close estimate ("around 50", "low, like 20").

### Score concepts

| Concept       | Picked as clearest | Named main risk | Read the score correctly | Median time | Median confidence |
| ------------- | ------------------ | --------------- | ------------------------ | ----------- | ----------------- |
| A Dial        | 2 / 5              | 5 / 5           | 5 / 5                    | 9.4 s       | 4                 |
| B Verdict     | **3 / 5**          | 4 / 5           | 5 / 5                    | **7.3 s**   | **5**             |
| C Benchmark   | 0 / 5              | 4 / 5           | 1 / 5                    | 18.9 s      | 3                 |

### Breakdown concepts

| Concept       | Trusted most | Named main risk | Median time | Median confidence |
| ------------- | ------------ | --------------- | ----------- | ----------------- |
| 1 Bars        | 1 / 5        | 5 / 5           | 9.4 s       | 4                 |
| 2 Plain list  | **4 / 5**    | **5 / 5**       | **8.1 s**   | **5**             |
| 3 From 100    | 0 / 5        | 3 / 5           | 18.9 s      | 3                 |

P5 named both Dial and Plain list as most trusted; only the breakdown pick is counted above.

### Per participant

| Participant | Clearest score | Trusted most        | Key comment                                                       |
| ----------- | -------------- | ------------------- | ----------------------------------------------------------------- |
| P1          | B Verdict      | 2 Plain list        | "It tells me why in words."                                       |
| P2          | A Dial         | 1 Bars              | "The points make it feel calculated." Asked who sets the points.  |
| P3          | B Verdict      | 2 Plain list        | Benchmark dots were "too much to read in a store."                |
| P4          | A Dial         | 2 Plain list        | Trusted the list because sources show without tapping.            |
| P5          | B Verdict      | A Dial, 2 Plain list | "Words to decide, number to believe it."                         |

## Why

**Verdict for the score.** It was the fastest concept (median 7.3 s), had the highest confidence and
was picked as clearest most often (3 of 5). Every participant still recalled the score from it,
even though it was printed small. Dial had a perfect score-recall rate and 2 of 5 picked it as
clearest, and P5 summed up the split: "words to decide, number to believe it." So we keep Verdict's
layout and make the number more prominent to get the strengths of both.

**Plain list for the breakdown.** It was the only breakdown with perfect main-risk accuracy and the
fastest median time (8.1 s), and 4 of 5 participants trusted it most. Showing the source inline
mattered: P4 pointed at the Beers Criteria citation as the reason to trust it, and P1 said it
explains "why in words."

## Alternatives considered

- **A Dial.** Accurate and well liked (2 of 5 clearest, 5 of 5 read the score), but slower than
  Verdict and the number alone doesn't say what to do. Its larger number is folded into the chosen
  design.
- **C Benchmark.** 4 of 5 participants mistook the percentile for the score ("22%? wait, is that the
  score?", "maybe 70?"). It was also the slowest concept (18.9 s) with the lowest confidence. P4
  found the comparison useful, so a one-line text comparison can return as secondary information
  (see #61), but not as the main score.
- **1 Bars.** Accurate (5 of 5) and P2 trusted the visible points, but most participants preferred
  words over numbers to understand a risk, and sources are hidden behind a tap.
- **3 From 100.** Slowest breakdown (18.9 s), lowest accuracy (3 of 5), and it raised the wrong
  question: "why isn't it 100?" Participants also confused the bar's numbers with the percentile.

## Limitations

- 5 participants is enough to spot large usability problems, not to measure small differences.
- In 4 of 5 sessions the score and breakdown concepts were paired the same way (A with 1, B with 2,
  C with 3). Only P5 saw other pairings, so the effects of a score view and the breakdown shown with
  it are partly mixed together. The Benchmark and From 100 results especially may make each other
  look worse.
- Each concept was seen with a different mix of products, and participant ages and backgrounds
  weren't recorded. None were confirmed to be older adults, a key Nomi audience.

## Consequences

- #41 builds the Plain list breakdown, and the result screen uses the Verdict layout with a larger
  score.
- The chosen design is built as two components, a score card (Verdict) and a risk row (Plain list),
  in [this Figma file](https://www.figma.com/design/TG1HUhuo037wkCLmFGxcLf/NOMI-014-Score-card---Risk-row--for-Nomi-Library-?node-id=0-1). They move into the Nomi Library (#13) once edit access is
  sorted out.
- Follow-ups to consider:
  - Test the chosen design with older adults, ideally 65+.
  - Try showing points lost next to each Plain list item for users who want the numbers (P2).
  - Explain where the points come from, since P2 asked who decides them.
  - Add a benchmark as one line of text if #61 needs it, worded so it can't be read as the score.
