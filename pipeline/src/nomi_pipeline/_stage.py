import logging

import typer

logger = logging.getLogger(__name__)


def placeholder_app(stage: str) -> typer.Typer:
    """Build the typer app here with a single not-implemented-yet command for a stage."""
    app = typer.Typer()

    @app.command()
    def placeholder() -> None:
        logger.info("%s stage is not implemented yet", stage)

    return app
