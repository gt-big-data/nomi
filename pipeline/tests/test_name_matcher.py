import csv
from pathlib import Path

<<<<<<< HEAD
from nomi_pipeline.evidence.name_matcher import FaersNameMatcher
=======
from nomi_pipeline.evidence.name_matcher import FaersNameMatcher, tune_fuzzy_threshold
>>>>>>> feat/NOMI-033-match-faers

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "faers_names_labeled.csv"


def load_labeled_data() -> list[dict[str, str]]:
    """Load the CSV into a list of row dictionaries."""
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


SAMPLE_CANONICAL: dict[str, tuple[str, ...]] = {
    "acetaminophen": ("362O9ITL9D",),
    "ibuprofen": ("WK2XYI10QM",),
    "aspirin": ("R16CO5Y76E",),
    "naproxen": ("57Y76R9ATQ",),
    "diphenhydramine": ("814498Ch67",),
    "pseudoephedrine": ("6V9V2RYJ8N",),
    "caffeine": ("3G6A5W338E",),
    "dextromethorphan": ("7355X3ROTS",),
    "guaifenesin": ("495W7451VQ",),
    "loratadine": ("7AJO3BO7QN",),
    "cetirizine": ("64O047KTOA",),
    "fexofenadine": ("2S068B75ZU",),
    "doxylamine": ("V9BI9B5YI2",),
}

SAMPLE_SYNONYMS: dict[str, tuple[str, ...]] = {
    "tylenol": ("362O9ITL9D",),
    "advil": ("WK2XYI10QM",),
    "motrin": ("WK2XYI10QM",),
    "bayer": ("R16CO5Y76E",),
    "aleve": ("57Y76R9ATQ",),
    "benadryl": ("814498Ch67",),
    "excedrin": ("362O9ITL9D", "R16CO5Y76E", "3G6A5W338E"),
    "advil pm": ("WK2XYI10QM", "814498Ch67"),
    "zyrtec": ("64O047KTOA",),
    "allegra": ("2S068B75ZU",),
    "claritin": ("7AJO3BO7QN",),
    "sudafed": ("6V9V2RYJ8N",),
    "mucinex": ("495W7451VQ",),
    "delsym": ("7355X3ROTS",),
    "unisom": ("V9BI9B5YI2",),
}


def test_data_structure() -> None:
    """Test that the labeled data structure aligns with expectations."""
    rows = load_labeled_data()
    assert len(rows) >= 500, f"Expected at least 500 rows, got {len(rows)}"

    # Filter for rows where annotator_2 is not empty
    double_labeled = [r for r in rows if r.get("annotator_2", "").strip()]
    assert len(double_labeled) >= 50, (
        f"Expected at least 50 double-labeled, got {len(double_labeled)}"
    )
    agreed = sum(1 for r in double_labeled if r["annotator_1"].strip() == r["annotator_2"].strip())
    assert agreed / len(double_labeled) >= 0.95

    held_out = [r for r in rows if r.get("split", "").strip() == "held_out"]
    tuning = [r for r in rows if r.get("split", "").strip() == "tuning"]
    assert len(held_out) >= 250, f"Expected at least 250 held-out samples, got {len(held_out)}"
    assert len(tuning) >= 250, f"Expected at least 250 tuning samples, got {len(tuning)}"


def test_held_out() -> None:
    """Test that the held-out data achieves at least 97% precision with the sample matcher."""
    rows = load_labeled_data()
    # Filter for the held-out partition
    held_out = [r for r in rows if r.get("split", "").strip() == "held_out"]
    held_out_raw_names = [r["raw_name"] for r in held_out]
    held_out_uniis = [r.get("uniis") or r.get("expected_uniis", "") for r in held_out]

    matcher = FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS, fuzzy_threshold=0.85)
    matched_results = matcher.match_batch(held_out_raw_names)

    tp, fp = 0, 0
    for i in range(len(held_out)):
        match = matched_results[i]
        true_uniis = held_out_uniis[i].strip()

        # Unmapped names are treated as negatives; skip them
        if match.method == "unmapped":
            continue

        # Safely parse the expected UNIIs (empty string becomes empty set)
        expected_set = {u.strip() for u in true_uniis.split(";") if u.strip()}

        if set(match.uniis) == expected_set:
            tp += 1
        else:
            fp += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    assert precision >= 0.97, f"Precision was {precision:.2%}, expected >= 97%"


