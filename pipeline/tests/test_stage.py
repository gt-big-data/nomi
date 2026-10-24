import logging

import pytest
from nomi_pipeline._stage import placeholder_app
from typer.testing import CliRunner

runner = CliRunner()


def test_placeholder_logs(caplog: pytest.LogCaptureFixture) -> None:
    app = placeholder_app("fetch")
    with caplog.at_level(logging.INFO):
        result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "fetch stage is not implemented yet" in caplog.text
