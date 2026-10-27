"""Rule-based Drug Facts extraction (NOMI-031).

Pulls fields with standard FDA wording from label text: mandated warnings, age limits, maximum
daily dose and allergens. Every fact keeps the exact label text it came from.
"""

import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

SCANNED_FIELDS = (
    "boxed_warning",
    "warnings",
    "do_not_use",
    "ask_doctor",
    "ask_doctor_or_pharmacist",
    "stop_use",
    "pregnancy_or_breast_feeding",
    "dosage_and_administration",
    "inactive_ingredient",
    "spl_unclassified_section",
)
DOSAGE_FIELDS = ("dosage_and_administration", "spl_unclassified_section", "text")
INACTIVE_FIELDS = ("inactive_ingredient", "spl_unclassified_section", "text")

Dimension = Literal[
    "liver",
    "gi_bleeding",
    "cardiovascular_bp",
    "kidney",
    "anticholinergic_cognitive",
    "sedation_falls",
    "serotonergic_interactions",
    "anticoagulant_bleeding",
    "pediatric",
    "rebound_overuse",
    "pregnancy_lactation",
    "duplicate_dosing",
    "excipients",
    "local_skin",
    "efficacy_evidence",
]


class Evidence(BaseModel):
    field: str
    item_index: int
    start: int
    end: int
    text: str


class WarningFact(BaseModel):
    warning_id: str
    dimension: Dimension | None
    evidence: Evidence


Action = Literal["do_not_use", "ask_doctor"]


class AgeLimit(BaseModel):
    """Children younger than `under_years` (and at least `min_years`, if set) must not use or must ask a doctor."""

    action: Action
    min_years: int | None
    under_years: int
    evidence: Evidence


class MaxDailyDose(BaseModel):
    amount: int
    unit: str
    evidence: Evidence


class Allergen(BaseModel):
    allergen: str
    kind: Literal["allergy_alert", "phenylketonuria", "dye"]
    evidence: Evidence


class LabelFacts(BaseModel):
    warnings: list[WarningFact]
    age_limits: list[AgeLimit]
    max_daily_doses: list[MaxDailyDose]
    allergens: list[Allergen]

    def warning_ids(self) -> set[str]:
        return {fact.warning_id for fact in self.warnings}


@dataclass(frozen=True)
class WarningRule:
    warning_id: str
    dimension: Dimension | None
    pattern: re.Pattern[str]


def _rx(pattern: str) -> re.Pattern[str]:
    return re.compile(pattern.replace(" ", r"\s+"), re.IGNORECASE)


_SEP = r"\W*"
NSAIDS = r"(?:aspirin|ibuprofen|naproxen(?: sodium)?|ketoprofen|carbaspirin calcium|(?:choline|magnesium|sodium) salicylate)"

WARNING_RULES: tuple[WarningRule, ...] = (
    WarningRule(
        "liver_warning",
        "liver",
        _rx(rf"liver (?:damage )?warning{_SEP} this product contains acetaminophen"),
    ),
    WarningRule(
        "stomach_bleeding_warning",
        "gi_bleeding",
        _rx(rf"stomach bleeding warning{_SEP} this product contains an? NSAID"),
    ),
    WarningRule(
        "heart_attack_and_stroke_warning",
        "cardiovascular_bp",
        _rx(rf"heart attack and stroke warning{_SEP} NSAIDs?"),
    ),
    WarningRule(
        "nsaid_allergy_alert",
        None,
        _rx(rf"allergy alert{_SEP} {NSAIDS} may cause a severe allergic reaction"),
    ),
    WarningRule(
        "acetaminophen_skin_reaction_alert",
        None,
        _rx(rf"allergy alert{_SEP} (?:acetaminophen )?may cause severe skin reactions"),
    ),
    WarningRule(
        "reyes_syndrome_warning",
        "pediatric",
        _rx(rf"reye['’]?s syndrome{_SEP} children and teenagers who have or are recovering"),
    ),
    WarningRule(
        "diphenhydramine_duplicate_use_warning",
        "duplicate_dosing",
        _rx(r"with any other product containing diphenhydramine, even one used on skin"),
    ),
    WarningRule(
        "acetaminophen_duplicate_use_warning",
        "duplicate_dosing",
        _rx(r"with any other (?:drug|product) containing acetaminophen"),
    ),
    WarningRule(
        "maoi_warning",
        "serotonergic_interactions",
        _rx(r"monoamine oxidase inhibitor \(MAOI\)"),
    ),
    WarningRule(
        "nsaid_pregnancy_warning",
        "pregnancy_lactation",
        _rx(rf"important not to use {NSAIDS} during the last 3 months of pregnancy"),
    ),
    WarningRule(
        "sore_throat_warning",
        None,
        _rx(rf"sore throat warning{_SEP} if sore throat is severe"),
    ),
    WarningRule(
        "phenylketonuria_warning",
        "excipients",
        _rx(rf"phenylketonurics{_SEP} contains phenylalanine"),
    ),
)

