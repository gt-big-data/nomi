import logging

import typer

from nomi_pipeline import build, evidence, extract, fetch, identity, ingest, score
from nomi_pipeline.config import Settings

app = typer.Typer(help="Nomi data and scoring pipeline")


@app.callback()
def configure_logging() -> None:
    settings = Settings()
    logging.basicConfig(level=settings.log_level, format="%(levelname)s %(name)s: %(message)s")


app.add_typer(fetch.app, name="fetch")
app.add_typer(ingest.app, name="ingest")
app.add_typer(identity.app, name="identity")
app.add_typer(extract.app, name="extract")
app.add_typer(evidence.app, name="evidence")
app.add_typer(score.app, name="score")
app.add_typer(build.app, name="build")


def main() -> None:
    app()
