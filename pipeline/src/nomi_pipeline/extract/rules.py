"""Rule-based extraction of warnings, age limits, dosing facts and allergens
from drug-label text. Every finding carries the evidence span it came from.

Field names (agree with the #32 LLM-extraction owner before merging):
    warnings, age_limits, dosing, allergens
Warnings are keyed by the ids in knowledge/mandated_warnings.yaml (#18).
"""
from __future__ import annotations

import difflib
import json
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator

# --------------------------------------------------------------------------
# Shared types and helpers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Evidence:
    text: str
    start: int  # character offsets into the original label text
    end: int


@dataclass(frozen=True)
class Finding:
    field: str
    value: dict
    evidence: Evidence

    def to_dict(self) -> dict:
        return asdict(self)


_SPLIT = re.compile(r"(?<!No\.)(?<!no\.)(?<=[.;!?])\s+|\n+|\s*•\s*")


def _segments(text: str) -> Iterator[Evidence]:
    """Split label text into sentence-ish segments, keeping offsets."""
    pos = 0
    bounds = [(m.start(), m.end()) for m in _SPLIT.finditer(text)]
    for s, e in bounds + [(len(text), len(text))]:
        raw = text[pos:s]
        stripped = raw.strip()
        if stripped:
            start = pos + (len(raw) - len(raw.lstrip()))
            yield Evidence(stripped, start, start + len(stripped))
        pos = e


def _norm(s: str) -> str:
    """Lowercase and tidy OCR noise. Used for matching only, never for offsets."""
    s = s.lower().replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
    s = re.sub(r"-\s+", "-", s)  # "breast- feeding"
    return re.sub(r"\s+", " ", s)


_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
          "seven": 7, "eight": 8, "nine": 9, "ten": 10, "twelve": 12,
          "½": 0.5, "¼": 0.25, "¾": 0.75}
_NUM = r"(?:\d+\s*/\s*\d+|\d+(?:\.\d+)?|" + "|".join(_WORDS) + r")"
_RANGE_SEP = r"\s*(?:-|to|or)\s*"


def _num(tok: str) -> float:
    tok = tok.strip()
    if tok in _WORDS:
        return _WORDS[tok]
    if "/" in tok:
        a, b = tok.split("/")
        return float(a) / float(b)
    return float(tok)


def _clean(x: float) -> float | int:
    return int(x) if float(x).is_integer() else x


# --------------------------------------------------------------------------
# Warnings
#
# Two sources, both returned from extract_warnings():
#   source="mandated"  wording variants from the #18 registry (mandated_warnings.yaml),
#                      matched across sentence boundaries, tolerant of OCR noise.
#   source="heading"   generic Drug Facts statements (not in the registry).
# --------------------------------------------------------------------------

DEFAULT_REGISTRY = Path(__file__).parents[3] / "knowledge" / "mandated_warnings.yaml"

_CHAR_MAP = {"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
             "\u2013": "-", "\u2014": "-"}


@dataclass(frozen=True)
class WarningSpec:
    id: str
    dimension: str
    ingredients: tuple[str, ...]
    variants: tuple[str, ...]
    citations: tuple[str, ...]


def _scalar(v: str) -> str:
    v = v.strip()
    if v.startswith('"') and v.endswith('"') and len(v) >= 2:
        return json.loads(v)
    if v.startswith("'") and v.endswith("'") and len(v) >= 2:
        return v[1:-1].replace("''", "'")
    return v


def _parse_simple_registry(text: str) -> dict:
    """Minimal parser for the registry's YAML subset (a list of items with scalar
    keys and lists of scalars), used when PyYAML isn't installed."""
    items: list[dict] = []
    item_indent: int | None = None
    cur: dict | None = None
    key: str | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#") or line.strip() == "warnings:":
            continue
        indent = len(line) - len(line.lstrip())
        body = line.strip()
        if body.startswith("- "):
            if item_indent is None:
                item_indent = indent
            if indent == item_indent:  # new registry item: "- id: foo"
                cur = {}
                items.append(cur)
                body = body[2:].strip()
            else:  # list value under the current key
                assert cur is not None and key is not None, f"bad registry line: {raw!r}"
                cur.setdefault(key, []).append(_scalar(body[2:]))
                continue
        k, _, v = body.partition(":")
        assert cur is not None, f"bad registry line: {raw!r}"
        key = k.strip()
        if v.strip():
            cur[key] = _scalar(v)
        else:
            cur.setdefault(key, [])
    return {"warnings": items}


