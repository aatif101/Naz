"""Integration tests for naz scan command error paths and success."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from naz.cli import app
from naz.detection import NodeNotFoundError, SpecfyError, SpecfyTimeoutError

runner = CliRunner()


def test_scan_node_not_found():
    """naz scan shows Rich error panel with nodejs.org URL when Node.js is missing."""
    with patch(
        "naz.cli.run_specfy",
        side_effect=NodeNotFoundError(
            "npx not found. Node.js must be installed: https://nodejs.org"
        ),
    ):
        result = runner.invoke(app, ["scan", "."])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "Node.js" in combined
    assert "nodejs.org" in combined
    assert "Error" in combined


def test_scan_timeout():
    """naz scan shows Rich error panel with smaller directory suggestion on timeout."""
    with patch(
        "naz.cli.run_specfy",
        side_effect=SpecfyTimeoutError("Stack analysis timed out after 120 seconds."),
    ):
        result = runner.invoke(app, ["scan", "."])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "timed out" in combined.lower()
    assert "smaller directory" in combined


def test_scan_specfy_error():
    """naz scan shows Rich error panel with stderr content on Specfy failure."""
    with patch(
        "naz.cli.run_specfy",
        side_effect=SpecfyError("Specfy exited with code 1", stderr="ENOENT something"),
    ):
        result = runner.invoke(app, ["scan", "."])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "failed" in combined.lower()
    assert "ENOENT" in combined


def test_scan_specfy_error_no_stderr():
    """naz scan shows Rich error panel even when Specfy error has no stderr."""
    with patch(
        "naz.cli.run_specfy",
        side_effect=SpecfyError("Specfy exited with code 1", stderr=""),
    ):
        result = runner.invoke(app, ["scan", "."])

    assert result.exit_code == 1
    combined = result.output + (result.stderr or "")
    assert "failed" in combined.lower()


def test_scan_success():
    """naz scan prints raw result dict on success."""
    with patch(
        "naz.cli.run_specfy",
        return_value={"techs": ["python"], "dependencies": []},
    ):
        result = runner.invoke(app, ["scan", "."])

    assert result.exit_code == 0
    assert "python" in result.output
