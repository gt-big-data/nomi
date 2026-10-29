from nomi_pipeline.cli import app
from typer.testing import CliRunner

runner = CliRunner()

STAGES = ["fetch", "ingest", "identity", "extract", "evidence", "score", "build"]
PLACEHOLDER_STAGES = ["ingest", "identity", "extract", "evidence", "score", "build"]


def test_help_stages() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    for stage in STAGES:
        assert stage in result.stdout


def test_stage_placeholder_runs() -> None:
    for stage in PLACEHOLDER_STAGES:
        result = runner.invoke(app, [stage, "placeholder"])
        assert result.exit_code == 0, f"{stage} failed: {result.output}"


def test_fetch_commands_available() -> None:
    result = runner.invoke(app, ["fetch", "--help"])
    assert result.exit_code == 0
    for cmd in ("all", "ndc", "faers"):
        assert cmd in result.stdout
