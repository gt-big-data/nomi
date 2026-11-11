import json
import sys
from pathlib import Path

import pytest

from nomi_pipeline.extract.rules import (
    expected_warning_ids, extract_age_limits, extract_all, extract_allergens, extract_dosing,
    DEFAULT_REGISTRY, _parse_simple_registry, extract_warnings, load_registry, missing_warning_ids,
)


def vals(findings):
    return [f.value for f in findings]


# ---------------------------------------------------------------- warnings
REGISTRY = load_registry()
ALL_VARIANTS = [(s.id, v) for s in REGISTRY for v in s.variants]


def ids(findings, source=None):
    return {f.value["id"] for f in findings if source in (None, f.value["source"])}


def messy(variant: str) -> str:
    """Simulate label/OCR noise: curly quotes, line wraps every 5 words,
    hyphen wraps, ALL CAPS, and surrounding label text."""
    words = variant.replace("'", "\u2019").split()
    lines = [" ".join(words[i:i + 5]) for i in range(0, len(words), 5)]
    body = "\n".join(lines)
    return f"DRUG FACTS\nUses: temporarily relieves minor aches\nWarnings\n{body.upper()}\nDirections: see below"


def test_registry_loads_without_pyyaml():
    saved = sys.modules.get("yaml")
    sys.modules["yaml"] = None  # makes `import yaml` raise ImportError
    try:
        specs = load_registry()
    finally:
        if saved is None:
            del sys.modules["yaml"]
        else:
            sys.modules["yaml"] = saved
    assert len(specs) == 10 and specs[0].id == "liver_warning"
    assert sum(len(s.variants) for s in specs) == 23


def test_simple_parser_matches_pyyaml():
    try:
        import yaml
    except ImportError:
        pytest.skip("PyYAML not installed")
    text = DEFAULT_REGISTRY.read_text(encoding="utf-8")
    assert _parse_simple_registry(text) == yaml.safe_load(text)


def test_registry_loads_all_warnings():
    assert len(REGISTRY) == 10 and len(ALL_VARIANTS) == 23


@pytest.mark.parametrize("wid,variant", ALL_VARIANTS)
def test_every_registry_variant_is_found_clean(wid, variant):
    assert wid in ids(extract_warnings(f"Warnings\n{variant} More label text follows."), "mandated")


@pytest.mark.parametrize("wid,variant", ALL_VARIANTS)
def test_every_registry_variant_is_found_noisy(wid, variant):
    assert wid in ids(extract_warnings(messy(variant)), "mandated")


def test_mandated_warning_recall_on_registry_is_at_least_98pct():
    hit = sum(wid in ids(extract_warnings(messy(v)), "mandated") for wid, v in ALL_VARIANTS)
    assert hit / len(ALL_VARIANTS) >= 0.98


def test_truncated_variant_evidence_extends_to_sentence_end():
    text = ("Liver warning: This product contains acetaminophen. Severe liver damage may occur "
            "if you take more than 4,000 mg of acetaminophen in 24 hours. Do not use with other drugs.")
    f = [x for x in extract_warnings(text) if x.value["id"] == "liver_warning"][0]
    assert f.evidence.text.endswith("in 24 hours.")
    assert text[f.evidence.start:f.evidence.end] == f.evidence.text
    assert f.value["match"] == "exact" and f.value["citations"]


def test_fuzzy_match_survives_ocr_typos():
    text = "Stomach bleeding warning: This product contains an NSA1D, which may cause severe stomach bleed1ng. The chance is higher if you are age 60 or older."
    f = [x for x in extract_warnings(text) if x.value["id"] == "stomach_bleeding_warning"]
    assert f and f[0].value["match"] == "fuzzy"


def test_shared_maoi_wording_is_disambiguated_by_ingredient():
    maoi = ("Do not use if you are now taking a prescription monoamine oxidase inhibitor (MAOI) (certain drugs "
            "for depression, psychiatric, or emotional conditions, or Parkinson's disease), or for 2 weeks after "
            "stopping the MAOI drug. If you do not know if your prescription drug contains an MAOI, ask a doctor "
            "or pharmacist before taking this product.")
    dm = ids(extract_warnings("Active ingredient: dextromethorphan hydrobromide\n" + maoi), "mandated")
    assert dm == {"maoi_dextromethorphan_warning"}
    pse = ids(extract_warnings("Active ingredient: pseudoephedrine hydrochloride\n" + maoi), "mandated")
    assert pse == {"maoi_nasal_decongestant_warning"}
    both = extract_warnings(maoi)  # no ingredient named: keep both, flagged ambiguous
    assert all(f.value["ambiguous"] for f in both if f.value["source"] == "mandated")


def test_missing_warning_detection():
    label = "Active ingredient: acetaminophen 500 mg. Keep out of reach of children."
    assert expected_warning_ids(label) == {"liver_warning"}
    assert missing_warning_ids(label) == {"liver_warning"}


def test_no_missing_when_warning_present():
    label = ("Active ingredient: acetaminophen 500 mg. Liver warning: This product contains acetaminophen. "
             "Severe liver damage may occur if you take more than 4,000 mg in 24 hours.")
    assert missing_warning_ids(label) == set()


@pytest.mark.parametrize("text,wid", [
    ("Ask a doctor before use if you have liver disease.", "ask_doctor_before_use"),
    ("Ask a doctor or pharmacist before use if you are taking a blood thinner.", "ask_doctor_before_use"),
    ("Stop use and ask a doctor if pain lasts more than 10 days.", "stop_use"),
    ("If pregnant or breast- feeding, ask a health professional before use.", "pregnancy_breastfeeding"),
    ("Keep out of reach of children.", "keep_out_of_reach"),
    ("In case of overdose, get medical help or call Poison Control (1-800-222-1222).", "overdose_poison_control"),
])
def test_heading_warnings(text, wid):
    assert wid in ids(extract_warnings(text), "heading")


