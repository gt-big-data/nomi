import json
from pathlib import Path

import pytest
from nomi_pipeline.cli import app
from nomi_pipeline.extract.rules import extract, extract_text
from typer.testing import CliRunner

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
SNIPPETS = [
    json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((FIXTURES / "warnings").glob("*.json"))
]
SNIPPET_WARNING_IDS = {
    "liver_warning",
    "stomach_bleeding_warning",
    "nsaid_allergy_alert",
    "reyes_syndrome_warning",
    "diphenhydramine_duplicate_use_warning",
}


def load_label(name: str) -> dict[str, object]:
    label: dict[str, object] = json.loads((FIXTURES / "labels" / f"{name}.json").read_text())
    return label


def test_mandated_warning_recall_on_label_snippets() -> None:
    expected = sum(len(snippet["expected_warnings"]) for snippet in SNIPPETS)
    found = sum(
        len(set(snippet["expected_warnings"]) & extract_text(snippet["text"]).warning_ids())
        for snippet in SNIPPETS
    )
    assert expected >= 45
    assert found / expected >= 0.98


def test_no_false_warnings_on_label_snippets() -> None:
    for snippet in SNIPPETS:
        found = extract_text(snippet["text"]).warning_ids() & SNIPPET_WARNING_IDS
        assert found <= set(snippet["expected_warnings"]), snippet["id"]


def test_evidence_points_at_label_text() -> None:
    for snippet in SNIPPETS:
        for fact in extract_text(snippet["text"]).warnings:
            assert snippet["text"][fact.evidence.start : fact.evidence.end] == fact.evidence.text


@pytest.mark.parametrize(
    ("text", "warning_id", "dimension"),
    [
        (
            "Liver warning This product contains acetaminophen. Severe liver damage may occur",
            "liver_warning",
            "liver",
        ),
        (
            "Acetaminophen liver damage warning: This product contains acetaminophen.",
            "liver_warning",
            "liver",
        ),
        (
            "Stomach bleeding warning : This product contains an NSAID, which may cause",
            "stomach_bleeding_warning",
            "gi_bleeding",
        ),
        (
            "Heart attack and stroke warning: NSAIDs, except aspirin, increase the risk",
            "heart_attack_and_stroke_warning",
            "cardiovascular_bp",
        ),
        (
            "NSAID allergy alert: ibuprofen may cause a severe allergic reaction",
            "nsaid_allergy_alert",
            None,
        ),
        (
            "Reye’s syndrome Children and teenagers who have or are recovering from chicken pox",
            "reyes_syndrome_warning",
            "pediatric",
        ),
        (
            "Do not use • with any other drug containing acetaminophen (prescription or nonprescription)",
            "acetaminophen_duplicate_use_warning",
            "duplicate_dosing",
        ),
        (
            "if you are now taking a prescription monoamine oxidase inhibitor (MAOI)",
            "maoi_warning",
            "serotonergic_interactions",
        ),
        (
            "It is especially important not to use ibuprofen during the last 3 months of pregnancy",
            "nsaid_pregnancy_warning",
            "pregnancy_lactation",
        ),
        ("Phenylketonurics: Contains Phenylalanine 6 mg", "phenylketonuria_warning", "excipients"),
    ],
)
def test_warning_wording_variants(text: str, warning_id: str, dimension: str | None) -> None:
    facts = extract_text(text)
    assert [(fact.warning_id, fact.dimension) for fact in facts.warnings] == [
        (warning_id, dimension)
    ]


@pytest.mark.parametrize(
    "text",
    [
        "Ask a doctor before use if you have liver disease.",
        "Ask a doctor before use if stomach bleeding warning applies to you",
        "Keep out of reach of children.",
        "In case of overdose, get medical help right away.",
        "Do not use if you have an ulcer a bleeding problem bloody or black stool",
    ],
)
def test_no_warning_in_plain_text(text: str) -> None:
    assert extract_text(text).warnings == []


