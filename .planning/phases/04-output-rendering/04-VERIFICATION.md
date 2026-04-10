---
phase: 04-output-rendering
verified: 2026-04-10T00:00:00Z
status: human_needed
score: 3/3 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run `naz scan .` in a real terminal against a repo that includes openai as a dependency. Confirm the AI / LLM panel renders with a yellow border."
    expected: "Panel titled 'AI / LLM Components (N)' appears with a visually distinct yellow border. Border is not blue like the other panels."
    why_human: "CliRunner strips ANSI codes. Color rendering requires a real TTY to confirm. Automated tests only verify panel title presence, not border color."
  - test: "Run `naz scan . | cat` in a real terminal against any repository."
    expected: "Output is readable plain text — panel content visible with no garbage ANSI escape sequences or broken characters. Output degraded but not garbled."
    why_human: "Rich's TTY auto-detection only activates when stdout is a real pipe. CliRunner does not simulate pipe mode; Console() behaviour in a piped shell requires manual validation."
---

# Phase 4: Output Rendering Verification Report

**Phase Goal:** Users see a clear, formatted terminal summary of their project's technology stack, and can get machine-readable JSON
**Verified:** 2026-04-10
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A Rich-formatted terminal summary displays the detected stack, dependency counts, infrastructure, services, and AI/LLM components | VERIFIED | `test_render_languages_panel`, `test_render_technologies_panel`, `test_render_dependencies_panel`, `test_render_ai_panel_when_present`, `test_render_no_ai_panel_when_empty` all pass. `render()` in renderer.py produces Languages, Technologies, Dependencies, and conditional AI/LLM panels. |
| 2 | A JSON output of the complete ProjectProfile can be produced for machine consumption | VERIFIED | `test_scan_json_flag_produces_valid_json`, `test_scan_json_contains_technologies`, `test_scan_json_excludes_raw_field` all pass. `--json` flag wired in cli.py via `typer.Option(False, "--json")`. `print(profile.model_dump_json(indent=2))` produces pipe-clean JSON with keys: path, technologies, languages, dependencies, ai_dependencies, components. `raw` field correctly excluded. |
| 3 | Output renders correctly when piped or in non-terminal contexts (no Rich markup in plain text) | VERIFIED (automated) / HUMAN NEEDED (visual) | `_console = Console()` with no `force_terminal` argument — Rich auto-detects TTY and strips ANSI when piped (D-12, D-13). `test_render_stdout_not_stderr` confirms Rich output goes to stdout. JSON path uses stdlib `print()`, producing markup-free output. Manual pipe test needed to confirm readable plain text in real shell. |

