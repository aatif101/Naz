# Phase 4: Output Rendering - Research

**Researched:** 2026-04-10
**Domain:** Rich terminal rendering, Pydantic JSON serialization, Typer boolean flags
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Terminal Layout**
- D-01: Multiple sections with separate Rich panels — one per logical group, not a single flat table
- D-02: Section order: Header → Languages → Technologies → Dependencies → AI/LLM
- D-03: Header shows the scanned path (e.g. `Scan complete: ./my-app`) before the panels
- D-04: Languages section shows each language with its line count
- D-05: Technologies section groups by category — each row shows `[category] name`
- D-06: Dependencies section shows the full dependency list with manager, name, and version (if present)
- D-07: AI/LLM section uses a visually distinct panel (e.g. yellow or magenta border) if `ai_dependencies` is non-empty; **omit the section entirely** if no AI deps are detected

**JSON Output**
- D-08: `--json` flag on `naz scan` switches to JSON output mode
- D-09: JSON output goes to stdout; Rich terminal summary is the default (no `--json`)
- D-10: JSON shape is `ProjectProfile.model_dump()` — full serialization of the Pydantic model (the `raw` field is already excluded via `exclude=True` in the model)
- D-11: When `--json` is active, suppress the Rich terminal summary entirely — stdout must be clean for piping

**Pipe / Non-Terminal Behavior**
- D-12: Use Rich's auto-detection — `Console()` without `force_terminal` automatically strips ANSI markup when stdout is not a TTY (pipe, file redirect, CI environment)
- D-13: No extra code needed for non-TTY handling — rely on Rich's default behavior

**Code Style**
- D-14: Simple, readable renderer — matches project constraint of no over-abstraction
- D-15: Renderer lives in `src/naz/renderer.py` — keeps output logic separate from CLI and detection
- D-16: Public function: `render(profile: ProjectProfile) -> None` — prints to stdout, no return value
- D-17: `cli.py` scan command calls `normalize(raw)` then `render(profile)` (terminal mode) or `print(profile.model_dump_json())` (JSON mode)

### Claude's Discretion
- Exact panel border colors and styles
- Column widths and alignment within each panel
- Whether to show a count summary line (e.g. "12 dependencies detected")
- Handling of empty sections other than AI/LLM (e.g. if no languages detected)

### Deferred Ideas (OUT OF SCOPE)
- OUT-03 (v2): AI-agent-optimized format — self-describing JSON for AI coding agents
- Verbosity levels / --verbose flag — not in scope for v0.1; simple summary only
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OUT-01 | Clean Rich terminal summary showing detected stack, dependency counts, infrastructure, services, and AI/LLM components | Rich Panel + Table patterns; renderer.py architecture |
| OUT-02 | Machine-readable JSON output of the project profile | Pydantic `model_dump_json()`; Typer `--json` boolean flag |
</phase_requirements>

---

## Summary

Phase 4 is a pure output phase: consume a `ProjectProfile` from `normalize()` and render it two ways. The terminal path uses Rich's Panel and Table components; the machine path uses Pydantic's built-in `model_dump_json()`. No new detection, no new models, no new subcommands.

All critical API choices are already locked by decisions D-01 through D-17. Rich's Console auto-detects TTY and strips ANSI codes automatically when stdout is piped — no special handling needed. Pydantic v2's `model_dump_json()` already excludes the `raw` field (it has `exclude=True`) so JSON output is correct with zero extra configuration.

The only non-trivial integration point is wiring `--json` into the existing `scan` command in `cli.py` and replacing the `typer.echo(raw)` stub that currently occupies the success path.

**Primary recommendation:** Write `renderer.py` as a single module with one public function `render(profile)`. Wire `--json` into `scan` using `typer.Option(False, "--json")`. Use a stdout `Console()` (not the stderr one already present) for the Rich output path.

---

## Standard Stack

All libraries are already installed — no new dependencies needed for this phase.

### Core (already in pyproject.toml)