def load_registry(path: str | Path | None = None) -> list[WarningSpec]:
    text = Path(path or DEFAULT_REGISTRY).read_text(encoding="utf-8")
    try:
        import yaml  # PyYAML, optional

        data = yaml.safe_load(text)
    except ImportError:
        data = _parse_simple_registry(text)
    return [
        WarningSpec(
            id=w["id"],
            dimension=w.get("dimension", ""),
            ingredients=tuple(i.strip().lower() for i in w.get("ingredients", [])),
            variants=tuple(w["wording_variants"]),
            citations=tuple(w.get("citations", [])),
        )
        for w in data["warnings"]
    ]


@lru_cache(maxsize=1)
def _default_registry() -> tuple[WarningSpec, ...]:
    return tuple(load_registry())


def _normalize(original: str) -> tuple[str, list[int]]:
    """Lowercase, fold curly quotes, collapse whitespace, rejoin 'flu- like'.

    Returns (normalized, idx) where idx[i] is the offset in `original` of
    normalized[i], so matches can be mapped back to evidence spans.
    """
    out: list[str] = []
    idx: list[int] = []
    prev_space = True
    for i, ch in enumerate(original):
        ch = _CHAR_MAP.get(ch, ch)
        if ch.isspace():
            if not prev_space and out[-1] != "-":
                out.append(" ")
                idx.append(i)
            prev_space = True
            continue
        out.append(ch.lower())
        idx.append(i)
        prev_space = False
    while out and out[-1] == " ":
        out.pop()
        idx.pop()
    return "".join(out), idx


def _norm_text(s: str) -> str:
    return _normalize(s)[0]


def _tokens(s: str) -> list[tuple[int, int]]:
    return [m.span() for m in re.finditer(r"\S+", s)]


def _find_exact(nt: str, nv: str) -> Iterator[tuple[int, int, float]]:
    pos = nt.find(nv)
    while pos != -1:
        yield pos, pos + len(nv), 1.0
        pos = nt.find(nv, pos + len(nv))


def _find_fuzzy(nt: str, nv: str, threshold: float) -> Iterator[tuple[int, int, float]]:
    """Token-window fuzzy search (difflib). Only windows starting at a token that
    resembles the variant's first token are scored, which keeps this fast."""
    toks = _tokens(nt)
    vtoks = nv.split()
    k = len(vtoks)
    if not toks or k == 0:
        return
    first = vtoks[0]
    best: list[tuple[float, int, int]] = []
    for i, (s0, _) in enumerate(toks):
        cand = nt[s0:toks[i][1]]
        if difflib.SequenceMatcher(None, cand, first).ratio() < 0.7:
            continue
        for size in (k - 1, k, k + 1):
            j = i + size
            if size < 1 or j > len(toks):
                continue
            window = nt[s0:toks[j - 1][1]]
            sm = difflib.SequenceMatcher(None, window, nv, autojunk=False)
            if sm.real_quick_ratio() < threshold or sm.quick_ratio() < threshold:
                continue
            r = sm.ratio()
            if r >= threshold:
                best.append((r, s0, toks[j - 1][1]))
    best.sort(reverse=True)
    taken: list[tuple[int, int]] = []
    for r, s, e in best:
        if all(e <= a or s >= b for a, b in taken):
            taken.append((s, e))
            yield s, e, r


_SENT_END = re.compile(r"[.!?](?=\s|$)|\n")


def _extend_to_sentence_end(original: str, end: int) -> int:
    """Registry variants are often truncated mid-sentence; extend the evidence
    to the end of that sentence so it carries the rest of the statement."""
    if end > 0 and original[end - 1] in ".!?":
        return end
    m = _SENT_END.search(original, end)
    return m.end() if m else len(original)


def ingredients_in_text(text: str, registry: Iterable[WarningSpec] | None = None) -> set[str]:
    nt = _norm_text(text)
    names = {i for spec in (registry or _default_registry()) for i in spec.ingredients}
    return {i for i in names if re.search(rf"\b{re.escape(i)}\b", nt)}


