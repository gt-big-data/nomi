from nomi_pipeline.identity.crosswalk import normalize_name


def test_normalize_name_ignores_case_and_punctuation() -> None:
    assert normalize_name("Acetaminophen") == "acetaminophen"
    assert normalize_name("  ACETAMINOPHEN, ") == "acetaminophen"
    assert normalize_name("Alpha-Lipoic Acid") == "alpha lipoic acid"
    assert normalize_name("Aspirin (Acetylsalicylic Acid)") == "aspirin acetylsalicylic acid"