@pytest.mark.parametrize(
    ("text", "limits"),
    [
        ("children under 12 years: ask a doctor", [("ask_doctor", None, 12)]),
        ("children under 4 yrs do not use", [("do_not_use", None, 4)]),
        ("children 4 to under 12 yrs ask a doctor", [("ask_doctor", 4, 12)]),
        ("children 2 to 5 years do not use unless directed by a doctor", [("ask_doctor", 2, 6)]),
        ("Do not use • for children under 12 years of age", [("do_not_use", None, 12)]),
        ("adults and children 12 years and over take 2 caplets every 8 hours", []),
    ],
)
def test_age_limits(text: str, limits: list[tuple[str, int | None, int]]) -> None:
    found = extract_text(text).age_limits
    assert [(limit.action, limit.min_years, limit.under_years) for limit in found] == limits


@pytest.mark.parametrize(
    ("text", "amount", "unit"),
    [
        ("do not take more than 6 caplets in 24 hours, unless directed by a doctor", 6, "caplets"),
        ("not to exceed 48 tablets in 24 hours unless directed by a doctor", 48, "tablets"),
        ("do not exceed 8 doses (16 caplets) in 24 hours", 8, "doses"),
        ("do not exceed 8 caplets per 24 hrs", 8, "caplets"),
        ("do not give more than 5 times in 24 hours", 5, "doses"),
        ("do not exceed 3 tablets in a 24-hour period", 3, "tablets"),
    ],
)
def test_max_daily_dose(text: str, amount: int, unit: str) -> None:
    doses = extract_text(text).max_daily_doses
    assert [(dose.amount, dose.unit) for dose in doses] == [(amount, unit)]


def test_liver_warning_limit_is_not_a_daily_dose() -> None:
    text = (
        "Severe liver damage may occur if you take more than 4,000 mg of acetaminophen in 24 hours"
    )
    assert extract_text(text).max_daily_doses == []


@pytest.mark.parametrize(
    ("text", "allergen", "kind"),
    [
        ("Allergy alert: Aspirin may cause a severe allergic reaction", "aspirin", "allergy_alert"),
        (
            "NSAID allergy alert: ibuprofen may cause a severe allergic reaction",
            "ibuprofen",
            "allergy_alert",
        ),
        (
            "Acetaminophen allergy alert: may cause severe skin reactions",
            "acetaminophen",
            "allergy_alert",
        ),
        (
            "Allergy alert: Contains salicylate. Do not take if you are allergic",
            "salicylate",
            "allergy_alert",
        ),
        (
            "Phenylketonurics: Contains Phenylalanine 6 mg per tablet",
            "phenylalanine",
            "phenylketonuria",
        ),
        (
            "Inactive ingredients FD&C yellow #5 (tartrazine) aluminum lake",
            "FD&C Yellow No. 5",
            "dye",
        ),
    ],
)
def test_allergens(text: str, allergen: str, kind: str) -> None:
    found = [(item.allergen, item.kind) for item in extract_text(text).allergens]
    assert (allergen, kind) in found


def test_full_label_nyquil() -> None:
    facts = extract(load_label("nyquil_cold_and_flu"))
    assert {
        "liver_warning",
        "acetaminophen_duplicate_use_warning",
        "maoi_warning",
    } <= facts.warning_ids()
    assert [(dose.amount, dose.unit) for dose in facts.max_daily_doses] == [(8, "caplets")]
    assert ("do_not_use", None, 4) in [
        (limit.action, limit.min_years, limit.under_years) for limit in facts.age_limits
    ]


def test_full_label_bayer_aspirin() -> None:
    facts = extract(load_label("bayer_chewable_low_dose_aspirin"))
    assert {
        "reyes_syndrome_warning",
        "nsaid_allergy_alert",
        "stomach_bleeding_warning",
    } <= facts.warning_ids()
    assert "aspirin" in {item.allergen for item in facts.allergens}


def test_full_label_childrens_benadryl() -> None:
    facts = extract(load_label("childrens_benadryl_dye_free"))
    assert facts.warning_ids() == {"diphenhydramine_duplicate_use_warning"}
    assert [(limit.action, limit.min_years, limit.under_years) for limit in facts.age_limits] == [
        ("do_not_use", None, 2),
        ("ask_doctor", 2, 6),
    ]


def test_cli_rules_prints_facts() -> None:
    result = CliRunner().invoke(
        app, ["extract", "rules", str(FIXTURES / "labels" / "pepto_bismol_caplets.json")]
    )
    assert result.exit_code == 0, result.output
    assert "reyes_syndrome_warning" in result.stdout