def extract_mandated_warnings(
    text: str,
    registry: Iterable[WarningSpec] | None = None,
    fuzzy_threshold: float = 0.9,
) -> list[Finding]:
    specs = list(registry) if registry is not None else list(_default_registry())
    nt, idx = _normalize(text)
    present = ingredients_in_text(text, specs)

    # (norm_start, norm_end) -> list of (spec, score, mode)
    hits: dict[tuple[int, int], list[tuple[WarningSpec, float, str]]] = {}
    for spec in specs:
        for variant in spec.variants:
            nv = _norm_text(variant)
            matches = list(_find_exact(nt, nv))
            mode = "exact"
            if not matches:
                matches, mode = list(_find_fuzzy(nt, nv, fuzzy_threshold)), "fuzzy"
            for s, e, score in matches:
                hits.setdefault((s, e), []).append((spec, score, mode))

    # Collapse spec duplicates per span, then disambiguate specs that share wording
    # (e.g. the MAOI text appears under both dextromethorphan and nasal decongestants).
    findings: list[Finding] = []
    seen: set[tuple[str, int, int]] = set()
    for (s, e), items in sorted(hits.items()):
        by_id = {}
        for spec, score, mode in items:
            if spec.id not in by_id or score > by_id[spec.id][1]:
                by_id[spec.id] = (spec, score, mode)
        cands = list(by_id.values())
        ambiguous = False
        if len(cands) > 1:
            narrowed = [c for c in cands if present & set(c[0].ingredients)]
            ambiguous = len(narrowed) != 1
            cands = narrowed or cands
        o_start = idx[s]
        o_end = _extend_to_sentence_end(text, idx[e - 1] + 1)
        ev = Evidence(text[o_start:o_end].strip(), o_start, o_end)
        for spec, score, mode in cands:
            key = (spec.id, o_start, o_end)
            if key in seen:
                continue
            seen.add(key)
            findings.append(Finding("warnings", {
                "id": spec.id,
                "source": "mandated",
                "dimension": spec.dimension,
                "match": mode,
                "score": round(score, 3),
                "ambiguous": ambiguous,
                "ingredients_in_label": sorted(present & set(spec.ingredients)),
                "citations": list(spec.citations),
            }, ev))
    return findings


def expected_warning_ids(text: str, registry: Iterable[WarningSpec] | None = None) -> set[str]:
    """Warnings the label should carry, judged by which registry ingredients it names.
    A heuristic: use it to flag labels where a mandated warning looks missing."""
    specs = list(registry) if registry is not None else list(_default_registry())
    present = ingredients_in_text(text, specs)
    return {s.id for s in specs if present & set(s.ingredients)}


def missing_warning_ids(text: str, registry: Iterable[WarningSpec] | None = None) -> set[str]:
    found = {f.value["id"] for f in extract_mandated_warnings(text, registry)}
    return expected_warning_ids(text, registry) - found


HEADING_PATTERNS: dict[str, str] = {
    "do_not_use": r"\bdo not use\b",
    "ask_doctor_before_use": r"\bask a doctor (?:or pharmacist )?before use\b",
    "when_using": r"\bwhen using this product\b",
    "stop_use": r"\bstop use and ask a doctor\b",
    "pregnancy_breastfeeding": r"\bif pregnant or breast-?feeding\b",
    "keep_out_of_reach": r"\bkeep out of reach of children\b",
    "overdose_poison_control": r"\boverdose\b|\bpoison control\b|1-?800-?222-?1222",
    "alcohol_warning": r"\balcohol warning\b|\b3 or more alcoholic drinks\b",
    "sore_throat_warning": r"\bsore throat warning\b",
}
_HEADING_RE = {k: re.compile(v) for k, v in HEADING_PATTERNS.items()}


def extract_heading_warnings(text: str) -> list[Finding]:
    out = []
    for seg in _segments(text):
        n = _norm(seg.text)
        for wid, rx in _HEADING_RE.items():
            if rx.search(n):
                out.append(Finding("warnings", {"id": wid, "source": "heading"}, seg))
    return out


