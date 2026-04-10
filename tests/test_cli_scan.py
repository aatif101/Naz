"""Integration tests for naz scan command error paths and success."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from naz.cli import app
from naz.detection import NodeNotFoundError, SpecfyError, SpecfyTimeoutError

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures"
FLAT = json.loads((FIXTURES / "specfy_flat.json").read_text())


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
    """naz scan renders Rich panels to stdout on success."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", "."])

    assert result.exit_code == 0
    assert "Languages" in result.output
    assert "Technologies" in result.output
    assert "Dependencies" in result.output


def test_scan_json_flag_produces_valid_json():
    """naz scan --json outputs parseable JSON to stdout."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", ".", "--json"])

    assert result.exit_code == 0
    data = json.loads(result.output)  # raises if invalid JSON
    assert isinstance(data, dict)


def test_scan_json_excludes_raw_field():
    """naz scan --json does not include the internal raw field."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", ".", "--json"])

    data = json.loads(result.output)
    assert "raw" not in data


def test_scan_json_contains_technologies():
    """naz scan --json output contains technologies key."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", ".", "--json"])

    data = json.loads(result.output)
    assert "technologies" in data


def test_scan_json_no_rich_panels():
    """naz scan --json suppresses Rich terminal output entirely."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", ".", "--json"])

    assert result.exit_code == 0
    # Rich panel titles must not appear in stdout when --json is active
    assert "Languages" not in result.output
    assert "Technologies" not in result.output
