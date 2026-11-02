import csv
from nomi_pipeline.evidence.name_matcher import FaersNameMatcher
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "faers_names_labeled.csv"


def load_labeled_data() -> list[dict[str, str]]:
    """Load the CSV into a list of row dictionaries."""
    with open(FIXTURE_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


SAMPLE_CANONICAL: dict[str, tuple[str, ...]] = {
    "acetaminophen": ("362O9ITL9D",),
    "ibuprofen": ("WK2XYI10QM",),
    "aspirin": ("R16CO5Y76E",),
    "naproxen": ("57Y76R9ATQ",),
    "diphenhydramine": ("814498Ch67",),
    "pseudoephedrine": ("7AJO3BO7QN",),
    "caffeine": ("3G6A5W338E",),
    "dextromethorphan": ("7355X3ROTS",),
    "guaifenesin": ("495W7451VQ",),
    "loratadine": ("7AJO3BO7QN",),
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
}


def test_data_structure() -> None:
    """Test that the labeled data structure aligns with expectations."""
    rows = load_labeled_data()
    assert len(rows) >= 500, f"Expected at least 500 rows, got {len(rows)}"

    # Filter for rows where annotator_2 is not empty
    double_labeled = [r for r in rows if r.get("annotator_2", "").strip()]
    assert (
        len(double_labeled) >= 50
    ), f"Expected at least 50 double-labeled, got {len(double_labeled)}"
    agreed = sum(
        1
        for r in double_labeled
        if r["annotator_1"].strip() == r["annotator_2"].strip()
    )
    assert agreed / len(double_labeled) >= 0.95

    held_out = [r for r in rows if r.get("split", "").strip() == "held_out"]
    tuning = [r for r in rows if r.get("split", "").strip() == "tuning"]
    assert (
        len(held_out) >= 250
    ), f"Expected at least 250 held-out samples, got {len(held_out)}"
    assert (
        len(tuning) >= 250
    ), f"Expected at least 250 tuning samples, got {len(tuning)}"


def test_held_out() -> None:
    """Test that the held-out data achieves at least 97% precision with the sample matcher."""
    rows = load_labeled_data()
    # Filter for the held-out partition
    held_out = [r for r in rows if r.get("split", "").strip() == "held_out"]
    held_out_raw_names = [r["raw_name"] for r in held_out]
    held_out_uniis = [r.get("uniis") or r.get("expected_uniis", "") for r in held_out]

    matcher = FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS, fuzzy_threshold=0.85)
    matched_results = matcher.match_batch(held_out_raw_names)

    tp = 0
    fp = 0
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
