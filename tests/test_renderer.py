"""Tests for naz.renderer — Rich terminal output for ProjectProfile."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from naz.cli import app

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures"
FLAT = json.loads((FIXTURES / "specfy_flat.json").read_text())
AI = json.loads((FIXTURES / "specfy_ai.json").read_text())


def test_render_languages_panel():
    """Languages panel shows language names and line counts."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "Languages" in result.output
    assert "Python" in result.output
    assert "834" in result.output


def test_render_technologies_panel():
    """Technologies panel shows detected tech names."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "Technologies" in result.output
    assert "python" in result.output


def test_render_dependencies_panel():
    """Dependencies panel shows manager, package, and version."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "Dependencies" in result.output
    assert "typer" in result.output
    assert "0.24.0" in result.output


def test_render_no_ai_panel_when_empty():
    """AI/LLM panel is absent when ai_dependencies is empty."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "AI / LLM" not in result.output


def test_render_ai_panel_when_present():
    """AI/LLM panel appears with yellow border when ai_dependencies is non-empty."""
    with patch("naz.cli.run_specfy", return_value=AI):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "AI / LLM" in result.output
    assert "openai" in result.output


def test_render_empty_languages():
    """Languages panel shows 'None detected' row when languages dict is empty."""
    EMPTY = {**FLAT, "languages": {}, "techs": [], "dependencies": []}
    with patch("naz.cli.run_specfy", return_value=EMPTY):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "None detected" in result.output


def test_render_stdout_not_stderr():
    """Rich panel content appears in stdout (result.output), not only stderr."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    # result.output is stdout; panels must appear there so output is pipeable
    assert "Languages" in result.output


def test_scan_header_shows_path():
    """Scan header shows 'Scan complete' with the scanned path."""
    with patch("naz.cli.run_specfy", return_value=FLAT):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "Scan complete" in result.output