def test_tune_fuzzy_threshold_selects_optimal_threshold() -> None:
    """Test that tune_fuzzy_threshold selects an optimal threshold achieving >= 97% precision on tuning fuzzy attempts."""
    rows = load_labeled_data()
    tuning = [r for r in rows if r.get("split", "").strip() == "tuning"]
    matcher = FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS)

    optimal_threshold = tune_fuzzy_threshold(tuning, matcher, target_precision=0.97)

    assert isinstance(optimal_threshold, float)
    assert 0.0 < optimal_threshold <= 1.0

    # Verify fuzzy precision on tuning data at the chosen threshold
    matcher.fuzzy_threshold = optimal_threshold
    tuning_raw_names = [r["raw_name"] for r in tuning]
    results = matcher.match_batch(tuning_raw_names)

    fuzzy_tp = 0
    fuzzy_fp = 0
    for r, match in zip(tuning, results, strict=True):
        if match.method != "fuzzy":
            continue
        true_uniis = {u.strip() for u in (r.get("uniis") or "").split(";") if u.strip()}
        if set(match.uniis) == true_uniis:
            fuzzy_tp += 1
        else:
            fuzzy_fp += 1

    assert fuzzy_tp + fuzzy_fp > 0, "Expected fuzzy matches in tuning set"
    tuning_fuzzy_precision = fuzzy_tp / (fuzzy_tp + fuzzy_fp)
    assert tuning_fuzzy_precision >= 0.97, (
        f"Tuning fuzzy precision was {tuning_fuzzy_precision:.2%}, expected >= 97%"
    )


def test_tune_fuzzy_threshold_held_out_fuzzy_precision() -> None:
    """Test that applying the tuned threshold to held-out data achieves >= 97% fuzzy-only precision."""
    rows = load_labeled_data()
    tuning = [r for r in rows if r.get("split", "").strip() == "tuning"]
    held_out = [r for r in rows if r.get("split", "").strip() == "held_out"]

    matcher = FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS)
    optimal_threshold = tune_fuzzy_threshold(tuning, matcher, target_precision=0.97)

    matcher.fuzzy_threshold = optimal_threshold
    held_out_raw_names = [r["raw_name"] for r in held_out]
    results = matcher.match_batch(held_out_raw_names)

    fuzzy_tp = 0
    fuzzy_fp = 0
    for r, match in zip(held_out, results, strict=True):
        if match.method != "fuzzy":
            continue

        true_uniis = {
            u.strip()
            for u in (r.get("uniis") or r.get("expected_uniis", "")).split(";")
            if u.strip()
        }
        if set(match.uniis) == true_uniis:
            fuzzy_tp += 1
        else:
            fuzzy_fp += 1

    assert fuzzy_tp + fuzzy_fp > 0, "Expected at least one fuzzy match on held-out data"
    fuzzy_precision = fuzzy_tp / (fuzzy_tp + fuzzy_fp)
    assert fuzzy_precision >= 0.97, (
        f"Held-out fuzzy-only precision was {fuzzy_precision:.2%}, expected >= 97%"
    )


def test_tune_fuzzy_threshold_evaluates_residual_only() -> None:
    """Test that queries resolvable by exact, synonym, or combination matching are excluded from fuzzy evaluation."""
    matcher = FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS)
    sample_rows = [
        # Exact match query with wrong UNII: if evaluated as a fuzzy candidate, it would corrupt evaluation
        {"raw_name": "aspirin", "uniis": "WRONG_UNII"},
        # Synonym match query with wrong UNII:
        {"raw_name": "tylenol", "uniis": "WRONG_UNII"},
        # Combination match query with wrong UNII:
        {"raw_name": "aspirin / caffeine", "uniis": "WRONG_UNII"},
        # True fuzzy residual query (minor typo for aspirin) with correct UNII:
        {"raw_name": "asprin", "uniis": "R16CO5Y76E"},
    ]
    threshold = tune_fuzzy_threshold(
        sample_rows,
        matcher,
        candidate_thresholds=[0.80],
        target_precision=0.97,
    )
    # At 0.80, 'asprin' fuzzy matches 'aspirin' (TP).
    # Since exact/synonym/combination rows are excluded, precision is 100% and 0.80 is accepted.
    assert threshold == 0.80


def test_tune_fuzzy_threshold_custom_candidates() -> None:
    """Test tune_fuzzy_threshold with custom candidate thresholds list."""
    rows = load_labeled_data()
    tuning = [r for r in rows if r.get("split", "").strip() == "tuning"]
    matcher = FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS)

    candidates = [0.80, 0.84, 0.90]
    threshold = tune_fuzzy_threshold(
        tuning,
        matcher,
        candidate_thresholds=candidates,
        target_precision=0.97,
    )
    assert threshold in candidates
    assert threshold == 0.84
