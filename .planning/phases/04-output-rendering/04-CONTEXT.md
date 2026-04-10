# Phase 4: Output Rendering - Context

**Gathered:** 2026-04-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Consume a `ProjectProfile` (produced by Phase 3's `normalize()`) and render two outputs:
1. A Rich terminal summary to stdout — human-readable, formatted with panels
2. A machine-readable JSON output to stdout — triggered by `--json` flag

This phase owns the renderer and wires it into the existing `naz scan` command. No new CLI subcommands, no new detection logic, no changes to ProjectProfile schema.

</domain>

<decisions>
## Implementation Decisions

### Terminal Layout
- **D-01:** Multiple sections with separate Rich panels — one per logical group, not a single flat table
- **D-02:** Section order: Header → Languages → Technologies → Dependencies → AI/LLM
- **D-03:** Header shows the scanned path (e.g. `Scan complete: ./my-app`) before the panels
- **D-04:** Languages section shows each language with its line count
- **D-05:** Technologies section groups by category — each row shows `[category] name`
- **D-06:** Dependencies section shows the full dependency list with manager, name, and version (if present)
- **D-07:** AI/LLM section uses a visually distinct panel (e.g. yellow or magenta border) if `ai_dependencies` is non-empty; **omit the section entirely** if no AI deps are detected

### JSON Output
- **D-08:** `--json` flag on `naz scan` switches to JSON output mode
- **D-09:** JSON output goes to stdout; Rich terminal summary is the default (no `--json`)
- **D-10:** JSON shape is `ProjectProfile.model_dump()` — full serialization of the Pydantic model (the `raw` field is already excluded via `exclude=True` in the model)
- **D-11:** When `--json` is active, suppress the Rich terminal summary entirely — stdout must be clean for piping

### Pipe / Non-Terminal Behavior
- **D-12:** Use Rich's auto-detection — `Console()` without `force_terminal` automatically strips ANSI markup when stdout is not a TTY (pipe, file redirect, CI environment)
- **D-13:** No extra code needed for non-TTY handling — rely on Rich's default behavior

### Code Style
- **D-14:** Simple, readable renderer — matches project constraint of no over-abstraction
- **D-15:** Renderer lives in `src/naz/renderer.py` — keeps output logic separate from CLI and detection
- **D-16:** Public function: `render(profile: ProjectProfile) -> None` — prints to stdout, no return value
- **D-17:** `cli.py` scan command calls `normalize(raw)` then `render(profile)` (terminal mode) or `print(profile.model_dump_json())` (JSON mode)

### Claude's Discretion
- Exact panel border colors and styles
- Column widths and alignment within each panel
- Whether to show a count summary line (e.g. "12 dependencies detected")
- Handling of empty sections other than AI/LLM (e.g. if no languages detected)

</decisions>

<specifics>
## Specific Ideas

- AI/LLM panel should visually pop — the target user is a solo dev checking if their app has AI exposure. Making it distinct (colored border) makes the finding salient.
- JSON output should be pipeable: `naz scan . --json | jq .technologies` must work cleanly
- `naz scan . --json > report.json` is the primary machine-readable use case

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing code (read before planning)
- `src/naz/cli.py` — Current scan command; Phase 4 replaces the `typer.echo(raw)` stub with normalize() + render(). Console(stderr=True) already wired for errors; stdout is free.
- `src/naz/models.py` — ProjectProfile, Technology, Dependency models; Phase 4 consumes these directly. Note: `raw` field has `exclude=True` — not included in model_dump().
- `src/naz/detection/normalizer.py` — normalize(raw) returns ProjectProfile; this is Phase 4's input.

### Requirements
- `.planning/REQUIREMENTS.md` — OUT-01 (terminal summary), OUT-02 (machine-readable JSON)
- `.planning/PROJECT.md` — Constraints: Typer + Rich non-negotiable; simple and readable code style

### Prior phase context
- `.planning/phases/03-normalization-and-ai-detection/03-CONTEXT.md` — normalizer design decisions, what ProjectProfile fields are populated

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Console(stderr=True)` already in `cli.py` for error panels — stdout (`Console()`) is free for scan output
- `ProjectProfile.model_dump()` / `model_dump_json()` — already available via Pydantic v2, no extra code needed for JSON serialization

### Established Patterns
- Flat functions, no class hierarchy — matches `runner.py` and `normalizer.py` style
- `from __future__ import annotations` at top of every module
- Typer `typer.echo()` for plain stdout; Rich `Console().print()` for formatted output

### Integration Points
- `cli.py` scan command: replace `typer.echo(raw)` with `normalize(raw)` → `render(profile)` or JSON output
- New `--json` flag added to the existing `scan` command via `typer.Option`
- `renderer.py` is a new file; no existing renderer to extend

</code_context>

<deferred>
## Deferred Ideas

- **OUT-03 (v2): AI-agent-optimized format** — self-describing JSON for AI coding agents; explicitly deferred to v2 in REQUIREMENTS.md
- **Verbosity levels / --verbose flag** — not in scope for v0.1; simple summary only

</deferred>

---

*Phase: 04-output-rendering*
*Context gathered: 2026-04-10*
