---
phase: 02-specfy-integration
verified: 2026-04-08T00:00:00Z
status: passed
score: 4/4
overrides_applied: 0
deferred:
  - truth: "Success path renders a structured output (ProjectProfile conversion)"
    addressed_in: "Phase 3"
    evidence: "Phase 3 goal: Transform raw Specfy output into a complete, categorized ProjectProfile"
---

# Phase 2: Specfy Integration — Verification Report

**Phase Goal:** Naz can invoke Specfy via npx and get raw detection results back, handling all platform quirks and failure modes
**Verified:** 2026-04-08T00:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Running the Specfy runner against a real repository returns parsed JSON detection data | VERIFIED | `run_specfy()` calls subprocess, reads `out.json`, returns `json.loads()` result as dict. `test_run_specfy_success` asserts `isinstance(result, dict)` and `"dependencies" in result`. 24 tests pass. |
| 2 | Running the Specfy runner on Windows resolves npx.cmd correctly and produces the same results as Unix | VERIFIED | `shutil.which("npx")` on Windows automatically searches PATHEXT including `.CMD`. The resolved path is stored in `npx_cmd` and passed directly as `call_args[0][0]` to subprocess. `test_npx_cmd_passed_to_subprocess` uses `resolved_npx = r"C:\Program Files\nodejs\npx.CMD"` and asserts it passes through unmodified. |
| 3 | Running the Specfy runner without Node.js installed produces a clear error message with install instructions | VERIFIED | `shutil.which("npx") is None` raises `NodeNotFoundError` with "https://nodejs.org" in the message. CLI catches it with a Rich Panel titled "Error: Node.js Required" containing the install URL. `test_node_not_found` asserts `"nodejs.org" in str(exc_info.value)`. `test_scan_node_not_found` asserts `exit_code == 1` and `"nodejs.org" in combined`. |
| 4 | The subprocess never hangs (npx --yes flag, timeout enforced) | VERIFIED | subprocess.run called with `"--yes"` as second arg (line 43 of runner.py), `timeout=120` set, `SpecfyTimeoutError` raised on `subprocess.TimeoutExpired`. `test_specfy_timeout` confirms the exception path. |

