---
phase: 02-specfy-integration
plan: "02"
subsystem: cli
tags: [cli, rich, error-handling, typer, specfy, integration-tests]
dependency_graph:
  requires: [02-01]
  provides: [scan-command-wired, rich-error-panels, cli-scan-tests]
  affects: [src/naz/cli.py, tests/test_cli_scan.py, tests/test_cli.py]
tech_stack:
  added: []
  patterns: [rich-stderr-console, typed-exception-catch, typer-exit-code]
key_files:
  created:
    - tests/test_cli_scan.py
  modified:
    - src/naz/cli.py
    - tests/test_cli.py
decisions:
  - "Console(stderr=True) routes error panels to stderr so stdout stays clean for piping"
  - "exc.stderr[:500] truncates Specfy error output to prevent large terminal dumps (T-02-05)"
  - "CliRunner() used without mix_stderr — Typer version in this project does not support the kwarg"
  - "typer.echo(raw) as temporary success path until Phase 3 adds ProjectProfile conversion"
metrics:
  duration: "~10 min"
  completed: "2026-04-08"
  tasks_completed: 2
  files_changed: 3
---

# Phase 2 Plan 2: CLI Scan Wiring Summary

**One-liner:** Scan command wired to run_specfy with three Rich error panels (NodeNotFoundError, SpecfyTimeoutError, SpecfyError) writing to stderr, all exiting code 1 cleanly.

## What Was Built

Updated `src/naz/cli.py` to call `run_specfy(path)` and catch all three typed exceptions from the detection layer. Each failure mode displays a Rich `Panel` to stderr with an actionable message: Node.js install URL, smaller-directory suggestion, or Specfy stderr excerpt (truncated to 500 chars). Success path prints the raw dict via `typer.echo` (Phase 3 will replace with ProjectProfile conversion). Added 5 integration tests in `test_cli_scan.py` and updated existing scan tests in `test_cli.py` to mock the runner.

### Files Modified

- **`src/naz/cli.py`** — Imports `run_specfy`, `NodeNotFoundError`, `SpecfyTimeoutError`, `SpecfyError` from detection layer. `scan()` command wraps `run_specfy(path)` in try/except with three Rich Panel error outputs writing to stderr. `Console(stderr=True)` used so error output doesn't pollute stdout.
- **`tests/test_cli_scan.py`** (new) — 5 integration tests using `CliRunner`: node-not-found, timeout, specfy-error-with-stderr, specfy-error-no-stderr, success path.
- **`tests/test_cli.py`** (updated) — `test_scan_default_path` and `test_scan_custom_path` now mock `naz.cli.run_specfy`. `test_scan_custom_path` asserts `mock.assert_called_once_with("/some/path")`.

## Verification Results

```
uv run pytest tests/test_cli_scan.py tests/test_cli.py -x -q  → 9 passed
uv run pytest tests/ -x -q                                      → 24 passed
grep -r "import rich" src/naz/detection/                        → (no results — detection Rich-free)
grep "Panel(" src/naz/cli.py                                    → 3 matches
grep "Exit(code=1)" src/naz/cli.py                              → 3 matches
grep "stderr=True" src/naz/cli.py                               → 1 match
```

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 6125908 | Integration tests and updated existing CLI scan tests |
| Task 2 | b9dbcb5 | Scan command wired to runner with Rich error panels |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CliRunner `mix_stderr=False` not supported by installed Typer version**

- **Found during:** Task 1 verification — import check failed with `TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'`
- **Issue:** Plan specified `CliRunner(mix_stderr=False)` but the Typer version installed (likely 0.9.x range based on error) does not support this kwarg
- **Fix:** Changed to `CliRunner()` (default). Tests use `result.output + (result.stderr or "")` combined check to handle merged output gracefully
- **Files modified:** `tests/test_cli_scan.py`
- **Commit:** 6125908 (same commit, fixed before commit)

## Known Stubs

One intentional stub: `typer.echo(raw)` in the scan success path prints the raw dict. This is tracked — Phase 3 will replace it with ProjectProfile conversion and a Rich-formatted summary table. The stub does not block the plan's goal (CLI scan wiring with error panels is complete).

## Threat Surface Scan

No new network endpoints or auth paths. The scan command passes `path` argument directly to `run_specfy()` which validates path existence and uses no shell=True — consistent with T-02-01. The `exc.stderr[:500]` truncation implements T-02-05. Rich markup in error panels uses hardcoded strings only — no user-controlled markup injection (T-02-06).

## Self-Check: PASSED

- `tests/test_cli_scan.py` — FOUND
- `src/naz/cli.py` — FOUND (modified)
- `tests/test_cli.py` — FOUND (modified)
- Commit 6125908 — FOUND
- Commit b9dbcb5 — FOUND
