---
phase: 02-specfy-integration
plan: "01"
subsystem: detection
tags: [subprocess, specfy, exceptions, testing, npx]
dependency_graph:
  requires: [01-02]
  provides: [run_specfy, NodeNotFoundError, SpecfyTimeoutError, SpecfyError, NazDetectionError]
  affects: [src/naz/detection/]
tech_stack:
  added: []
  patterns: [temp-dir-capture, typed-exceptions, shutil-which-resolution]
key_files:
  created:
    - src/naz/detection/exceptions.py
    - src/naz/detection/runner.py
    - tests/fixtures/specfy_flat.json
    - tests/test_runner.py
  modified:
    - src/naz/detection/__init__.py
decisions:
  - "Use existing tmp_path subdirs as scan targets in tests (path validation runs before subprocess mock)"
  - "Always print first-run message before npx invocation (D-11) using stdlib print(), not typer.echo()"
  - "Separate out_dir from scan_dir in tests to avoid fixture collision"
metrics:
  duration: "~15 min"
  completed: "2026-04-08"
  tasks_completed: 2
  files_changed: 5
---

# Phase 2 Plan 1: Specfy Subprocess Runner Summary

**One-liner:** Typed subprocess runner for Specfy stack-analyser using temp-dir file capture with `shutil.which` npx resolution and four typed exception classes.

## What Was Built

A detection layer module (`src/naz/detection/`) that invokes `npx @specfy/stack-analyser` via subprocess, captures JSON output from a temporary directory, and returns the raw dict. All failure modes raise typed exceptions that the CLI layer catches in Plan 02.

### Files Created

- **`src/naz/detection/exceptions.py`** — Four exception classes: `NazDetectionError` (base), `NodeNotFoundError`, `SpecfyTimeoutError`, `SpecfyError` (with `stderr` attribute)
- **`src/naz/detection/runner.py`** — `run_specfy(path)` function implementing temp-dir capture pattern, `shutil.which` npx resolution, 120s timeout, no `shell=True`
- **`src/naz/detection/__init__.py`** — Re-exports `run_specfy` and all four exception classes as public API
- **`tests/fixtures/specfy_flat.json`** — Verified Specfy `--flat` output schema with 3 dependencies
- **`tests/test_runner.py`** — 8 unit tests covering all failure modes with mocked subprocess

## Verification Results

```
uv run pytest tests/test_runner.py -x -q   → 8 passed
uv run pytest tests/ -x -q                 → 19 passed (full suite green)
from naz.detection import run_specfy, ...  → imports OK
grep -r "import rich" src/naz/detection/   → no results (detection layer Rich-free)
grep -r "shell=True" src/naz/detection/    → no results
```

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | f0ac6cb | Exception classes, Specfy fixture, runner test stubs |
| Task 2 | acc3fe1 | run_specfy implementation, __init__ re-exports, test fixes |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test stubs used non-existent path `/some/repo` as scan target**

- **Found during:** Task 2 GREEN phase — tests failed because path validation runs before subprocess mock
- **Issue:** Tests patching `shutil.which` and `subprocess.run` still failed because `Path("/some/repo").exists()` returns False before reaching the mocked subprocess call
- **Fix:** Replaced `/some/repo` with `tmp_path / "repo"` (a real directory created via `mkdir()`) in all affected tests. Used separate `out_dir = tmp_path / "out"` for the TemporaryDirectory mock to avoid fixture file collision. `test_node_not_found` and `test_path_not_exists` were unaffected (they raise before or at the path check)
- **Files modified:** `tests/test_runner.py`
- **Commit:** acc3fe1

## Known Stubs

None — all code paths are fully implemented and tested.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns beyond what the plan's threat model covers. The `run_specfy` function passes `path` as a list element to `subprocess.run` (no shell injection), validates path existence before invocation, and enforces 120s timeout — all per the T-02-01 and T-02-03 mitigations.

## Self-Check: PASSED

- `src/naz/detection/exceptions.py` — FOUND
- `src/naz/detection/runner.py` — FOUND
- `src/naz/detection/__init__.py` — FOUND (updated)
- `tests/fixtures/specfy_flat.json` — FOUND
- `tests/test_runner.py` — FOUND
- Commit f0ac6cb — FOUND
- Commit acc3fe1 — FOUND
