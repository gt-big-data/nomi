from nomi_pipeline.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_fetch_rxnorm_runs() -> None:
    result = runner.invoke(app, ["fetch", "rxnorm"])

    assert result.exit_code == 0, result.output