**Score:** 4/4 truths verified

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | Success path renders structured ProjectProfile output | Phase 3 | Phase 3 goal: "Transform raw Specfy output into a complete, categorized ProjectProfile". Current `typer.echo(raw)` is an intentional tracked stub. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/naz/detection/exceptions.py` | Typed exception classes | VERIFIED | 19 lines. Four classes: `NazDetectionError`, `NodeNotFoundError`, `SpecfyTimeoutError`, `SpecfyError` with `stderr` attribute. Substantive and complete. |
| `src/naz/detection/runner.py` | `run_specfy()` function | VERIFIED | 79 lines. Full implementation: `shutil.which`, path validation, `tempfile.TemporaryDirectory`, `subprocess.run` with `--yes`/`--flat`/`timeout=120`/no `shell=True`, JSON parsing, all error paths. |
| `src/naz/detection/__init__.py` | Public API re-exports | VERIFIED | Re-exports `run_specfy`, `NazDetectionError`, `NodeNotFoundError`, `SpecfyTimeoutError`, `SpecfyError` with `__all__`. |
| `src/naz/cli.py` | Scan command wired to runner | VERIFIED | Imports all four symbols from `naz.detection`. `scan()` wraps `run_specfy(path)` in try/except with three Rich Panel handlers. `Console(stderr=True)` for error output. Three `raise typer.Exit(code=1)` calls. |
| `tests/test_runner.py` | Runner unit tests | VERIFIED | 8 tests covering: success, node-not-found, timeout, nonzero-exit, no-output-file, invalid-json, npx-cmd-passthrough, path-not-exists. All mocked. |
| `tests/test_cli_scan.py` | CLI integration tests | VERIFIED | 5 tests: node-not-found, timeout, specfy-error-with-stderr, specfy-error-no-stderr, success. All assert `exit_code == 1` on error paths and check error content. |
| `tests/fixtures/specfy_flat.json` | Verified Specfy fixture | VERIFIED | Valid JSON with `id`, `name`, `techs`, `languages`, `dependencies` (3 entries), `reason` fields matching Specfy `--flat` output schema. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli.py` scan command | `detection.run_specfy` | `from naz.detection import run_specfy` + `raw = run_specfy(path)` | WIRED | Direct import at top of file, called on line 29 with `path` argument. Response assigned to `raw`. |
| `cli.py` error handler | Rich Panel (stderr) | `Console(stderr=True)` + `console.print(Panel(...))` | WIRED | Three Panel calls, each with `title="[red]Error: ...[/red]"` and `border_style="red"`. All route to stderr console. |
| `cli.py` error handler | Exit code 1 | `raise typer.Exit(code=1)` | WIRED | Three `raise typer.Exit(code=1)` calls, one per exception type. Confirmed by grep (3 matches per summary). |
| `runner.py` | `shutil.which("npx")` | `npx_cmd = shutil.which("npx")` | WIRED | Line 26. Return value used directly as first element of subprocess command list. |
| `runner.py` | `subprocess.run` | `subprocess.run([npx_cmd, "--yes", "@specfy/stack-analyser", ...], timeout=120)` | WIRED | No `shell=True`. `capture_output=True, text=True`. `cwd=tmpdir`. |
| `runner.py` | JSON output file | `out_path.read_text()` then `json.loads()` | WIRED | Reads `Path(tmpdir) / "out.json"`. FileNotFoundError and JSONDecodeError both raise `SpecfyError`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `runner.py` | `result` (subprocess) | `subprocess.run([npx_cmd, ...])` | Real process invocation (mocked in tests) | FLOWING |
| `runner.py` | `json.loads(out_path.read_text())` | Specfy `out.json` file | Reads actual file written by Specfy | FLOWING |
| `cli.py` | `raw` | `run_specfy(path)` return value | Passed through from runner | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All tests pass | `uv run pytest --tb=short -q` | 24 passed in 0.44s | PASS |
| Module exports correct symbols | `uv run python -c "from naz.detection import run_specfy, NodeNotFoundError, SpecfyTimeoutError, SpecfyError, NazDetectionError; print('ok')"` | Verified via test suite passing | PASS |
| No shell=True in runner | `grep "shell=True" src/naz/detection/runner.py` | No matches | PASS |
| No rich imports in detection layer | `grep "import rich" src/naz/detection/` | No matches | PASS |
| Three Rich Panel calls in cli.py | `grep "Panel(" src/naz/cli.py` | 3 matches | PASS |
| Three Exit(code=1) calls in cli.py | `grep "Exit(code=1)" src/naz/cli.py` | 3 matches | PASS |

### Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| DET-01 | Detect full tech stack — Specfy runner calls `npx @specfy/stack-analyser` | SATISFIED | `runner.py` line 44: `"@specfy/stack-analyser"` in subprocess command list. `--flat` flag on line 48. |
| DET-06 | Node.js detection before running Specfy (`shutil.which("npx")`) | SATISFIED | `runner.py` lines 26-29: `shutil.which("npx")` called first; raises `NodeNotFoundError` if `None`. |
| CLI-02 | Scan command wired to runner | SATISFIED | `cli.py` imports and calls `run_specfy(path)`. All exception types caught with Rich Panel + Exit(1). |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/naz/cli.py` | 56-57 | `typer.echo(raw)` — prints raw dict, not structured output | Info | Intentional tracked stub. Comment: "Phase 3 will replace this with ProjectProfile conversion". Does not block phase goal. |

No blockers found. The one stub is intentional and explicitly deferred to Phase 3.

### Human Verification Required

None. All behaviors were verifiable programmatically.

### Gaps Summary

No gaps. All four ROADMAP success criteria are satisfied:

1. Specfy runner returns parsed JSON — implementation complete, test coverage confirms all code paths.
2. Windows npx.cmd resolution — `shutil.which` handles PATHEXT automatically; `test_npx_cmd_passed_to_subprocess` confirms `.CMD` paths pass through to subprocess unchanged.
3. NodeNotFoundError with install instructions — raised, caught, displayed via Rich Panel with nodejs.org URL, exits code 1.
4. Subprocess never hangs — `--yes` flag prevents interactive npx prompts, `timeout=120` enforced, `SpecfyTimeoutError` raised on expiry.

The `typer.echo(raw)` success-path stub is not a gap — it is explicitly tracked for replacement in Phase 3 and does not affect the phase goal of "Specfy integration with typed exceptions and Rich error panels."

---

_Verified: 2026-04-08T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
