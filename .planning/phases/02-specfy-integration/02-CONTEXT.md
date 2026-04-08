# Phase 2: Specfy Integration - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Subprocess runner that invokes `npx @specfy/stack-analyser` safely on all platforms (Windows npx.cmd resolution), handles all failure modes (missing Node.js, timeout, bad output), and returns raw JSON detection data. This phase does NOT parse or normalize the output -- that's Phase 3.

</domain>

<decisions>
## Implementation Decisions

### Error Messaging
- **D-01:** Use Rich-formatted error panels for all user-facing errors (consistent with Rich-based output)
- **D-02:** Actionable minimum verbosity -- what went wrong + one clear next step. No stack traces or debug info unless --verbose flag added later.
- **D-03:** Node.js missing error must include install URL (https://nodejs.org) and the command to retry

### Timeout & Failure
- **D-04:** Use 120-second timeout for Specfy subprocess (per stack doc)
- **D-05:** On timeout, abort immediately with Rich error panel suggesting smaller directory. No retry.
- **D-06:** Non-zero exit code or unparseable JSON is a hard failure -- show stderr content in Rich error panel. No partial results.

### Runner Return Contract
- **D-07:** Runner function returns raw dict on success (parsed JSON from Specfy stdout)
- **D-08:** Raise typed exceptions on failure: `NodeNotFoundError`, `SpecfyTimeoutError`, `SpecfyError`
- **D-09:** CLI layer catches exceptions and renders Rich error panels. Detection layer never imports Rich.
- **D-10:** Runner lives in `src/naz/detection/` module

### First-Run Experience
- **D-11:** Print a brief message before npx call on first run: "Downloading stack analyser (first run only)..."
- **D-12:** Use `npx --yes` flag to auto-accept the install prompt (no interactive blocking)
- **D-13:** No spinner or progress bar -- just the text message. Keep it simple.

### Platform Handling (from requirements)
- **D-14:** On Windows, resolve `npx.cmd` instead of `npx` (use `shutil.which("npx")` which handles this)
- **D-15:** Never use `shell=True` in subprocess calls
- **D-16:** Use `subprocess.run()` with `capture_output=True, text=True`

### Claude's Discretion
- Exact exception class hierarchy and base class design
- Internal module structure within `src/naz/detection/`
- How to detect first-run vs subsequent runs (checking npx cache, or always showing the message)
- Test fixture structure for mocked Specfy output

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Stack & Architecture
- `CLAUDE.md` -- Subprocess management section specifies exact subprocess.run() call pattern, --yes flag, timeout, shutil.which() usage
- `.planning/PROJECT.md` -- Constraints: Specfy via npx subprocess, Node.js runtime dependency
- `.planning/REQUIREMENTS.md` -- DET-01 (run Specfy), DET-06 (Windows npx.cmd), CLI-02 (Node.js missing error)

### Prior Phase Context
- `.planning/phases/01-project-foundation/01-CONTEXT.md` -- Foundation decisions (src layout, Pydantic v2, Typer/Rich)

No external specs beyond the above -- Specfy's CLI interface is documented in its npm package.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/naz/models.py` -- ProjectProfile, Technology, Dependency models (Phase 3 will use these to parse runner output)
- `src/naz/cli.py` -- Stub `scan` command ready to call the runner
- `src/naz/detection/__init__.py` -- Empty, ready for runner module

### Established Patterns
- Pydantic v2 for all data models
- Typer for CLI, Rich for terminal output
- src layout with `src/naz/` package structure

### Integration Points
- `cli.py:scan()` will import and call the runner function
- Runner returns raw dict; Phase 3 will add the dict-to-ProjectProfile conversion
- Exception classes need to be importable by both detection and CLI layers

</code_context>

<specifics>
## Specific Ideas

- Error panels should follow the Rich Panel style shown in the discussion previews
- The "Downloading stack analyser (first run only)..." message should print before the subprocess call, not during
- Keep the runner function signature simple: `run_specfy(path: str | Path) -> dict`

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope

</deferred>

---

*Phase: 02-specfy-integration*
*Context gathered: 2026-04-08*