| Library | Version (installed) | Purpose | Why |
|---------|---------------------|---------|-----|
| Rich | >=14.0.0 | Terminal panels and tables | Non-negotiable; Panel + Table + Console are all in this package |
| Pydantic | >=2.12.0 | JSON serialization | `model_dump_json()` is built in; `raw` field excluded automatically |
| Typer | >=0.24.0 | `--json` boolean flag | `typer.Option(False, "--json")` creates a flag-only option |

**No new packages to install.** [VERIFIED: pyproject.toml in codebase]

---

## Architecture Patterns

### Recommended File Layout

```
src/naz/
├── cli.py           # Add --json param; replace typer.echo(raw) stub
├── renderer.py      # NEW: render(profile: ProjectProfile) -> None
├── models.py        # Unchanged — ProjectProfile consumed directly
└── detection/
    └── normalizer.py  # Unchanged — normalize(raw) is Phase 4's input
```

### Pattern 1: renderer.py Structure

**What:** Single flat module, one public function, Rich primitives assembled inline.

**When to use:** Always — matches project constraint of no over-abstraction and flat function style.

```python
# src/naz/renderer.py
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from naz.models import ProjectProfile

_console = Console()  # stdout, auto-detects TTY


def render(profile: ProjectProfile) -> None:
    """Render ProjectProfile to the terminal as Rich panels."""
    # Header
    _console.print(f"[bold]Scan complete:[/bold] {profile.path}")

    # Languages panel
    ...

    # Technologies panel
    ...

    # Dependencies panel
    ...

    # AI/LLM panel (omit if empty)
    if profile.ai_dependencies:
        ...
```

**Key detail:** `_console = Console()` at module level is fine. Rich Console is not a singleton and is safe to construct once per module. [ASSUMED — common Rich usage pattern; consistent with existing `Console(stderr=True)` in cli.py]

### Pattern 2: Typer --json Flag

**What:** Boolean flag option with no negative counterpart. When passed, suppresses Rich output and prints JSON to stdout.

**When to use:** Exactly as specified in D-08 through D-11.

```python
# src/naz/cli.py — updated scan command signature
@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to the repository to scan"),
    json: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    ...
    raw = run_specfy(path)
    profile = normalize(raw)

    if json:
        print(profile.model_dump_json())  # stdlib print — clean stdout, no Rich
    else:
        render(profile)
```

