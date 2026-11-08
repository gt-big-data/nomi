"""Find FDA-mandated OTC warnings in label text (NOMI-017; used by the rule extractor, NOMI-031).

A warning is found when any of its wording variants appears in the label text after both are
normalized, so headings with or without a colon, bullets and curly quotes don't matter.
"""

from __future__ import annotations

import re
import unicodedata
from functools import cache
from pathlib import Path
from typing import Any

import yaml

CATALOGUE = Path(__file__).resolve().parents[3] / "knowledge" / "mandated_warnings.yaml"


@cache
def load_catalogue(path: Path = CATALOGUE) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = yaml.safe_load(path.read_text(encoding="utf-8"))["warnings"]
    return warnings


def normalize(text: str) -> str:
    """Lowercase, drop accents, straighten quotes, and keep only letters, digits and apostrophes."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().replace("’", "'").replace("‘", "'")
    return " ".join(re.sub(r"[^a-z0-9']+", " ", text).split())


def find_warnings(text: str, catalogue: list[dict[str, Any]] | None = None) -> set[str]:
    """Ids of the catalogued warnings whose wording appears in text."""
    # A variant must start at a word, so "liver" can't match inside "deliver". It may end inside
    # one, so "reaction" still matches "reactions".
    label = f" {normalize(text)}"
    if catalogue is None:
        catalogue = load_catalogue()
    return {
        w["id"]
        for w in catalogue
        if any(f" {normalize(v)}" in label for v in w["wording_variants"])
    }
