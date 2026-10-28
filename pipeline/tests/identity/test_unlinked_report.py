import csv
from pathlib import Path

from nomi_pipeline.identity.crosswalk import UnlinkedRow, write_unlinked_csv


def test_write_unlinked_csv_writes_header_and_sorted_rows(tmp_path: Path) -> None:
    path = tmp_path / "reports" / "crosswalk_unlinked.csv"
    rows = [
        UnlinkedRow("ZZZZZZZZZZ", "Unknown Ingredient", "unii_not_in_rxnorm"),
        UnlinkedRow("", "Mystery, Ingredient", "missing_unii"),
    ]

    write_unlinked_csv(rows, path)

    with path.open(encoding="utf-8", newline="") as file:
        assert list(csv.reader(file)) == [
            ["unii", "ingredient_name", "reason"],
            ["", "Mystery, Ingredient", "missing_unii"],
            ["ZZZZZZZZZZ", "Unknown Ingredient", "unii_not_in_rxnorm"],
        ]
