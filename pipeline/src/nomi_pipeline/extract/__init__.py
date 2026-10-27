"""Label fact extraction: rule-based and LLM extractors and their merge (NOMI-031, 032, 045, 047)."""

import json
from pathlib import Path

import typer

from nomi_pipeline._stage import placeholder_app
from nomi_pipeline.extract.rules import extract

app = placeholder_app("extract")


@app.command()
def rules(label: Path) -> None:
    """Run the rule-based extractor on one openFDA label JSON file and print the facts."""
    record = json.loads(label.read_text(encoding="utf-8"))
    if "results" in record:
        record = record["results"][0]
    typer.echo(extract(record).model_dump_json(indent=2))
