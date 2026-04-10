---
phase: 04-output-rendering
plan: "02"
subsystem: cli
tags: [cli, renderer, json, typer, tdd]
dependency_graph:
  requires: [naz.renderer.render, naz.detection.normalizer.normalize, naz.models.ProjectProfile]
  provides: [naz scan --json flag, OUT-01 wired end-to-end, OUT-02 machine-readable JSON]
  affects: [src/naz/cli.py, tests/test_cli_scan.py]
tech_stack:
  added: []
  patterns: [typer.Option(False, "--json") for singular boolean flag, stdlib print() for pipe-clean JSON output]
key_files:
  created: []
  modified:
    - src/naz/cli.py
    - tests/test_cli_scan.py
decisions:
  - "Use typer.Option(False, '--json') with explicit flag name to produce singular --json (not --json/--no-json)"
  - "Use stdlib print() for JSON output, not typer.echo() or console.print(), to keep stdout pipe-clean"
  - "normalize() + render() called sequentially in scan command; render() never called when --json is True"
metrics:
  duration: "5 minutes"
  completed: "2026-04-10"
  tasks_completed: 2
  files_changed: 2
---

# Phase 04 Plan 02: CLI Wiring Summary

**One-liner:** Wired normalize()+render() into scan command and added --json flag using typer.Option(False, "--json") with stdlib print() for pipe-clean JSON output.

## What Was Built

Modified `src/naz/cli.py` to replace the `typer.echo(raw)` stub with a full success path: `normalize(raw)` converts the Specfy dict to a `ProjectProfile`, then either `render(profile)` (default) or `print(profile.model_dump_json(indent=2))` (when `--json` is active). The `--json` flag is a singular boolean option (not a toggle pair) using `typer.Option(False, "--json")`.

Updated `tests/test_cli_scan.py`: replaced the old raw-dict success assertion with panel title assertions, and added 4 new JSON flag tests covering valid JSON output, `raw` field exclusion, `technologies` key presence, and Rich panel suppression.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Update cli.py — add --json flag and replace typer.echo(raw) stub | 9336a34 | src/naz/cli.py |
| 2 | Update tests/test_cli_scan.py — fix success test, add JSON tests | 765b555 | tests/test_cli_scan.py |

## Decisions Made

1. `typer.Option(False, "--json")` — passing the explicit flag name `"--json"` as the second positional argument to `typer.Option` produces a singular `--json` flag in the help text. Without it, Typer generates `--json/--no-json` for boolean options.
2. `print(profile.model_dump_json(indent=2))` — stdlib `print()` is used (not `typer.echo()`, not `console.print()`) so that stdout contains only raw JSON with no Rich markup, making it safe for piping to `python -m json.tool` or other consumers.
3. `render()` is never called when `--json` is True — the if/else branch ensures no Rich panels contaminate JSON output (D-11 from 04-CONTEXT.md).

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| `uv run pytest` — full suite 54/54 | PASS |
| `uv run naz scan --help` shows `--json`, not `--json/--no-json` | PASS |
| JSON output contains `technologies`, excludes `raw` | PASS |
| Rich panels appear in default (no --json) mode | PASS |
| `typer.echo(raw)` stub removed | PASS |
| normalize and render imported at module top-level | PASS |

## Known Stubs

None — cli.py success path is fully wired. No placeholder output remains.

## Threat Flags

No new security-relevant surface introduced beyond the plan's threat model (T-04-06 through T-04-09 accepted as documented).

## Self-Check

- [x] src/naz/cli.py modified with --json flag, normalize+render imports, stub removed
- [x] tests/test_cli_scan.py has 9 tests: 4 error + 1 success (panels) + 4 JSON
- [x] Commits 9336a34 and 765b555 exist in git log
- [x] Full suite: 54 passed