def extract_warnings(
    text: str,
    registry: Iterable[WarningSpec] | None = None,
    fuzzy_threshold: float = 0.9,
) -> list[Finding]:
    found = extract_mandated_warnings(text, registry, fuzzy_threshold) + extract_heading_warnings(text)
    return sorted(found, key=lambda f: (f.evidence.start, f.value["id"]))


# --------------------------------------------------------------------------
# Age limits
# --------------------------------------------------------------------------

_UNIT = r"(years?|yrs?|months?|mos?)"
_AGE_RANGE = re.compile(
    rf"(?:ages?\s+)?({_NUM}){_RANGE_SEP}(under\s+)?({_NUM})\s*{_UNIT}")
_AGE_UNDER = re.compile(rf"(?:under|younger than|less than)\s+({_NUM})\s*{_UNIT}")
_AGE_AT_LEAST = re.compile(
    rf"({_NUM})\s*{_UNIT}(?:\s+of age)?\s*(?:and over|and older|or older|or over|\+)")


def _months(n: str, unit: str) -> int:
    v = _num(n)
    return int(round(v * (1 if unit.startswith("m") else 12)))


def _age_action(n: str) -> str:
    if re.search(r"\bdo not (?:use|give)\b|\bshould not\b|\bnot for\b|\bnot recommended\b", n):
        return "do_not_use"
    if re.search(r"\bask a doctor\b|\bconsult\b|\bdoctor\b", n):
        return "ask_doctor"
    if re.search(r"\btake\b|\bgive\b|\bdose\b|\badults and children\b|\bchildren\b.*:", n):
        return "dosing_applies"
    return "unspecified"


def extract_age_limits(text: str) -> list[Finding]:
    out = []
    for seg in _segments(text):
        n = _norm(seg.text)
        action = _age_action(n)
        taken: list[tuple[int, int]] = []

        def free(m: re.Match) -> bool:
            return all(m.end() <= a or m.start() >= b for a, b in taken)

        for m in _AGE_RANGE.finditer(n):
            if not free(m):
                continue
            taken.append(m.span())
            out.append(Finding("age_limits", {
                "kind": "range",
                "min_age_months": _months(m.group(1), m.group(4)),
                "max_age_months": _months(m.group(3), m.group(4)),
                "max_exclusive": bool(m.group(2)),
                "action": action}, seg))
        for m in _AGE_UNDER.finditer(n):
            if free(m):
                taken.append(m.span())
                out.append(Finding("age_limits", {
                    "kind": "under", "age_months": _months(m.group(1), m.group(2)),
                    "action": action}, seg))
        for m in _AGE_AT_LEAST.finditer(n):
            if free(m):
                taken.append(m.span())
                out.append(Finding("age_limits", {
                    "kind": "at_least", "age_months": _months(m.group(1), m.group(2)),
                    "action": action}, seg))
    return out


# --------------------------------------------------------------------------
# Dosing
# --------------------------------------------------------------------------

_DOSE_UNITS = {
    "tablet": "tablet", "caplet": "caplet", "capsule": "capsule",
    "softgel": "softgel", "lozenge": "lozenge", "packet": "packet",
    "teaspoonful": "teaspoon", "teaspoon": "teaspoon", "tsp": "teaspoon",
    "tablespoonful": "tablespoon", "tablespoon": "tablespoon", "tbsp": "tablespoon",
    "ml": "mL", "mg": "mg", "mcg": "mcg", "drop": "drop",
}
_UNIT_RE = r"(" + "|".join(sorted(_DOSE_UNITS, key=len, reverse=True)) + r")s?\b"
_AMOUNT = re.compile(rf"\b({_NUM})(?:{_RANGE_SEP}({_NUM}))?\s*{_UNIT_RE}")
_INTERVAL = re.compile(rf"\bevery\s+({_NUM})(?:{_RANGE_SEP}({_NUM}))?\s*hours?")
_MAX = re.compile(
    r"(?:do not (?:exceed|take more than)|not to exceed|no more than|maximum(?: daily dose)?(?: of)?)"
    rf"\s+({_NUM})\s*{_UNIT_RE}"
    r"(?:\s*(?:in|per|within|a)\s*(?:24\s*hours?|24-hour period|day))?")
_DOSE_VERB = re.compile(r"\b(?:take|give|chew|dissolve|swallow|administer|dose|use)\b")
_POPULATION = re.compile(r"^(.*?(?:adults?|children|ages?|years).*?):")


