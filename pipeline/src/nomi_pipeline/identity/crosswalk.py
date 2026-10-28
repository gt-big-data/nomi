"""Link OTC ingredient FDA ids (UNII) to RxNorm ids and name synonyms (NOMI-019)."""

import re
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

# RXNCONSO.RRF is pipe-delimited. These are the column positions we use.
_RXCUI, _SAB, _TTY, _CODE, _STR, _SUPPRESS = 0, 11, 12, 13, 14, 16
_MIN_COLUMNS = 17


@dataclass(frozen=True)
class RxnormTerm:
    """One name or code for an RxNorm concept."""

    rxcui: str
    sab: str
    tty: str
    code: str
    name: str


@dataclass(frozen=True)
class CrosswalkRow:
    """One link between an FDA ingredient id (UNII) and an RxNorm ingredient."""

    unii: str
    rxcui: str
    rxnorm_name: str
    synonyms: tuple[str, ...]


def normalize_name(name: str) -> str:
    """Lowercase a name and collapse punctuation and spaces so spellings compare equal."""
    return _NON_ALNUM.sub(" ", name.lower()).strip()


def parse_rxnconso(lines: Iterable[str]) -> Iterator[RxnormTerm]:
    """Yield the non-suppressed terms from RXNCONSO.RRF lines."""
    for line in lines:
        fields = line.rstrip("\n").split("|")
        if len(fields) < _MIN_COLUMNS or fields[_SUPPRESS] != "N":
            continue
        yield RxnormTerm(
            rxcui=fields[_RXCUI],
            sab=fields[_SAB],
            tty=fields[_TTY],
            code=fields[_CODE],
            name=fields[_STR],
        )


def _is_unii(code: str) -> bool:
    return len(code) == 10 and code.isalnum()


def build_crosswalk(terms: Iterable[RxnormTerm]) -> list[CrosswalkRow]:
    """Link UNIIs to RxNorm ingredients (IN terms), with normalized name synonyms."""
    names: dict[str, str] = {}
    synonyms: dict[str, set[str]] = defaultdict(set)
    uniis: dict[str, set[str]] = defaultdict(set)

    for term in terms:
        if term.sab == "RXNORM" and term.tty == "IN":
            names[term.rxcui] = term.name
        if term.sab == "MTHSPL" and _is_unii(term.code):
            uniis[term.rxcui].add(term.code)
        synonyms[term.rxcui].add(normalize_name(term.name))

    rows = [
        CrosswalkRow(unii, rxcui, name, tuple(sorted(synonyms[rxcui])))
        for rxcui, name in names.items()
        for unii in uniis.get(rxcui, set())
    ]
    return sorted(rows, key=lambda row: (row.unii, row.rxcui))