_YEARS = r"(?:years?|yrs?)(?: of age)?"
_ACTION = r"(?P<action>do not use(?! unless)|do not give(?! unless)|ask a doctor|consult a doctor|do not use unless directed by a doctor)"
AGE_RANGE = _rx(
    rf"children (?P<low>\d+) to (?P<under>under )?(?P<high>\d+) {_YEARS}{_SEP} {_ACTION}"
)
AGE_UNDER = _rx(rf"(?:children )?under (?P<high>\d+) {_YEARS}{_SEP} {_ACTION}")
AGE_DO_NOT_USE = _rx(rf"do not use{_SEP} (?:in|for) children under (?P<high>\d+) {_YEARS}")

DOSE_UNITS = r"caplets?|tablets?|capsules?|softgels?|gelcaps?|liquid ?gels?|doses?|times|mL|lozenges?|pieces?|chews?|packets?|teaspoons?|tablespoons?|sprays?|drops?"
MAX_DOSE = _rx(
    rf"(?:do not|not to) (?:take|exceed|give|use)(?: more than)? (?P<amount>\d+) (?P<unit>{DOSE_UNITS})"
    r"(?: \([^)]*\))? (?:in|per) (?:a |any )?24(?:-| )?h(?:ou)?rs?"
)

ALLERGY_ALERT = re.compile(
    r"(?:(?P<before>[a-z]+)\s+)?allergy\s+alert\W*"
    r"(?:contains\s+(?P<contains>salicylates?)|(?:(?P<after>[a-z]+(?:\s+[a-z]+)?)\s+)?may\s+cause)",
    re.IGNORECASE,
)
PHENYLALANINE = _rx(rf"phenylketonurics{_SEP} contains phenylalanine")
DYES = _rx(r"FD&C yellow (?:no\.?|#) ?(?P<number>[56])\b|tartrazine")


def _texts(label: Mapping[str, object], fields: Iterable[str]) -> Iterable[tuple[str, int, str]]:
    for field in fields:
        value = label.get(field)
        items: Sequence[object] = [value] if isinstance(value, str) else []
        if isinstance(value, list):
            items = value
        for index, item in enumerate(items):
            if isinstance(item, str) and item.strip():
                yield field, index, item


def _evidence(field: str, index: int, match: re.Match[str]) -> Evidence:
    return Evidence(
        field=field, item_index=index, start=match.start(), end=match.end(), text=match.group(0)
    )


def extract_warnings(label: Mapping[str, object]) -> list[WarningFact]:
    found: dict[str, WarningFact] = {}
    for field, index, text in _texts(label, (*SCANNED_FIELDS, "text")):
        for rule in WARNING_RULES:
            if rule.warning_id in found:
                continue
            match = rule.pattern.search(text)
            if match:
                found[rule.warning_id] = WarningFact(
                    warning_id=rule.warning_id,
                    dimension=rule.dimension,
                    evidence=_evidence(field, index, match),
                )
    return [found[rule.warning_id] for rule in WARNING_RULES if rule.warning_id in found]


def _action(raw: str) -> Action:
    raw = raw.lower()
    if "unless" in raw or "doctor" in raw:
        return "ask_doctor"
    return "do_not_use"