`typer.Option(False, "--json")` creates only `--json` (no `--no-json` counterpart). [VERIFIED: Typer docs — https://typer.tiangolo.com/tutorial/parameter-types/bool/]

**Critical:** Use `print()` (stdlib) not `typer.echo()` for JSON output. `typer.echo()` adds a newline by default, which is fine, but the critical requirement is that stdout is CLEAN — no Rich markup. `print(profile.model_dump_json())` is the simplest correct form.

**Variable name conflict:** `json` as a parameter name shadows the stdlib `json` module. Since `cli.py` does not import the stdlib `json` module directly, this is not a problem. If it ever becomes one, rename the param to `as_json` and pass `"--json"` explicitly.

### Pattern 3: Rich Panel + Table

**What:** Rich Panel wraps a Table. Each section is one Panel.

```python
# Languages panel
table = Table(show_header=True, header_style="bold")
table.add_column("Language")
table.add_column("Lines", justify="right")
for lang, count in profile.languages.items():
    table.add_row(lang, str(count))
_console.print(Panel(table, title="Languages", border_style="blue"))

# Technologies panel — grouped by category
table = Table(show_header=True, header_style="bold")
table.add_column("Category")
table.add_column("Technology")
for tech in profile.technologies:
    table.add_row(tech.category, tech.name)
_console.print(Panel(table, title="Technologies", border_style="blue"))

# AI/LLM panel — visually distinct, omit if empty
if profile.ai_dependencies:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Manager")
    table.add_column("Package")
    table.add_column("Version")
    for dep in profile.ai_dependencies:
        table.add_row(dep.manager, dep.name, dep.version or "—")
    _console.print(Panel(table, title="AI / LLM Components", border_style="yellow"))
```

[ASSUMED — Rich Panel/Table constructor syntax from training knowledge; consistent with Rich 14.x API]

### Pattern 4: Rich Auto-TTY Stripping

**What:** `Console()` with no arguments auto-detects whether stdout is a TTY. When piped or redirected, Rich strips all ANSI escape codes and renders plain text. No code changes needed — this is the default behavior.

**Why this matters:** `naz scan . --json | jq .technologies` must work. The JSON path uses `print()` (no Rich), so no stripping needed there. The Rich path is only triggered without `--json`, and if someone pipes that output it will be plain text automatically.

[VERIFIED: Rich docs — Console auto-detection of TTY; confirmed by search result quoting Rich documentation: "If Rich detects that it is not writing to a terminal it will strip control codes from the output."]

### Pattern 5: Pydantic model_dump_json()

**What:** `ProjectProfile.model_dump_json()` serializes the full model to a JSON string. The `raw` field is decorated with `exclude=True` in models.py so it is automatically excluded.

```python
# Already correct — no extra configuration needed
print(profile.model_dump_json())

# For pretty-printed JSON (optional, not required by D-10):
print(profile.model_dump_json(indent=2))
```

[VERIFIED: models.py — `raw: dict = Field(default_factory=dict, exclude=True)` confirms automatic exclusion]

### Anti-Patterns to Avoid

- **Don't use `Console(stderr=True)` for the render output.** The existing error console in cli.py uses stderr — the render output must go to stdout so it can be piped and redirected. Create a separate `Console()` in renderer.py.
- **Don't import Click directly.** Typer wraps Click. Use `typer.Option`, not `click.option`.
- **Don't use `force_terminal=True`** on the stdout Console — this would prevent Rich from stripping ANSI codes when piped, breaking `naz scan . > out.txt`.
- **Don't hand-roll TTY detection.** Rich does it automatically. No `sys.stdout.isatty()` checks needed.
- **Don't mix Rich output and JSON output.** When `--json` is active, the render function must not be called at all (D-11). The branch must be exclusive in cli.py.
- **Don't name the param `json_output` in the function signature** if you also want `--json` on the CLI — Typer derives the flag name from the param name by default unless overridden. Use `typer.Option(False, "--json")` to force the flag name.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON serialization | Custom `to_dict()` + `json.dumps()` | `profile.model_dump_json()` | Pydantic v2 handles field exclusion, type coercion, None → null automatically |
| TTY detection | `sys.stdout.isatty()` checks | `Console()` default behavior | Rich handles pipe, redirect, CI, NO_COLOR env var automatically |
| ANSI stripping | Manual regex strip | Rich auto-detection | Rich's stripping is exhaustive; manual regex will miss edge cases |
| Table formatting | Manual string padding | `rich.table.Table` | Column alignment, overflow handling, Unicode width are non-trivial |

**Key insight:** Rich and Pydantic together eliminate all the hard parts of this phase. The implementation is wiring, not building.

---

## Common Pitfalls

### Pitfall 1: stdout vs stderr Console confusion

**What goes wrong:** Using the existing `console = Console(stderr=True)` from cli.py for render output. Rich output appears on stderr instead of stdout, breaking `naz scan . | grep python`.

**Why it happens:** cli.py already has a module-level `console` for errors. Easy to reuse it accidentally.

**How to avoid:** renderer.py creates its own `_console = Console()` (stdout). cli.py's console stays stderr-only for errors.

**Warning signs:** Test output shows Rich content in `result.stderr` instead of `result.output` in CliRunner tests.

### Pitfall 2: --json flag creates --no-json counterpart

**What goes wrong:** Using `json: bool = typer.Option(False)` without specifying `"--json"` explicitly. Typer auto-generates `--json/--no-json`, which is noisy help output and confusing UX.

**Why it happens:** Typer's default bool option behavior creates both positive and negative flags.

**How to avoid:** Always pass the explicit flag name: `typer.Option(False, "--json")`.

**Warning signs:** `naz scan --help` shows `--json/--no-json` instead of just `--json`.

### Pitfall 3: JSON output polluted by Rich

**What goes wrong:** `render(profile)` is called before the `--json` branch is checked, or the branch logic is inverted. Rich output lands in stdout mixed with JSON, breaking `jq` parsing.

**Why it happens:** Simple if/else ordering mistake.

**How to avoid:** The branch in cli.py must be exclusive — `if json: print(...) else: render(...)` — render is never called in JSON mode.

**Warning signs:** `naz scan . --json | python -m json.tool` fails with parse error.

### Pitfall 4: Empty sections crash or look broken

**What goes wrong:** `profile.languages` or `profile.technologies` is empty; the Table renders with zero rows, which looks odd or raises an error.

**Why it happens:** Empty lists are valid ProfileProject state (e.g., a project with no detectable languages).

**How to avoid:** For all sections except AI/LLM (which is omitted entirely), render the panel with a "None detected" row when the list is empty, or skip the table and print a plain message. Claude has discretion here per the locked decisions.

**Warning signs:** Tests with an empty-field ProfileProject produce panels with no content.

### Pitfall 5: model_dump_json() indentation not specified

**What goes wrong:** `profile.model_dump_json()` outputs a single-line compact JSON blob. `naz scan . --json > report.json` produces an unreadable file.

**Why it happens:** Pydantic defaults to compact output.

**How to avoid:** Use `profile.model_dump_json(indent=2)` for human-readable JSON files. The decision D-10 specifies the shape but not the indentation — this is Claude's discretion. Recommend `indent=2` for usability.

---

## Code Examples

### renderer.py skeleton (full module)

```python
# Source: derived from existing cli.py patterns + Rich docs
from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from naz.models import ProjectProfile

_console = Console()


def render(profile: ProjectProfile) -> None:
    """Render a ProjectProfile to the terminal as Rich panels.

    Sections: Header → Languages → Technologies → Dependencies → AI/LLM
    AI/LLM panel is omitted if no ai_dependencies are present.
    """
    # Header (D-03)
    _console.print(f"\n[bold]Scan complete:[/bold] {profile.path}\n")

    # Languages (D-04)
    _render_languages(profile)

    # Technologies (D-05)
    _render_technologies(profile)

    # Dependencies (D-06)
    _render_dependencies(profile)

    # AI/LLM — omit if empty (D-07)
    if profile.ai_dependencies:
        _render_ai(profile)


def _render_languages(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Language")
    table.add_column("Lines", justify="right")
    if profile.languages:
        for lang, count in profile.languages.items():
            table.add_row(lang, str(count))
    else:
        table.add_row("[dim]None detected[/dim]", "")
    _console.print(Panel(table, title="Languages", border_style="blue"))


def _render_technologies(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Category")
    table.add_column("Technology")
    if profile.technologies:
        for tech in profile.technologies:
            table.add_row(tech.category, tech.name)
    else:
        table.add_row("[dim]None detected[/dim]", "")
    _console.print(Panel(table, title="Technologies", border_style="blue"))


def _render_dependencies(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Manager")
    table.add_column("Package")
    table.add_column("Version")
    if profile.dependencies:
        for dep in profile.dependencies:
            table.add_row(dep.manager, dep.name, dep.version or "—")
    else:
        table.add_row("[dim]None detected[/dim]", "", "")
    count = len(profile.dependencies)
    _console.print(Panel(table, title=f"Dependencies ({count})", border_style="blue"))


def _render_ai(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Manager")
    table.add_column("Package")
    table.add_column("Version")
    for dep in profile.ai_dependencies:
        table.add_row(dep.manager, dep.name, dep.version or "—")
    count = len(profile.ai_dependencies)
    _console.print(Panel(
        table,
        title=f"[bold magenta]AI / LLM Components ({count})[/bold magenta]",
        border_style="yellow",
    ))
```

### cli.py updated scan command

```python
# Source: cli.py + Typer docs pattern
@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to the repository to scan"),
    json: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
) -> None:
    """Scan a repository and detect its technology stack."""
    try:
        raw = run_specfy(path)
    except NodeNotFoundError:
        ...  # error handling unchanged
    except SpecfyTimeoutError:
        ...
    except SpecfyError as exc:
        ...

    from naz.detection.normalizer import normalize
    from naz.renderer import render

    profile = normalize(raw)

    if json:
        print(profile.model_dump_json(indent=2))
    else:
        render(profile)
```

### Test pattern for renderer

```python
# Uses CliRunner with mocked run_specfy returning a full flat dict
from unittest.mock import patch
from typer.testing import CliRunner
from naz.cli import app

runner = CliRunner()

FIXTURE = {
    "path": ["/", "my-app"],
    "techs": ["python", "fastapi"],
    "languages": {"Python": 1200},
    "dependencies": [["python", "typer", "0.24.0"]],
    "childs": [],
}

def test_scan_renders_stack():
    with patch("naz.cli.run_specfy", return_value=FIXTURE):
        result = runner.invoke(app, ["scan", "."])
    assert result.exit_code == 0
    assert "Languages" in result.output
    assert "Technologies" in result.output

def test_scan_json_output_is_valid():
    import json
    with patch("naz.cli.run_specfy", return_value=FIXTURE):
        result = runner.invoke(app, ["scan", ".", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)  # must not raise
    assert "technologies" in data
    assert "raw" not in data  # excluded field
```

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.x |
| Config file | pyproject.toml (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run pytest tests/test_renderer.py tests/test_cli_scan.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| OUT-01 | Rich panels appear in stdout for scan success | Integration (CliRunner) | `uv run pytest tests/test_cli_scan.py -x` | Partially — test_scan_success needs update |
| OUT-01 | Languages/Technologies/Dependencies panels present | Integration (CliRunner) | `uv run pytest tests/test_renderer.py -x` | Wave 0 gap |
| OUT-01 | AI/LLM panel shown when ai_dependencies present | Integration (CliRunner) | `uv run pytest tests/test_renderer.py -x` | Wave 0 gap |
| OUT-01 | AI/LLM panel omitted when ai_dependencies empty | Integration (CliRunner) | `uv run pytest tests/test_renderer.py -x` | Wave 0 gap |
| OUT-02 | `--json` flag produces valid JSON on stdout | Integration (CliRunner) | `uv run pytest tests/test_cli_scan.py -x` | Wave 0 gap |
| OUT-02 | JSON output excludes `raw` field | Unit | `uv run pytest tests/test_renderer.py -x` | Wave 0 gap |
| OUT-02 | Rich output absent when `--json` active | Integration (CliRunner) | `uv run pytest tests/test_cli_scan.py -x` | Wave 0 gap |

### Sampling Rate

- Per task commit: `uv run pytest tests/test_renderer.py tests/test_cli_scan.py -x`
- Per wave merge: `uv run pytest`
- Phase gate: Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_renderer.py` — new file; covers OUT-01 panel rendering, AI section conditional, empty-section handling
- [ ] `tests/test_cli_scan.py` — update `test_scan_success` to assert on panel output, not raw dict; add `--json` tests

*(No framework install needed — pytest already in dev dependencies)*

---

## Project Constraints (from CLAUDE.md)

| Directive | Applies to Phase 4? | Impact |
|-----------|---------------------|--------|
| Language: Python | Yes | renderer.py is Python |
| CLI framework: Typer — non-negotiable | Yes | `--json` flag uses `typer.Option` |
| Terminal output: Rich — non-negotiable | Yes | All terminal rendering uses Rich |
| Code style: simple, no over-abstraction | Yes | No renderer class hierarchy; flat functions only |
| Never use Click directly | Yes | No `import click` in renderer.py or cli.py |
| Never use `shell=True` in subprocess | No — no subprocess in this phase | N/A |
| Paths: use pathlib, not os.path | No — no path handling in renderer | N/A |
| Tests: CliRunner for CLI, mock subprocess | Yes | All CLI tests use CliRunner; run_specfy mocked |
| `from __future__ import annotations` at top of every module | Yes | renderer.py must include this |

---

## Integration Points (Existing Code)

These are confirmed by reading the actual source files:

**cli.py current state:**
- `typer.echo(raw)` on line 57 is the stub to replace — confirmed present [VERIFIED: cli.py]
- `console = Console(stderr=True)` at module level — error console stays; do not reuse for render [VERIFIED: cli.py]
- `run_specfy` imported from `naz.detection` — normalize and render will be imported locally or at top [VERIFIED: cli.py]

**models.py confirmed fields:**
- `ProjectProfile.path: str` — used in Header (D-03)
- `ProjectProfile.languages: dict[str, int]` — lang → line count (D-04)
- `ProjectProfile.technologies: list[Technology]` — Technology has `.name` and `.category` (D-05)
- `ProjectProfile.dependencies: list[Dependency]` — Dependency has `.manager`, `.name`, `.version: str | None` (D-06)
- `ProjectProfile.ai_dependencies: list[Dependency]` — same shape as dependencies (D-07)
- `ProjectProfile.raw` — `exclude=True`, so absent from `model_dump_json()` (D-10)
[VERIFIED: models.py]

**normalizer.py** — `normalize(raw: dict) -> ProjectProfile` — already production-ready, no changes needed [VERIFIED: normalizer.py]

**Test fixture** — `tests/fixtures/specfy_flat.json` exists with a representative payload (2 techs, 2 languages, 3 deps, no AI deps). Adequate for most tests; a second fixture with AI deps would be useful. [VERIFIED: fixtures directory]

**Existing test_scan_success:** Currently asserts `"python" in result.output` after mocking run_specfy to return a raw dict. This test will break after Phase 4 wires in normalize+render because the output format changes. It must be updated as part of this phase. [VERIFIED: test_cli_scan.py line 72-82]

---

## Open Questions

1. **`normalize` import location in cli.py**
   - What we know: `run_specfy` is imported at module level; `normalize` is not currently imported
   - What's unclear: Import at module top vs. lazily inside the function body
   - Recommendation: Import at module top alongside `run_specfy` for consistency with the existing pattern

2. **Empty `technologies` list display**
   - What we know: D-07 specifies AI/LLM panel is omitted when empty; other sections have no explicit empty-state decision
   - What's unclear: Should Languages/Technologies/Dependencies panels show "None detected" or be omitted entirely?
   - Recommendation: Show a "None detected" row rather than omitting — a visible panel communicates "we looked and found nothing," which is more informative than silence

3. **`model_dump_json(indent=2)` vs compact**
   - What we know: D-10 specifies JSON shape but not formatting; primary use case is piping to jq and file redirect
   - What's unclear: jq handles both compact and indented; file redirect is more readable with indent
   - Recommendation: Use `indent=2` — minimal cost, improves readability of `> report.json` use case

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_console = Console()` at module level in renderer.py is safe (not a singleton issue) | Architecture Patterns | Low — worst case move inside `render()` function; no correctness impact |
| A2 | Rich Panel and Table constructor signatures match the code examples given | Code Examples | Low — Rich 14.x API is stable; easy to fix at implementation time |
| A3 | `typer.Option(False, "--json")` creates only `--json` with no `--no-json` counterpart | Architecture Patterns | Medium — verified via Typer docs; if wrong, rename param and add is_flag=True |

---

## Sources

### Primary (HIGH confidence)
- [VERIFIED: cli.py, models.py, normalizer.py, pyproject.toml] — direct codebase reads
- [VERIFIED: tests/test_cli_scan.py, tests/fixtures/specfy_flat.json] — direct codebase reads
- [VERIFIED: Typer docs — https://typer.tiangolo.com/tutorial/parameter-types/bool/] — boolean flag syntax confirmed via WebFetch

### Secondary (MEDIUM confidence)
- [CITED: Rich docs search result] — Console auto-strips ANSI when not TTY; `force_terminal=True` overrides; Rich 14.2.0 is current as of Jan 2026

### Tertiary (LOW confidence)
- None — all critical claims are VERIFIED or CITED

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, confirmed in pyproject.toml
- Architecture: HIGH — all decisions locked in CONTEXT.md; existing code patterns confirmed
- Pitfalls: HIGH — derived from actual codebase state (stub line identified, stderr/stdout confusion identified from existing console var)
- Test gaps: HIGH — test files read directly; gap list is exhaustive

**Research date:** 2026-04-10
**Valid until:** 2026-05-10 (Rich 14.x API is stable)
