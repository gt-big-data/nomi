"""Link OTC ingredient FDA ids (UNII) to RxNorm ids and name synonyms (NOMI-019)."""

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_name(name: str) -> str:
    """Lowercase a name and collapse punctuation and spaces so spellings compare equal."""
    return _NON_ALNUM.sub(" ", name.lower()).strip()
