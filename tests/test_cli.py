"""Tests for Naz CLI entry point."""

from unittest.mock import patch

from typer.testing import CliRunner

from naz.cli import app

runner = CliRunner()


def test_help():
    """naz --help prints help message."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Security scanning for solo developers" in result.output


def test_no_args_shows_help():
    """naz with no args shows help (no_args_is_help=True)."""
    result = runner.invoke(app, [])
    # Typer returns exit code 0 for --help but 2 for no_args_is_help
    assert result.exit_code in (0, 2)
    assert "scan" in result.output


def test_scan_default_path():
    """naz scan with no path uses current directory (mocked runner)."""
    with patch("naz.cli.run_specfy", return_value={"techs": ["python"]}):
        result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0


def test_scan_custom_path():
    """naz scan /some/path passes the path argument to run_specfy."""
    with patch("naz.cli.run_specfy", return_value={"techs": ["python"]}) as mock_run:
        result = runner.invoke(app, ["scan", "/some/path"])
    assert result.exit_code == 0
    mock_run.assert_called_once_with("/some/path")
