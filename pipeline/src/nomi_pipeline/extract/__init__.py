"""Label fact extraction: rule-based and LLM extractors and their merge (NOMI-031, 032, 045, 047)."""

import json
import os
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


@app.command("llm")
def llm_command(
    labels: Path,
    out: Path,
    limit: int = 200,
    model: str = "claude-haiku-4-5",
    in_scope_labels: int = 25_000,
) -> None:
    """Run LLM extraction on the first LIMIT labels of a JSONL file and print a cost report."""
    import nomi_pipeline.extract.llm as llm_extract

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise typer.BadParameter("set ANTHROPIC_API_KEY in the environment or .env")
    send = llm_extract.http_transport(api_key)
    lines = labels.read_text(encoding="utf-8").splitlines()[:limit]
    results = [llm_extract.extract(json.loads(line), send, model) for line in lines]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(r.record) + "\n" for r in results if r.record), encoding="utf-8"
    )
    typer.echo(llm_extract.report(results, model, in_scope_labels).model_dump_json(indent=2))
