from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from naz.detection.exceptions import NodeNotFoundError, SpecfyError, SpecfyTimeoutError


def run_specfy(path: str | Path) -> dict:
    """Run Specfy stack-analyser against path and return raw JSON dict.

    Args:
        path: Repository path to analyse.

    Returns:
        Parsed JSON dict from Specfy (flat format).

    Raises:
        NodeNotFoundError: npx not found on PATH.
        SpecfyTimeoutError: Analysis exceeded 120 seconds.
        SpecfyError: Non-zero exit, missing path, or unparseable output.
    """
    npx_cmd = shutil.which("npx")
    if npx_cmd is None:
        raise NodeNotFoundError(
            "npx not found. Node.js must be installed: https://nodejs.org"
        )

    target = Path(path)
    if not target.exists():
        raise SpecfyError(f"Path does not exist: {target}")

    print("Downloading stack analyser (first run only)...")  # D-11, D-13

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [
                    npx_cmd,
                    "--yes",
                    "@specfy/stack-analyser",
                    str(target),
                    "-o",
                    "out.json",
                    "--flat",
                ],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired as exc:
            raise SpecfyTimeoutError(
                "Stack analysis timed out after 120 seconds."
            ) from exc

        if result.returncode != 0:
            raise SpecfyError(
                f"Specfy exited with code {result.returncode}",
                stderr=result.stderr,
            )

        out_path = Path(tmpdir) / "out.json"
        try:
            return json.loads(out_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise SpecfyError(
                "Specfy did not produce output file",
                stderr=result.stderr,
            ) from exc
        except json.JSONDecodeError as exc:
            raise SpecfyError(
                f"Specfy output was not valid JSON: {exc}",
                stderr=result.stderr,
            ) from exc
