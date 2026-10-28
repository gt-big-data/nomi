from nomi_pipeline.identity.crosswalk import (
    CrosswalkRow,
    RxnormTerm,
    build_crosswalk,
    normalize_name,
    parse_rxnconso,
)


def make_line(rxcui: str, sab: str, tty: str, code: str, name: str, suppress: str = "N") -> str:
    """Build a fake RXNCONSO.RRF line with the real column positions."""
    fields = [""] * 18
    fields[0] = rxcui
    fields[11] = sab
    fields[12] = tty
    fields[13] = code
    fields[14] = name
    fields[16] = suppress
    return "|".join(fields) + "|"


def test_normalize_name_ignores_case_and_punctuation() -> None:
    assert normalize_name("Acetaminophen") == "acetaminophen"
    assert normalize_name("  ACETAMINOPHEN, ") == "acetaminophen"
    assert normalize_name("Alpha-Lipoic Acid") == "alpha lipoic acid"
    assert normalize_name("Aspirin (Acetylsalicylic Acid)") == "aspirin acetylsalicylic acid"


def test_parse_rxnconso_reads_fields() -> None:
    lines = [make_line("161", "RXNORM", "IN", "161", "Acetaminophen")]

    assert list(parse_rxnconso(lines)) == [
        RxnormTerm(rxcui="161", sab="RXNORM", tty="IN", code="161", name="Acetaminophen")
    ]


def test_parse_rxnconso_skips_suppressed_and_short_lines() -> None:
    lines = [
        make_line("161", "RXNORM", "IN", "161", "Acetaminophen"),
        make_line("999", "RXNORM", "IN", "999", "Old Name", suppress="O"),
        "not|a|real|line",
    ]

    terms = list(parse_rxnconso(lines))

    assert [term.rxcui for term in terms] == ["161"]


def test_build_crosswalk_links_unii_to_rxcui_with_synonyms() -> None:
    lines = [
        make_line("161", "RXNORM", "IN", "161", "Acetaminophen"),
        make_line("161", "RXNORM", "SY", "161", "Paracetamol"),
        make_line("161", "MTHSPL", "SU", "362O9ITL9D", "ACETAMINOPHEN"),
        make_line("5640", "RXNORM", "IN", "5640", "Ibuprofen"),
    ]

    rows = build_crosswalk(parse_rxnconso(lines))

    assert rows == [
        CrosswalkRow(
            unii="362O9ITL9D",
            rxcui="161",
            rxnorm_name="Acetaminophen",
            synonyms=("acetaminophen", "paracetamol"),
        )
    ]