def extract_age_limits(label: Mapping[str, object]) -> list[AgeLimit]:
    limits: dict[tuple[Action, int | None, int], AgeLimit] = {}
    for field, index, text in _texts(label, (*SCANNED_FIELDS, "text")):
        spans: list[tuple[int, int]] = []
        for match in AGE_RANGE.finditer(text):
            high = int(match["high"])
            under = high if match["under"] else high + 1
            key: tuple[Action, int | None, int] = (
                _action(match["action"]),
                int(match["low"]),
                under,
            )
            limits.setdefault(
                key,
                AgeLimit(
                    action=key[0],
                    min_years=key[1],
                    under_years=under,
                    evidence=_evidence(field, index, match),
                ),
            )
            spans.append(match.span())
        for match in AGE_UNDER.finditer(text):
            if any(start <= match.start() < end for start, end in spans):
                continue
            key = (_action(match["action"]), None, int(match["high"]))
            limits.setdefault(
                key,
                AgeLimit(
                    action=key[0],
                    min_years=None,
                    under_years=key[2],
                    evidence=_evidence(field, index, match),
                ),
            )
        for match in AGE_DO_NOT_USE.finditer(text):
            key = ("do_not_use", None, int(match["high"]))
            limits.setdefault(
                key,
                AgeLimit(
                    action="do_not_use",
                    min_years=None,
                    under_years=key[2],
                    evidence=_evidence(field, index, match),
                ),
            )
    return sorted(limits.values(), key=lambda limit: (limit.under_years, limit.min_years or 0))


def _unit(raw: str) -> str:
    unit = re.sub(r"\s+", "", raw.lower())
    if unit in {"times", "ml"}:
        return "doses" if unit == "times" else "mL"
    return unit if unit.endswith("s") else unit + "s"


def extract_max_daily_doses(label: Mapping[str, object]) -> list[MaxDailyDose]:
    doses: dict[tuple[int, str], MaxDailyDose] = {}
    for field, index, text in _texts(label, DOSAGE_FIELDS):
        for match in MAX_DOSE.finditer(text):
            key = (int(match["amount"]), _unit(match["unit"]))
            doses.setdefault(
                key,
                MaxDailyDose(amount=key[0], unit=key[1], evidence=_evidence(field, index, match)),
            )
    return list(doses.values())


def extract_allergens(label: Mapping[str, object]) -> list[Allergen]:
    allergens: dict[str, Allergen] = {}
    for field, index, text in _texts(label, (*SCANNED_FIELDS, "text")):
        for match in ALLERGY_ALERT.finditer(text):
            name = match["contains"] or match["after"] or match["before"]
            if not name or name.lower() in {"nsaid", "this", "product"}:
                name = match["before"]
            if name:
                name = name.lower().rstrip("s") if match["contains"] else name.lower()
                allergens.setdefault(
                    name,
                    Allergen(
                        allergen=name, kind="allergy_alert", evidence=_evidence(field, index, match)
                    ),
                )
        for match in PHENYLALANINE.finditer(text):
            allergens.setdefault(
                "phenylalanine",
                Allergen(
                    allergen="phenylalanine",
                    kind="phenylketonuria",
                    evidence=_evidence(field, index, match),
                ),
            )
    for field, index, text in _texts(label, INACTIVE_FIELDS):
        for match in DYES.finditer(text):
            name = f"FD&C Yellow No. {match['number'] or 5}"
            allergens.setdefault(
                name, Allergen(allergen=name, kind="dye", evidence=_evidence(field, index, match))
            )
    return list(allergens.values())


def extract(label: Mapping[str, object]) -> LabelFacts:
    """Extract facts from an openFDA label record (fields are lists of strings) or `{"text": ...}`."""
    return LabelFacts(
        warnings=extract_warnings(label),
        age_limits=extract_age_limits(label),
        max_daily_doses=extract_max_daily_doses(label),
        allergens=extract_allergens(label),
    )


def extract_text(text: str) -> LabelFacts:
    return extract({"text": [text]})