def test_warning_none_found():
    assert extract_warnings("Active ingredient: ibuprofen 200 mg") == []


# -------------------------------------------------------------- age limits
def test_age_under_years_do_not_give():
    v = vals(extract_age_limits("Do not give to children under 12 years of age."))[0]
    assert v == {"kind": "under", "age_months": 144, "action": "do_not_use"}


def test_age_under_months():
    v = vals(extract_age_limits("Do not use in children under 6 months."))[0]
    assert v["age_months"] == 6 and v["kind"] == "under"


def test_age_at_least():
    v = vals(extract_age_limits("Adults and children 12 years and over: take 2 tablets."))[0]
    assert v["kind"] == "at_least" and v["age_months"] == 144 and v["action"] == "dosing_applies"


def test_age_range_exclusive_upper():
    v = vals(extract_age_limits("Children 6 to under 12 years: take 1 tablet."))[0]
    assert (v["kind"], v["min_age_months"], v["max_age_months"], v["max_exclusive"]) == ("range", 72, 144, True)


def test_age_range_hyphen():
    v = vals(extract_age_limits("Ages 4-11 years: 5 mL."))[0]
    assert v["kind"] == "range" and v["min_age_months"] == 48 and v["max_age_months"] == 132


def test_age_ask_doctor():
    v = vals(extract_age_limits("Children under 2 years: ask a doctor."))[0]
    assert v["action"] == "ask_doctor"


def test_age_no_match_for_dose_hours():
    assert extract_age_limits("Take every 4 to 6 hours.") == []


# ------------------------------------------------------------------ dosing
def test_dosing_basic():
    v = vals(extract_dosing("Adults and children 12 years and over: take 2 tablets every 4 to 6 hours."))[0]
    assert (v["dose_min"], v["dose_unit"], v["interval_hours_min"], v["interval_hours_max"]) == (2, "tablet", 4, 6)
    assert v["population"] == "adults and children 12 years and over"


def test_dosing_max_per_24h_not_mistaken_for_dose():
    v = vals(extract_dosing("Do not exceed 6 tablets in 24 hours."))[0]
    assert v["max_amount"] == 6 and v["max_unit"] == "tablet" and v["max_period_hours"] == 24
    assert "dose_min" not in v


def test_dosing_dose_range():
    v = vals(extract_dosing("Take 1 to 2 capsules with water."))[0]
    assert (v["dose_min"], v["dose_max"], v["dose_unit"]) == (1, 2, "capsule")


def test_dosing_teaspoon_and_ml():
    v = vals(extract_dosing("Children 6 to 11 years: give 1 teaspoonful (5 mL) every 6 hours."))[0]
    assert v["dose_unit"] == "teaspoon" and v["interval_hours_min"] == 6


def test_dosing_fraction_and_word_numbers():
    assert vals(extract_dosing("Take one tablet daily."))[0]["dose_min"] == 1
    v = vals(extract_dosing("Take 1/2 tablet every 8 hours."))[0]
    assert v["dose_min"] == 0.5


def test_dosing_ignores_strength_statements():
    assert extract_dosing("Each tablet contains 200 mg ibuprofen.") == []


# --------------------------------------------------------------- allergens
def _by(findings):
    return {(v["allergen"], v["status"]) for v in vals(findings)}


def test_allergen_contains_statement():
    assert _by(extract_allergens("Contains: milk, soy.")) >= {("milk", "present"), ("soy", "present")}


def test_allergen_negated():
    assert ("sulfites", "absent") in _by(extract_allergens("Contains no sulfites."))


def test_allergen_free_suffix():
    assert ("wheat", "absent") in _by(extract_allergens("Gluten-free."))


def test_allergen_milk_of_magnesia_not_milk():
    assert extract_allergens("Active ingredient: milk of magnesia 400 mg/5 mL") == []


def test_allergen_drug_allergy_warning():
    got = _by(extract_allergens("Do not use if you are allergic to aspirin or any other pain reliever."))
    assert ("aspirin", "allergy_warning") in got


def test_allergen_inactive_list_hits():
    got = _by(extract_allergens("Inactive ingredients: lactose, FD&C Yellow No. 5, sesame oil."))
    assert {("milk", "present"), ("tartrazine", "present"), ("sesame", "present")} <= got


def test_active_ingredient_is_not_an_allergy_warning():
    assert extract_allergens("Active ingredient: ibuprofen 200 mg") == []


# ----------------------------------------------------------------- extract_all
def test_extract_all_keys():
    assert set(extract_all("Keep out of reach of children.")) == {"warnings", "age_limits", "dosing", "allergens"}


# ------------------------------------------- real label snippets (when #23 lands)
FIXTURES = Path(__file__).parents[1] / "fixtures" / "labels"


def test_recall_on_label_snippets():
    """Fixture format: {"text": "...", "expected_warnings": ["liver_warning", ...]}"""
    files = sorted(FIXTURES.glob("*.json"))
    if not files:
        pytest.skip("no label snippet fixtures yet")
    expected = hit = 0
    misses = []
    for p in files:
        d = json.loads(p.read_text())
        found = ids(extract_warnings(d["text"]))
        for wid in d["expected_warnings"]:
            expected += 1
            if wid in found:
                hit += 1
            else:
                misses.append((p.name, wid))
    assert hit / expected >= 0.98, f"recall {hit/expected:.3f}; misses: {misses}"