**Score:** 3/3 truths verified (automated checks pass; 2 human items for visual/pipe confirmation)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/naz/renderer.py` | Rich terminal renderer with Languages, Technologies, Dependencies, AI/LLM panels | VERIFIED | 104 lines, substantive. Exports `render(profile)`. Four panel-rendering helpers. `escape()` applied to all Specfy-derived strings (9 call sites: profile.path, lang names, tech.category, tech.name, dep.manager, dep.name, dep.version). `_console = Console()` at module level for stdout. |
| `src/naz/cli.py` | scan command with --json flag; calls normalize() then render() or print(model_dump_json()) | VERIFIED | Imports `normalize` and `render` at module top-level. `typer.Option(False, "--json")` produces singular `--json` (confirmed via `naz scan --help`). Success path: `profile = normalize(raw)` then branch on `json`. Stub `typer.echo(raw)` removed. Error handlers unchanged. |
| `tests/test_renderer.py` | 8 tests for Rich panel output via CLI | VERIFIED | 8 tests, all passing. Tests via CliRunner — exercises the full normalize→render pipeline using specfy_flat.json and specfy_ai.json fixtures. |
| `tests/test_cli_scan.py` | Updated success test + 4 new --json tests; all 4 prior error tests unchanged | VERIFIED | 9 tests total: 4 error paths (unchanged), 1 success (panel titles), 4 JSON tests. All 9 pass. |
| `tests/fixtures/specfy_ai.json` | AI fixture with openai dependency | VERIFIED | Exists. Contains `["python", "openai", "1.30.0"]` dependency, triggering AI detection. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/naz/cli.py` | `src/naz/renderer.py` | `from naz.renderer import render` | WIRED | Import at module top-level (line 14). `render(profile)` called in else branch of success path (line 64). |
| `src/naz/cli.py` | `src/naz/detection/normalizer.py` | `from naz.detection.normalizer import normalize` | WIRED | Import at module top-level (line 13). `normalize(raw)` called as first step of success path (line 59). |
| `tests/test_cli_scan.py` | `naz.cli.run_specfy` | `patch('naz.cli.run_specfy', return_value=...)` | WIRED | All 9 tests use this patch. Fixture FLAT loaded from specfy_flat.json at module level. |
| `tests/test_renderer.py` | `naz.cli.run_specfy` | `patch('naz.cli.run_specfy', return_value=FLAT/AI)` | WIRED | All 8 tests patch run_specfy and invoke via CliRunner, exercising the full cli→normalize→render pipeline. |
| `src/naz/renderer.py` | `naz.models.ProjectProfile` | `from naz.models import ProjectProfile` | WIRED | Type annotation on `render()` parameter. All four helpers consume profile fields directly. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `src/naz/renderer.py` | `profile.languages` | `normalize(raw)` in cli.py; populated from Specfy `languages` dict | Yes — normalizer maps raw dict to typed Pydantic model | FLOWING |
| `src/naz/renderer.py` | `profile.technologies` | `normalize(raw)` — maps `techs` list to `Technology` objects | Yes | FLOWING |
| `src/naz/renderer.py` | `profile.dependencies` | `normalize(raw)` — maps `dependencies` list to `Dependency` objects | Yes | FLOWING |
| `src/naz/renderer.py` | `profile.ai_dependencies` | `normalize(raw)` — filters dependencies against AI package list | Yes — test_render_ai_panel_when_present confirms openai fixture triggers this path | FLOWING |
| `src/naz/cli.py` (--json path) | `profile.model_dump_json()` | Pydantic serialization of the same `normalize(raw)` output | Yes — JSON output verified to contain real data from fixture | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| --json flag is singular (not --json/--no-json) | `uv run naz scan --help` | Output shows `--json` only; `--no-json` absent | PASS |
| JSON output contains technologies, excludes raw | Python one-liner with mocked run_specfy | Keys: path, technologies, languages, dependencies, ai_dependencies, components — no `raw` | PASS |
| Rich panels appear in default (no --json) mode | Python one-liner with mocked run_specfy | `Languages`, `Technologies`, `Scan complete` all in stdout | PASS |
| Full test suite green | `uv run pytest` | 54 passed, 0 failed | PASS |
| Target tests green | `uv run pytest tests/test_renderer.py tests/test_cli_scan.py -v` | 17/17 passed | PASS |
| No markup in --json stdout | Checked `[bold]` not in JSON output | No Rich markup strings present | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| OUT-01 | 04-01-PLAN (renderer), 04-02-PLAN (wiring) | Rich terminal summary: stack, dependency counts, infrastructure, services, AI/LLM | SATISFIED | renderer.py implements all four panels; wired into scan command; 8 renderer tests + test_scan_success confirm panel titles in stdout |
| OUT-02 | 04-02-PLAN | Machine-readable JSON output | SATISFIED | `--json` flag wired; `model_dump_json(indent=2)` via stdlib print(); 4 JSON tests pass; `raw` field excluded via Pydantic `exclude=True` |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | — |

Scan notes:
- No TODO/FIXME/placeholder comments in renderer.py or cli.py
- `typer.echo(raw)` stub confirmed removed from cli.py
- No `return null` / `return []` / empty handler patterns in implementation files
- `_console = Console()` at module level — not a stub, a real Rich console
- `escape()` applied consistently (9 call sites) — security mitigation, not a stub

---

### Human Verification Required

#### 1. AI/LLM Panel Yellow Border

**Test:** In a real terminal (not CliRunner), run `naz scan .` against a repository that has `openai` (or any other AI package) as a dependency. The `tests/fixtures/specfy_ai.json` fixture can be used by temporarily patching, or point the tool at a real Python project with openai installed.

**Expected:** The AI / LLM Components panel renders with a yellow border, visually distinct from the blue-bordered Languages, Technologies, and Dependencies panels.

**Why human:** CliRunner strips ANSI escape codes. The `border_style="yellow"` in `_render_ai()` can only be confirmed in a real TTY environment.

#### 2. Pipe / Non-Terminal Plain Text

**Test:** In a real terminal shell, run `naz scan . | cat` against any repository (or `naz scan . > /tmp/out.txt` then inspect the file).

**Expected:** Output is readable plain text. Panel borders appear as ASCII characters. Language names, tech names, and dependency names are visible. No garbage escape sequences (e.g., no `\x1b[33m` or similar). Content is degraded but not garbled.

**Why human:** Rich's TTY auto-detection triggers on the actual OS pipe file descriptor. CliRunner does not replicate this. `Console()` without `force_terminal` is the correct implementation per D-12/D-13, but visual confirmation of the degraded output is a manual step noted in 04-VALIDATION.md.

---

### Gaps Summary

No automated gaps. All three roadmap success criteria are verified by tests and spot-checks. Two human verification items remain from the project's own VALIDATION.md — both are visual/TTY-specific behaviors that cannot be tested programmatically. The implementation is correct; the human tests confirm it looks right in a real terminal.

---

_Verified: 2026-04-10_
_Verifier: Claude (gsd-verifier)_
