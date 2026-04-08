# Phase 2: Specfy Integration - Research

**Researched:** 2026-04-08
**Domain:** Python subprocess management, Specfy CLI interface, Windows npx resolution
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Use Rich-formatted error panels for all user-facing errors
- **D-02:** Actionable minimum verbosity -- what went wrong + one clear next step. No stack traces or debug info.
- **D-03:** Node.js missing error must include install URL (https://nodejs.org) and the command to retry
- **D-04:** 120-second timeout for Specfy subprocess
- **D-05:** On timeout, abort immediately with Rich error panel suggesting smaller directory. No retry.
- **D-06:** Non-zero exit code or unparseable JSON is a hard failure. No partial results.
- **D-07:** Runner function returns raw dict on success
- **D-08:** Raise typed exceptions: `NodeNotFoundError`, `SpecfyTimeoutError`, `SpecfyError`
- **D-09:** CLI layer catches exceptions and renders Rich error panels. Detection layer never imports Rich.
- **D-10:** Runner lives in `src/naz/detection/` module
- **D-11:** Print a brief message before npx call on first run: "Downloading stack analyser (first run only)..."
- **D-12:** Use `npx --yes` flag to auto-accept the install prompt
- **D-13:** No spinner or progress bar -- just the text message.
- **D-14:** On Windows, resolve `npx.cmd` instead of `npx` (use `shutil.which("npx")`)
- **D-15:** Never use `shell=True` in subprocess calls
- **D-16:** Use `subprocess.run()` with `capture_output=True, text=True`

### Claude's Discretion

- Exact exception class hierarchy and base class design
- Internal module structure within `src/naz/detection/`
- How to detect first-run vs subsequent runs (checking npx cache, or always showing the message)
- Test fixture structure for mocked Specfy output

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DET-01 | Naz runs Specfy stack-analyser via npx subprocess against the target path | Verified: Specfy CLI invoked via `npx --yes @specfy/stack-analyser <path> -o <file> --flat`. Output written to file, not stdout. Temp dir strategy confirmed working. |
| DET-06 | Detection works correctly on Windows (npx.cmd resolution, install prompt handling) | Verified: `shutil.which("npx")` returns `npx.CMD` on Windows (case-insensitive). `subprocess.run([npx_cmd, ...])` with the resolved path works. `--yes` flag eliminates interactive install prompt. |
| CLI-02 | User sees a clear error with install instructions if Node.js is not installed | Verified: `shutil.which("npx")` returns `None` when npx is not found. Rich Panel error display confirmed working. |
</phase_requirements>

---

## Summary

Phase 2 builds the subprocess runner that invokes `@specfy/stack-analyser` via npx and returns raw detection data as a Python dict. This phase does NOT parse or normalize the output -- that is Phase 3's responsibility.

The most important finding from live testing is that **Specfy does not write JSON to stdout**. The CLI writes JSON to a file (default: `output.json`) in the process working directory. The correct capture strategy is: run the subprocess with `cwd` set to a `tempfile.TemporaryDirectory()`, tell Specfy to write to a fixed relative filename (`-o out.json`), then read that file. This approach is clean, platform-safe, and requires no hacks.

On Windows, `shutil.which("npx")` correctly returns the `.CMD` extension path (`C:\Program Files\nodejs\npx.CMD`). Using this resolved path in `subprocess.run()` works reliably without `shell=True`. The `--yes` flag on npx eliminates the interactive install prompt that would cause the subprocess to hang on first run.

**Primary recommendation:** Use the temp-dir capture pattern. Resolve npx via `shutil.which`. Raise typed exceptions for all failure modes. Keep the detection module entirely free of Rich imports -- let the CLI layer handle all output.

---

## Standard Stack

All libraries below are stdlib or already in pyproject.toml from Phase 1. No new dependencies are required for this phase.

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| subprocess (stdlib) | N/A | Run npx subprocess | Locked decision. `subprocess.run()` with `capture_output=True, text=True` |
| shutil (stdlib) | N/A | Locate npx executable | `shutil.which("npx")` returns resolved path including `.CMD` on Windows |
| pathlib (stdlib) | N/A | Path validation | `Path(path).exists()` before invoking Specfy |
| tempfile (stdlib) | N/A | Capture Specfy output | `tempfile.TemporaryDirectory()` as context manager; Specfy writes JSON to file, not stdout |
| json (stdlib) | N/A | Parse Specfy JSON file | `json.loads()` on temp file contents |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rich (^14.3.3) | installed | Error panels in CLI layer | CLI layer only -- detection module must NOT import Rich |
| typing (stdlib) | N/A | Type annotations | `str \| Path` for path parameter |

### No New Dependencies

```bash
# No new packages needed -- all stdlib or already installed
uv run pytest  # verify existing tests still pass
```

---

## Architecture Patterns

### Module Structure

```
src/naz/
├── detection/
│   ├── __init__.py        # Re-exports: run_specfy, NodeNotFoundError, SpecfyTimeoutError, SpecfyError
│   ├── runner.py          # run_specfy() function, subprocess logic, file capture
│   └── exceptions.py      # Typed exception classes
├── cli.py                 # Updated: imports runner, catches exceptions, renders Rich panels
└── models.py              # Untouched (Phase 3 will use these)
tests/
├── fixtures/
│   └── specfy_flat.json   # Real Specfy --flat output fixture
├── test_runner.py         # Unit tests for runner (mocked subprocess + file)
└── test_cli_scan.py       # Integration tests for CLI scan command error paths
```

### Pattern 1: Temp-Dir File Capture

**What:** Specfy writes JSON to a file in the process working directory. Use `tempfile.TemporaryDirectory()` as the subprocess `cwd` to capture output cleanly.

**When to use:** Always -- Specfy has no `--output=stdout` option. `/dev/stdout` fails on Windows.

```python
# Source: verified by live testing on Windows (2026-04-08)
import subprocess, shutil, tempfile, json
from pathlib import Path

def run_specfy(path: str | Path) -> dict:
    npx_cmd = shutil.which("npx")
    if npx_cmd is None:
        raise NodeNotFoundError("npx not found -- Node.js must be installed")

    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            [npx_cmd, "--yes", "@specfy/stack-analyser", str(path), "-o", "out.json", "--flat"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=tmpdir,
        )
        if result.returncode != 0:
            raise SpecfyError(f"Specfy exited with code {result.returncode}", stderr=result.stderr)

        out_path = Path(tmpdir) / "out.json"
        try:
            return json.loads(out_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError) as exc:
            raise SpecfyError(f"Could not parse Specfy output: {exc}", stderr=result.stderr) from exc
```

### Pattern 2: Typed Exceptions

**What:** Three exception classes, all inheriting from a common base. Detection layer raises them; CLI layer catches and renders Rich panels.

**When to use:** Always -- D-08 and D-09 require this separation.

```python
# Source: locked decision D-08, D-09
class NazDetectionError(Exception):
    """Base for all detection-layer exceptions."""

class NodeNotFoundError(NazDetectionError):
    """npx not found -- Node.js is not installed."""

class SpecfyTimeoutError(NazDetectionError):
    """Specfy subprocess exceeded the timeout."""

class SpecfyError(NazDetectionError):
    """Specfy returned non-zero exit or unparseable output."""
    def __init__(self, message: str, stderr: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr
```

### Pattern 3: Rich Error Panels in CLI Layer

**What:** CLI scan command catches detection exceptions and renders Rich-formatted error panels.

**When to use:** CLI layer only -- detection module never imports Rich.

```python
# Source: verified Rich Panel display (2026-04-08)
from rich.console import Console
from rich.panel import Panel

console = Console(stderr=True)

try:
    raw = run_specfy(path)
except NodeNotFoundError:
    console.print(Panel(
        "Node.js is not installed.\n\nInstall from [link=https://nodejs.org]https://nodejs.org[/link]"
        " then run: [bold]naz scan .[/bold]",
        title="[red]Error: Node.js Required[/red]",
        border_style="red",
    ))
    raise typer.Exit(code=1)
except SpecfyTimeoutError:
    console.print(Panel(
        "Stack analysis timed out after 120 seconds.\n\nTry scanning a smaller directory.",
        title="[red]Error: Timeout[/red]",
        border_style="red",
    ))
    raise typer.Exit(code=1)
except SpecfyError as exc:
    console.print(Panel(
        f"Stack analysis failed.\n\n{exc.stderr[:500] if exc.stderr else str(exc)}",
        title="[red]Error: Analysis Failed[/red]",
        border_style="red",
    ))
    raise typer.Exit(code=1)
```

### Pattern 4: First-Run Message

**What:** Print a brief message before the npx call. D-11 requires it; D-13 says no spinner.

**When to use:** The simplest correct approach is to always show the message before the subprocess call. Detecting "first run" vs cached requires inspecting npm cache internals -- unnecessary complexity. Always printing is safe and matches D-11's intent.

```python
# Source: locked decisions D-11, D-12, D-13
typer.echo("Downloading stack analyser (first run only)...")
result = subprocess.run([npx_cmd, "--yes", ...], ...)
```

### Anti-Patterns to Avoid

- **`shell=True` in subprocess.run:** D-15 explicitly forbids it. Shell injection risk; unnecessary on Windows with resolved path.
- **Capturing stdout for JSON:** Specfy writes JSON to a file, not stdout. stdout only contains progress messages. Reading from stdout will get a file path string, not JSON.
- **`/dev/stdout` as output path:** Fails on Windows (verified: throws ENOENT for `proc\self\fd\1`). Not cross-platform.
- **Absolute paths in `-o` flag:** Specfy joins `-o` value with the repo path arg on Windows (verified), not the cwd. Use a plain relative filename (`out.json`) with `cwd=tmpdir`.
- **Importing Rich in `detection/`:** D-09 locks the boundary. Exception classes live in detection, Rich rendering lives in CLI.
- **`os.path`:** Use `pathlib.Path` everywhere per CLAUDE.md conventions.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| npx executable resolution | Custom PATH search | `shutil.which("npx")` | Returns `.CMD` on Windows, handles PATHEXT, returns `None` when missing |
| Temp file management | Manual file create/delete | `tempfile.TemporaryDirectory()` | Auto-cleanup even on exception; context manager |
| JSON parsing | Custom parser | `json.loads()` / `Path.read_text()` | Specfy output is KB-sized, stdlib is sufficient |
| Subprocess timeout | Custom threading alarm | `subprocess.run(timeout=120)` | Built-in, raises `TimeoutExpired` which you catch once |

**Key insight:** All the hard cross-platform work (path resolution, temp dirs, subprocess timeout) is already in the Python stdlib. The runner function is mostly wiring.

---

## Common Pitfalls

### Pitfall 1: Specfy Writes to File, Not Stdout

**What goes wrong:** Code does `result.stdout` expecting JSON. Gets the path message `"Output C:\...\output.json"` instead.

**Why it happens:** CLAUDE.md describes `--output=json` as a flag. That flag does not exist. The actual flag is `-o <filename>` which writes to a file. The only stdout is a human-readable status line.

**How to avoid:** Use the temp-dir pattern (Pattern 1 above). Specfy is told to write to `out.json` inside `tmpdir`; Python then reads that file.

**Warning signs:** `json.JSONDecodeError` when parsing `result.stdout`. stdout starts with `"Output "` or `"▶ Path "`.

### Pitfall 2: Absolute Output Paths Fail on Windows

**What goes wrong:** Passing an absolute temp path like `C:\Temp\out.json` to `-o` causes Specfy to try opening `<repo_path>\C:\Temp\out.json` on Windows (path join bug in Specfy's CLI source).

**Why it happens:** Specfy's Node.js CLI joins the `-o` value with the repo path on Windows before writing.

**How to avoid:** Always pass a plain relative filename (`out.json`) and set `cwd=tmpdir` on the subprocess. The file ends up at `tmpdir/out.json`, which Python can read cleanly.

**Warning signs:** Specfy exits with ENOENT error containing the doubled path.

### Pitfall 3: `subprocess.run` Raises Instead of Returning Non-Zero

**What goes wrong:** Calling `subprocess.run` without `check=False` (default) but then checking `returncode` -- this is fine. BUT if you call `subprocess.run(..., check=True)`, it raises `subprocess.CalledProcessError` instead of returning a result.

**Why it happens:** Using `check=True` is a common pattern but bypasses the explicit error handling we need to capture `stderr`.

**How to avoid:** Use the default (`check=False`). Check `result.returncode` manually and access `result.stderr` for diagnostics before raising `SpecfyError`.

### Pitfall 4: `shutil.which("npx")` Returns `.CMD` Case-Variation

**What goes wrong:** Comparing `shutil.which("npx")` result to a hardcoded string or expecting lowercase.

**Why it happens:** On Windows, `shutil.which("npx")` returns `C:\Program Files\nodejs\npx.CMD` (uppercase `.CMD`). The path is always valid for `subprocess.run` regardless of case.

**How to avoid:** Never compare the path -- just check `is None`. Pass the result directly to subprocess. Case doesn't matter for Windows execution.

### Pitfall 5: TimeoutExpired Leaves Subprocess Running

**What goes wrong:** After `subprocess.TimeoutExpired`, the child process may still be running in the background.

**Why it happens:** `subprocess.run(timeout=...)` raises `TimeoutExpired` but doesn't guarantee the child is dead.

**How to avoid:** The `subprocess.run()` implementation internally calls `process.kill()` and `process.communicate()` after a timeout, so the cleanup is handled. Just catch `TimeoutExpired` and raise `SpecfyTimeoutError`.

---

## Code Examples

### Complete Runner Function

```python
# Source: verified by live testing on this machine (2026-04-08)
# File: src/naz/detection/runner.py
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
        SpecfyError: Non-zero exit or unparseable output.
    """
    npx_cmd = shutil.which("npx")
    if npx_cmd is None:
        raise NodeNotFoundError(
            "npx not found. Node.js must be installed: https://nodejs.org"
        )

    print("Downloading stack analyser (first run only)...")  # D-11, D-13

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            result = subprocess.run(
                [npx_cmd, "--yes", "@specfy/stack-analyser", str(path), "-o", "out.json", "--flat"],
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
                "Specfy did not produce output.json",
                stderr=result.stderr,
            ) from exc
        except json.JSONDecodeError as exc:
            raise SpecfyError(
                f"Specfy output was not valid JSON: {exc}",
                stderr=result.stderr,
            ) from exc
```

### Exception Classes

```python
# Source: locked decisions D-08, D-09
# File: src/naz/detection/exceptions.py

class NazDetectionError(Exception):
    """Base class for all detection-layer errors."""


class NodeNotFoundError(NazDetectionError):
    """Raised when npx is not found on PATH (Node.js not installed)."""


class SpecfyTimeoutError(NazDetectionError):
    """Raised when Specfy subprocess exceeds the 120-second timeout."""


class SpecfyError(NazDetectionError):
    """Raised when Specfy returns a non-zero exit code or unparseable output."""

    def __init__(self, message: str, stderr: str = "") -> None:
        super().__init__(message)
        self.stderr = stderr
```

### Mocking Specfy in Tests

```python
# Source: CLAUDE.md testing section + test pattern from test_models.py
# File: tests/test_runner.py
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from naz.detection.exceptions import NodeNotFoundError, SpecfyError, SpecfyTimeoutError
from naz.detection.runner import run_specfy

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "specfy_flat.json"


def _mock_subprocess_success(tmpdir: str) -> MagicMock:
    """Write fixture JSON into tmpdir so runner can read it."""
    fixture = json.loads(FIXTURE_PATH.read_text())
    (Path(tmpdir) / "out.json").write_text(json.dumps(fixture))
    mock = MagicMock()
    mock.returncode = 0
    mock.stderr = ""
    return mock


def test_run_specfy_success(tmp_path):
    with patch("shutil.which", return_value="/usr/bin/npx"), \
         patch("subprocess.run") as mock_run, \
         patch("tempfile.TemporaryDirectory") as mock_tmpdir:
        # Point tmpdir at tmp_path so fixture write works
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        mock_run.return_value = _mock_subprocess_success(str(tmp_path))

        result = run_specfy("/some/repo")
        assert isinstance(result, dict)
        assert "dependencies" in result


def test_node_not_found():
    with patch("shutil.which", return_value=None):
        with pytest.raises(NodeNotFoundError):
            run_specfy("/some/repo")


def test_specfy_timeout():
    import subprocess
    with patch("shutil.which", return_value="/usr/bin/npx"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="npx", timeout=120)):
        with pytest.raises(SpecfyTimeoutError):
            run_specfy("/some/repo")


def test_specfy_nonzero_exit(tmp_path):
    mock = MagicMock()
    mock.returncode = 1
    mock.stderr = "some error"
    with patch("shutil.which", return_value="/usr/bin/npx"), \
         patch("subprocess.run", return_value=mock), \
         patch("tempfile.TemporaryDirectory") as mock_tmpdir:
        mock_tmpdir.return_value.__enter__.return_value = str(tmp_path)
        with pytest.raises(SpecfyError):
            run_specfy("/some/repo")
```

### Specfy Flat Output Schema (Fixture Reference)

The `--flat` flag collapses the component tree. The output schema for `out.json`:

```json
{
  "id": "string (random)",
  "name": "flatten",
  "path": ["/", ""],
  "tech": null,
  "edges": [],
  "inComponent": null,
  "childs": [],
  "techs": ["python", "javascript"],
  "languages": {"Python": 834, "JSON": 5},
  "licenses": [],
  "dependencies": [
    ["python", "typer", "0.24.0"],
    ["python", "pydantic", "2.12.0"]
  ],
  "reason": ["matched extension: .py"]
}
```

`dependencies` is a list of 3-element arrays: `[manager, name, version]`. [VERIFIED: live run 2026-04-08]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Always printing "Downloading stack analyser (first run only)..." is the correct interpretation of D-11 (vs detecting actual first run) | Architecture Patterns - Pattern 4 | Low: message is slightly inaccurate on subsequent runs but harmless. Detecting real first-run requires npm cache inspection -- complex with no benefit. |

---

## Open Questions (RESOLVED)

1. **Should the `print()` call in runner.py use `typer.echo()` or stdlib `print()`?**
   - What we know: D-09 says detection layer never imports Rich. Typer is not Rich.
   - What's unclear: Is importing Typer in the detection layer acceptable, or should it be stdlib `print()`?
   - Recommendation: Use stdlib `print()` to keep the detection layer dependency-free. The CLI layer wraps all output anyway.

2. **Path validation: should runner validate that `path` exists before invoking Specfy?**
   - What we know: If the path doesn't exist, Specfy will exit with a non-zero code.
   - What's unclear: Should runner do an early `Path(path).exists()` check for a better error message?
   - Recommendation: Yes -- validate early and raise `SpecfyError("Path does not exist: ...")` before invoking npx. Better UX, minimal code.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npx | DET-01, DET-06 | Yes | v25.2.1 / 11.6.2 | None -- tested on this machine |
| Python (via uv) | All | Yes | 3.14.0 | None |
| pytest | Testing | Yes | 9.0.2 | None |
| @specfy/stack-analyser | DET-01 | Yes (cached) | 1.27.6 | None |

Note: `shutil.which("npx")` returns `C:\Program Files\nodejs\npx.CMD` on this Windows machine. [VERIFIED: live test 2026-04-08]

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_runner.py -q` |
| Full suite command | `uv run pytest tests/ -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DET-01 | run_specfy returns dict on success | unit | `uv run pytest tests/test_runner.py::test_run_specfy_success -x` | No -- Wave 0 |
| DET-01 | run_specfy raises SpecfyError on non-zero exit | unit | `uv run pytest tests/test_runner.py::test_specfy_nonzero_exit -x` | No -- Wave 0 |
| DET-06 | run_specfy uses shutil.which("npx") result (not hardcoded "npx") | unit | `uv run pytest tests/test_runner.py::test_npx_cmd_resolved -x` | No -- Wave 0 |
| CLI-02 | scan command shows Rich error panel when Node.js missing | integration | `uv run pytest tests/test_cli_scan.py::test_scan_node_missing -x` | No -- Wave 0 |
| DET-01 | run_specfy raises SpecfyTimeoutError on 120s timeout | unit | `uv run pytest tests/test_runner.py::test_specfy_timeout -x` | No -- Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/test_runner.py -q`
- **Per wave merge:** `uv run pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/fixtures/specfy_flat.json` -- real Specfy flat output fixture (copy from live run)
- [ ] `tests/test_runner.py` -- covers DET-01, DET-06
- [ ] `tests/test_cli_scan.py` -- covers CLI-02 error paths

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | Yes | Validate `path` exists before passing to subprocess |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for subprocess + npx

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection via `path` argument | Tampering | Never use `shell=True`. Pass path as list element to `subprocess.run()` -- no shell interpretation. |
| Path traversal | Tampering | Validate `path` with `Path(path).resolve()` and check it exists before invoking Specfy |
| Subprocess hanging | Denial of Service | `timeout=120` enforced, `TimeoutExpired` caught and converted to `SpecfyTimeoutError` |
| Malicious Specfy output | Tampering | Phase 2 returns raw dict. Phase 3 validates through Pydantic -- this phase is safe since no model validation happens here |

---

## Sources

### Primary (HIGH confidence)

- Live testing on this machine (Windows 11, Node v25.2.1, npx 11.6.2, @specfy/stack-analyser 1.27.6) -- Specfy CLI interface, output schema, path resolution behavior
- `shutil.which()` stdlib -- verified returns `npx.CMD` on Windows
- `subprocess.run()` stdlib -- verified `TimeoutExpired` and `FileNotFoundError` behavior
- `tempfile.TemporaryDirectory()` stdlib -- verified cleanup behavior

### Secondary (MEDIUM confidence)

- CLAUDE.md subprocess section -- subprocess.run pattern, timeout value, shutil.which guidance [CITED: ./CLAUDE.md]
- Phase 2 CONTEXT.md locked decisions D-01 through D-16 [CITED: .planning/phases/02-specfy-integration/02-CONTEXT.md]

### Tertiary (LOW confidence)

None -- all critical claims were verified by live testing.

---

## Metadata

**Confidence breakdown:**

- Specfy CLI interface: HIGH -- live-tested on Windows, output schema confirmed
- subprocess / shutil patterns: HIGH -- stdlib, live-tested
- Windows npx.CMD resolution: HIGH -- `shutil.which("npx")` verified to return `.CMD` path
- Exception hierarchy design: HIGH -- follows locked decisions exactly
- First-run detection: MEDIUM -- always-print approach is pragmatic but interpretation of D-11

**Research date:** 2026-04-08
**Valid until:** 2026-07-08 (Specfy is stable; subprocess stdlib never changes)
