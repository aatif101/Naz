"""Unit tests for naz.detection.runner.run_specfy."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from naz.detection.exceptions import NodeNotFoundError, SpecfyError, SpecfyTimeoutError
from naz.detection.runner import run_specfy

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "specfy_flat.json"


def _write_fixture(tmpdir: str) -> MagicMock:
    """Write fixture JSON into tmpdir and return a mock subprocess result."""
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    (Path(tmpdir) / "out.json").write_text(json.dumps(fixture), encoding="utf-8")
    mock = MagicMock()
    mock.returncode = 0
    mock.stderr = ""
    return mock


def test_run_specfy_success(tmp_path):
    """run_specfy returns a dict with 'dependencies' key on success."""
    with (
        patch("naz.detection.runner.shutil.which", return_value="/usr/bin/npx"),
        patch("naz.detection.runner.subprocess.run") as mock_run,
        patch("naz.detection.runner.tempfile.TemporaryDirectory") as mock_tmpdir,
    ):
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        mock_run.return_value = _write_fixture(str(tmp_path))

        result = run_specfy("/some/repo")
        assert isinstance(result, dict)
        assert "dependencies" in result


def test_node_not_found():
    """run_specfy raises NodeNotFoundError when npx is not on PATH."""
    with patch("naz.detection.runner.shutil.which", return_value=None):
        with pytest.raises(NodeNotFoundError) as exc_info:
            run_specfy("/some/repo")
        assert "nodejs.org" in str(exc_info.value)


def test_specfy_timeout(tmp_path):
    """run_specfy raises SpecfyTimeoutError when subprocess exceeds timeout."""
    with (
        patch("naz.detection.runner.shutil.which", return_value="/usr/bin/npx"),
        patch(
            "naz.detection.runner.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="npx", timeout=120),
        ),
        patch("naz.detection.runner.tempfile.TemporaryDirectory") as mock_tmpdir,
    ):
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        with pytest.raises(SpecfyTimeoutError):
            run_specfy("/some/repo")


def test_specfy_nonzero_exit(tmp_path):
    """run_specfy raises SpecfyError with stderr when Specfy exits non-zero."""
    mock = MagicMock()
    mock.returncode = 1
    mock.stderr = "some error"
    with (
        patch("naz.detection.runner.shutil.which", return_value="/usr/bin/npx"),
        patch("naz.detection.runner.subprocess.run", return_value=mock),
        patch("naz.detection.runner.tempfile.TemporaryDirectory") as mock_tmpdir,
    ):
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        with pytest.raises(SpecfyError) as exc_info:
            run_specfy("/some/repo")
        assert exc_info.value.stderr == "some error"


def test_specfy_no_output_file(tmp_path):
    """run_specfy raises SpecfyError when out.json is not produced."""
    mock = MagicMock()
    mock.returncode = 0
    mock.stderr = ""
    # Do NOT write out.json into tmp_path
    with (
        patch("naz.detection.runner.shutil.which", return_value="/usr/bin/npx"),
        patch("naz.detection.runner.subprocess.run", return_value=mock),
        patch("naz.detection.runner.tempfile.TemporaryDirectory") as mock_tmpdir,
    ):
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        with pytest.raises(SpecfyError) as exc_info:
            run_specfy("/some/repo")
        assert "did not produce" in str(exc_info.value)


def test_specfy_invalid_json(tmp_path):
    """run_specfy raises SpecfyError when out.json contains invalid JSON."""
    mock = MagicMock()
    mock.returncode = 0
    mock.stderr = ""
    (tmp_path / "out.json").write_text("not json", encoding="utf-8")
    with (
        patch("naz.detection.runner.shutil.which", return_value="/usr/bin/npx"),
        patch("naz.detection.runner.subprocess.run", return_value=mock),
        patch("naz.detection.runner.tempfile.TemporaryDirectory") as mock_tmpdir,
    ):
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        with pytest.raises(SpecfyError) as exc_info:
            run_specfy("/some/repo")
        assert "not valid JSON" in str(exc_info.value)


def test_npx_cmd_passed_to_subprocess(tmp_path):
    """subprocess.run is called with the shutil.which result as first arg."""
    resolved_npx = r"C:\Program Files\nodejs\npx.CMD"
    with (
        patch("naz.detection.runner.shutil.which", return_value=resolved_npx),
        patch("naz.detection.runner.subprocess.run") as mock_run,
        patch("naz.detection.runner.tempfile.TemporaryDirectory") as mock_tmpdir,
    ):
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        mock_run.return_value = _write_fixture(str(tmp_path))

        run_specfy("/some/repo")
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == resolved_npx


def test_path_not_exists(tmp_path):
    """run_specfy raises SpecfyError when path does not exist."""
    with patch("naz.detection.runner.shutil.which", return_value="/usr/bin/npx"):
        with pytest.raises(SpecfyError) as exc_info:
            run_specfy("/does/not/exist/repo")
        assert "does not exist" in str(exc_info.value)
