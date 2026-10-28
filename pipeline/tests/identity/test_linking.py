from nomi_pipeline.identity.crosswalk import (
    CrosswalkRow,
    Ingredient,
    UnlinkedRow,
    link_ingredients,
)

CROSSWALK = [
    CrosswalkRow(
        unii="362O9ITL9D",
        rxcui="161",
        rxnorm_name="Acetaminophen",
        synonyms=("acetaminophen", "paracetamol"),
    )
]


def test_link_ingredients_splits_linked_and_unlinked_with_reasons() -> None:
    ingredients = [
        Ingredient(unii="362o9itl9d", name="Acetaminophen"),
        Ingredient(unii="", name="Mystery Ingredient"),
        Ingredient(unii="ZZZZZZZZZZ", name="Unknown Ingredient"),
    ]

    linked, unlinked = link_ingredients(ingredients, CROSSWALK)

    assert linked == CROSSWALK
    assert unlinked == [
        UnlinkedRow("", "Mystery Ingredient", "missing_unii"),
        UnlinkedRow("ZZZZZZZZZZ", "Unknown Ingredient", "unii_not_in_rxnorm"),
    ]


def test_link_ingredients_counts_a_repeated_unii_once() -> None:
    ingredients = [
        Ingredient(unii="362O9ITL9D", name="Acetaminophen"),
        Ingredient(unii="362O9ITL9D", name="Paracetamol"),
    ]

    linked, unlinked = link_ingredients(ingredients, CROSSWALK)

    assert linked == CROSSWALK
    assert unlinked == []