def extract_dosing(text: str) -> list[Finding]:
    out = []
    for seg in _segments(text):
        n = _norm(seg.text)
        value: dict = {}

        mx = _MAX.search(n)
        if mx:
            value["max_amount"] = _clean(_num(mx.group(1)))
            value["max_unit"] = _DOSE_UNITS[mx.group(2)]
            value["max_period_hours"] = 24
            n_dose = n[:mx.start()] + " " * (mx.end() - mx.start()) + n[mx.end():]
        else:
            n_dose = n

        iv = _INTERVAL.search(n_dose)
        if iv:
            lo = _num(iv.group(1))
            hi = _num(iv.group(2)) if iv.group(2) else lo
            value["interval_hours_min"], value["interval_hours_max"] = _clean(lo), _clean(hi)

        am = _AMOUNT.search(n_dose)
        if am and (iv or mx or _DOSE_VERB.search(n_dose)):
            lo = _num(am.group(1))
            hi = _num(am.group(2)) if am.group(2) else lo
            value["dose_min"], value["dose_max"] = _clean(lo), _clean(hi)
            value["dose_unit"] = _DOSE_UNITS[am.group(3)]

        if value:
            pop = _POPULATION.match(n)
            value["population"] = pop.group(1).strip() if pop else None
            out.append(Finding("dosing", value, seg))
    return out


# --------------------------------------------------------------------------
# Allergens
# --------------------------------------------------------------------------

_FOOD_TERMS = {
    "milk": r"milk(?!\s+of\s+magnesia)|lactose|casein|whey",
    "egg": r"eggs?",
    "fish": r"fish",
    "shellfish": r"shellfish|crustaceans?|shrimp",
    "tree_nuts": r"tree nuts?|almonds?|walnuts?|cashews?|pecans?",
    "peanut": r"peanuts?",
    "wheat": r"wheat|gluten",
    "soy": r"soy|soya|soybeans?",
    "sesame": r"sesame",
    "sulfites": r"sulfites?|sulphites?|metabisulfite",
    "tartrazine": r"tartrazine|fd&c yellow (?:no\.? ?)?5",
    "phenylalanine": r"phenylalanine",
}
_DRUG_TERMS = {
    "aspirin": r"aspirin",
    "nsaids": r"nsaids?|ibuprofen|naproxen",
    "sulfa": r"sulfa",
    "acetaminophen": r"acetaminophen",
}
_NEGATOR = re.compile(r"\b(?:free (?:of|from)|does not contain|do not contain|contains? no|no(?![.\w])|without|not made with)\b(?! more)")
_ALLERGIC_TO = re.compile(r"allergic to\b")


def _term_re(d: dict[str, str]) -> dict[str, re.Pattern]:
    return {k: re.compile(rf"\b(?:{v})\b") for k, v in d.items()}


_FOOD_RE, _DRUG_RE = _term_re(_FOOD_TERMS), _term_re(_DRUG_TERMS)


def extract_allergens(text: str) -> list[Finding]:
    out = []
    for seg in _segments(text):
        n = _norm(seg.text)
        seen: set[tuple[str, str]] = set()
        for name, rx in _FOOD_RE.items():
            for m in rx.finditer(n):
                window = n[max(0, m.start() - 40):m.start()]
                negated = bool(_NEGATOR.search(window)) or bool(re.match(r"\W{0,2}free\b", n[m.end():]))
                status = "absent" if negated else "present"
                if (name, status) not in seen:
                    seen.add((name, status))
                    out.append(Finding("allergens", {"allergen": name, "status": status}, seg))
        at = _ALLERGIC_TO.search(n)
        if at:
            tail = n[at.end():]
            for name, rx in _DRUG_RE.items():
                if rx.search(tail) and (name, "allergy_warning") not in seen:
                    seen.add((name, "allergy_warning"))
                    out.append(Finding("allergens", {"allergen": name, "status": "allergy_warning"}, seg))
    return out


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def extract_all(text: str) -> dict[str, list[Finding]]:
    return {
        "warnings": extract_warnings(text),
        "age_limits": extract_age_limits(text),
        "dosing": extract_dosing(text),
        "allergens": extract_allergens(text),
    }