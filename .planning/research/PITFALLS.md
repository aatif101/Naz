# Domain Pitfalls

**Domain:** CLI security tool (Python) shelling out to Node.js tooling
**Project:** Naz
**Researched:** 2026-03-25

## Critical Pitfalls

Mistakes that cause rewrites, broken user experiences, or security vulnerabilities.

---

### Pitfall 1: npx on Windows Requires shell=True or Explicit .cmd Resolution

**What goes wrong:** On Windows, `npx` is installed as two files: an extensionless bash script (`npx`) and a Windows batch file (`npx.cmd`). When you call `subprocess.run(["npx", ...], shell=False)` on Windows, Python finds the extensionless bash script via `shutil.which("npx")` (especially on Python 3.12+) and fails to execute it because it is not a native Windows executable. The process either errors out with `OSError` / `FileNotFoundError` or silently does nothing.

**Why it happens:** Python 3.12 changed `shutil.which()` behavior on Windows -- it now returns extensionless files that match, whereas Python 3.11 and earlier returned the `.cmd` variant. Developers testing on macOS/Linux never encounter this because `npx` works directly on Unix systems.

**Consequences:** Tool completely fails on Windows, which is the primary target platform (the developer uses Windows 11). Users get cryptic OS-level errors instead of helpful messages.

**Prevention:**
```python
import shutil
import subprocess
import sys

def get_npx_command():
    """Resolve npx executable, handling Windows .cmd files."""
    if sys.platform == "win32":
        # Explicitly look for npx.cmd on Windows
        npx_path = shutil.which("npx.cmd") or shutil.which("npx")
    else:
        npx_path = shutil.which("npx")

    if npx_path is None:
        raise FileNotFoundError("npx not found. Install Node.js: https://nodejs.org")

    return npx_path
```

Alternatively, use `shell=True` on Windows only -- but this introduces Pitfall 2 below.

**Detection:** Test on Windows early. If `subprocess.run(["npx", "--version"])` fails on Windows but works on macOS/Linux, this is the cause.

**Confidence:** HIGH -- verified via CPython issue #109590 and Python subprocess documentation.

**Phase:** Must be addressed in Phase 1 (Specfy integration). This is day-one code.

---

### Pitfall 2: shell=True Opens Command Injection Vulnerabilities

**What goes wrong:** Developers work around the Windows npx problem (Pitfall 1) by setting `shell=True` globally. This passes all arguments through `cmd.exe` on Windows, which interprets special characters (`&`, `|`, `%`, `>`, `<`) in file paths and arguments. A repository path containing `&` (e.g., `C:\Users\dev\projects\my&app`) causes command injection -- `cmd.exe` treats `&` as a command separator and executes whatever follows.

**Why it happens:** `shell=True` is the "easy fix" that works in development. Paths with special characters are uncommon in testing but exist in production.

**Consequences:** At minimum, the scan silently fails or scans the wrong directory. At worst, arbitrary command execution -- particularly bad for a security tool.

**Prevention:**
- Use the `.cmd` resolution approach from Pitfall 1 with `shell=False`.
- If `shell=True` is absolutely necessary, sanitize all arguments and never interpolate user-provided paths into shell command strings.
- Pass arguments as a list, never as a string: `subprocess.run([npx_path, "@specfy/stack-analyser", target_path])`.
- Note: On Windows, `.cmd` files are always launched through `cmd.exe` by the OS regardless of `shell=False`. This means arguments are still parsed by shell rules. Mitigate by validating the target path before passing it.

**Detection:** Security linters (bandit rule B602) flag `shell=True`. Run `bandit` on the codebase.

**Confidence:** HIGH -- documented in Python subprocess docs, MCP Python SDK issue #1257, and bandit security rules.

**Phase:** Phase 1. Bake the correct subprocess pattern into the first implementation.

---

### Pitfall 3: npx Interactive Install Prompt Blocks the Subprocess

**What goes wrong:** When `npx @specfy/stack-analyser` runs for the first time (or after cache clear), npx prompts: "Need to install the following packages: @specfy/stack-analyser. Ok to proceed? (y)". This prompt waits for stdin input. Since `subprocess.run()` does not provide interactive stdin by default, the process hangs indefinitely. The CLI appears frozen with no output.

**Why it happens:** npx changed behavior in npm 7+ to prompt before installing packages. Developers who already have the package cached never see this prompt during development.

**Consequences:** First-time users experience a completely frozen CLI. They think the tool is broken, uninstall, and never come back. This is the #1 first-run killer for tools that depend on npx.

**Prevention:**
```python
# Always pass --yes to suppress the install prompt
subprocess.run([npx_path, "--yes", "@specfy/stack-analyser", target_path, ...])
```

Also set a timeout to catch hangs from this or other causes:
```python
try:
    result = subprocess.run(
        [npx_path, "--yes", "@specfy/stack-analyser", target_path],
        capture_output=True, text=True, timeout=120
    )
except subprocess.TimeoutExpired:
    # Handle timeout with helpful message
    pass
```

**Detection:** Test with a clean npm cache (`rm -rf ~/.npm/_npx` or equivalent). If the process hangs, this is the cause.

**Confidence:** HIGH -- documented in npm/cli issue #2226 and npm/cli issue #3781.

**Phase:** Phase 1. The `--yes` flag must be present from the first subprocess call.

---

### Pitfall 4: Specfy stdout Contamination Breaks JSON Parsing

**What goes wrong:** Specfy's stack-analyser may output warnings, npm download progress messages, or npx installation logs to stdout alongside the JSON result. When you capture stdout and call `json.loads(result.stdout)`, parsing fails because the output is not pure JSON -- it has npm progress bars, deprecation warnings, or other text prepended/appended.

**Why it happens:** npx writes download progress to stdout (not always stderr). Node.js itself may emit warnings (e.g., deprecation notices, experimental feature warnings) to stdout. The `--output=<filename>` flag exists but adds file I/O complexity.

**Consequences:** `json.JSONDecodeError` on first run (when npx downloads the package) but works fine afterward (when cached). Extremely confusing intermittent failure.

**Prevention:**
- **Strategy A (recommended):** Use `--output=<tempfile>` to write JSON to a file, then read the file. This completely isolates JSON output from npm/npx noise.
```python
import tempfile
import json

with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
    tmp_path = tmp.name

result = subprocess.run(
    [npx_path, "--yes", "@specfy/stack-analyser", target_path, f"--output={tmp_path}"],
    capture_output=True, text=True, timeout=120
)

with open(tmp_path, "r") as f:
    data = json.load(f)
```

- **Strategy B (fallback):** If capturing stdout, strip non-JSON content by finding the first `{` or `[` character and the last `}` or `]`.

**Detection:** Run with a clean npx cache and check if `result.stdout` starts with `{` or `[`. If it starts with anything else (download progress, warnings), this pitfall is active.

**Confidence:** MEDIUM -- inferred from npx behavior patterns and npm/cli issues. Not verified against Specfy specifically, but the pattern is well-documented for npx-invoked tools.

**Phase:** Phase 1. The JSON parsing strategy must be decided upfront.

---

### Pitfall 5: Specfy Dependency Creates Single Point of Failure with No Fallback

**What goes wrong:** The entire detection layer depends on a single third-party npm package (`@specfy/stack-analyser`). If the package is unpublished from npm, has a breaking change in output format, or the Specfy project is abandoned, Naz stops working entirely. The PROJECT.md explicitly states "Specfy is the only general detection engine" and secondary engines are out of scope.

**Why it happens:** Pragmatic decision to leverage existing 700+ tech detection rather than reimplementing. Correct for v0.1, but risky without mitigation.

**Consequences:** Complete tool failure if Specfy has issues. No graceful degradation.

**Prevention:**
- Pin to a specific version: `npx --yes @specfy/stack-analyser@1.27.6` instead of `@specfy/stack-analyser` (which resolves to latest).
- Define an internal data model that is independent of Specfy's output format. Parse Specfy output into your own `ProjectProfile` type. If Specfy changes or dies, you only need to replace the parser, not the entire downstream pipeline.
- Cache the last known working Specfy output format as a test fixture. If parsing fails, you know the output format changed.
- Monitor the GitHub repo for activity. The project is currently active (v1.27.6, January 2026), but Specfy the company has pivoted before.

**Detection:** CI test that runs Specfy against a known repo and validates the output schema.

**Confidence:** HIGH -- architectural risk, well understood.

**Phase:** Phase 1 (version pinning + internal data model). Fallback engines can be deferred to later milestones.

---

## Moderate Pitfalls

---

### Pitfall 6: Node.js Not Installed -- Cryptic Error Instead of Helpful Message

**What goes wrong:** User runs `naz scan .` without Node.js installed. `shutil.which("npx")` returns `None`, or the subprocess call fails with a system-level error. The user sees a Python traceback or OS error instead of a clear message explaining what is needed.

**Prevention:**
- Check for Node.js/npx availability before attempting to run Specfy.
- Use `shutil.which()` to detect npx, and if missing, print a Rich-formatted error panel explaining: (1) Node.js is required, (2) where to install it, (3) that this is a one-time setup.
- Check Node.js version too -- Specfy may require a minimum version.

```python
def check_node_available():
    npx = get_npx_command()  # From Pitfall 1 resolution
    # Also verify node version
    result = subprocess.run([shutil.which("node"), "--version"],
                          capture_output=True, text=True)
    # Parse version, check minimum
```

**Detection:** Test in a clean environment without Node.js.

**Confidence:** HIGH -- standard dependency-check pattern.

**Phase:** Phase 1. Pre-flight check before any Specfy invocation.

---

### Pitfall 7: Specfy Output Schema Is Not Validated, Causing Silent Data Loss

**What goes wrong:** Specfy's JSON output changes between versions (new fields, renamed fields, restructured nesting). The Python code accesses fields by key name (`data["techs"]`, `data["dependencies"]`) without validation. Missing or renamed fields cause `KeyError` crashes or, worse, silently return empty results that look like "no technologies detected."

**Why it happens:** No formal JSON schema is published for Specfy's output. The output structure is only documented by example in the README. Developers code against the current output and never test against format changes.

**Prevention:**
- Define a Pydantic model (or dataclass) for the expected Specfy output shape.
- Parse Specfy output through validation before using it. Catch validation errors and provide clear messages: "Specfy output format may have changed. Expected field X not found."
- Use `.get()` with defaults instead of direct key access for resilience.

**Detection:** Unit tests with fixture JSON that cover all expected fields. If Specfy updates break fixtures, tests fail before users see the bug.

**Confidence:** MEDIUM -- inferred from Specfy's lack of published schema and active development pace (frequent releases may change output).

**Phase:** Phase 1. Define the internal model from day one.

---

### Pitfall 8: subprocess Deadlock on Large Repository Output

**What goes wrong:** For monorepos or large projects, Specfy may produce substantial JSON output. If using `subprocess.Popen` with `stdout=PIPE` and reading stdout after the process completes (instead of concurrently), the OS pipe buffer fills (typically 64KB on Linux, 4KB on some Windows configurations). The subprocess blocks waiting to write, the parent blocks waiting for the subprocess to exit -- deadlock.

**Prevention:**
- Use `subprocess.run()` with `capture_output=True` (which internally uses `communicate()` to read both streams concurrently).
- Or use the `--output=<file>` flag to write to a temp file (recommended for large repos anyway -- see Pitfall 4).
- Set a timeout to break any deadlock: `timeout=120`.

**Detection:** Test against a large monorepo (100+ packages). If the CLI hangs, this is likely the cause.

**Confidence:** HIGH -- well-documented Python subprocess behavior.

**Phase:** Phase 1. Use `subprocess.run()` with `capture_output=True` or file output from the start.

---

### Pitfall 9: Typer Entry Point Misconfiguration in pyproject.toml

**What goes wrong:** The CLI installs via `pip install` but the `naz` command does not work. Common causes:
1. Module name uses hyphens (Python modules must use underscores).
2. Entry point references the wrong object (`naz.main:app` vs `naz.cli:app`).
3. The package is installed in editable mode (`pip install -e .`) but the module structure changes and the old entry point is cached.

**Prevention:**
```toml
# pyproject.toml
[project.scripts]
naz = "naz.cli:app"  # Points to the Typer app object
```

- Keep the entry point stable from the first commit. Changing it later confuses installed users.
- Test installation in a clean virtualenv: `pip install .` then `naz --help`.
- Use underscores in package directory names, hyphens only in the distribution name if desired.

**Detection:** `pip install .` in a fresh venv, then `which naz` and `naz --help`.

**Confidence:** HIGH -- standard Python packaging knowledge.

**Phase:** Phase 1 (project scaffolding).

---

### Pitfall 10: Rich Output Breaks in CI/CD and Piped Contexts

**What goes wrong:** Rich's fancy terminal output (colors, panels, tables, spinners) produces garbled output or ANSI escape codes when piped to a file, used in CI environments, or run in terminals that do not support ANSI. Security tools are frequently run in CI pipelines, so this is not an edge case.

**Prevention:**
- Use `rich.console.Console(force_terminal=...)` or check `Console.is_terminal` to detect non-interactive contexts.
- Provide a `--no-color` or `--plain` flag (Rich respects the `NO_COLOR` environment variable standard).
- Ensure the JSON output mode (`--json` flag) produces clean JSON without Rich formatting.
- Typer integrates with Rich by default; be aware that error output also gets Rich formatting. Set `TYPER_USE_RICH=0` environment variable or handle explicitly.

**Detection:** Run `naz scan . | cat` and `naz scan . > output.txt`. If either contains ANSI escape codes or garbled output, this pitfall is active.

**Confidence:** HIGH -- well-known Rich/terminal behavior.

**Phase:** Phase 1 for basic detection; dedicated CI output mode can be a later phase.

---

## Minor Pitfalls

---

### Pitfall 11: Specfy Misidentifies File Types

**What goes wrong:** Specfy has known bugs where it misidentifies file extensions. For example, `.rs` (Rust) files are reported as RenderScript (GitHub issue #95), and `.mo` (gettext translation) files are reported as Modelica (issue #90). This means the detected tech stack may contain false positives.

**Prevention:**
- Do not blindly trust Specfy output. Consider a post-processing step that applies sanity checks (e.g., if Rust files exist but "RenderScript" is detected, flag it).
- For v0.1, document known Specfy misidentifications and accept them. Fix in a later phase with a correction layer.

**Detection:** Scan a known Rust project and check if RenderScript appears in the output.

**Confidence:** HIGH -- confirmed via Specfy GitHub issues #95 and #90.

**Phase:** Not critical for v0.1. Add a correction/filtering layer in a later milestone.

---

### Pitfall 12: Python Version Compatibility Not Declared

**What goes wrong:** Tool is developed on Python 3.12+ but does not declare `requires-python` in pyproject.toml. Users on Python 3.9 or 3.10 install it successfully but hit syntax errors or missing stdlib features at runtime.

**Prevention:**
```toml
[project]
requires-python = ">=3.10"
```

Pick a minimum version and stick to it. Python 3.10 is a good minimum (match/case syntax, modern typing). Test on the minimum version in CI.

**Detection:** Set up a CI matrix with the minimum declared Python version.

**Confidence:** HIGH -- standard packaging practice.

**Phase:** Phase 1 (project scaffolding).

---

### Pitfall 13: Temp File Cleanup Failures on Windows

**What goes wrong:** When using `--output=<tempfile>` for Specfy output (as recommended in Pitfall 4), Windows file locking prevents deletion of temp files if the JSON file is still open or if the process did not close cleanly. Accumulation of temp files in the temp directory.

**Prevention:**
- Use `tempfile.NamedTemporaryFile(delete=False)` and explicitly clean up in a `finally` block.
- On Windows, ensure the file handle is closed before attempting to read it with a separate `open()`.
- Use `atexit` or try/finally to guarantee cleanup.

**Detection:** Run the scan multiple times on Windows and check `%TEMP%` for leftover files.

**Confidence:** MEDIUM -- standard Windows file-locking behavior.

**Phase:** Phase 1. Handle correctly from the start.

---

### Pitfall 14: npx Cache Staleness After Version Pin Update

**What goes wrong:** You pin `@specfy/stack-analyser@1.27.6` in your subprocess call. Later you update the pin to `@1.28.0`. Users who ran the old version still have `1.27.6` in their npx cache. npx may use the cached version instead of downloading the new one, depending on npm version and caching behavior.

**Prevention:**
- Include the version in the npx call: `npx --yes @specfy/stack-analyser@1.27.6`.
- When updating the pin, test that npx actually downloads the new version.
- Consider documenting `npx clear-npx-cache` or equivalent if users report stale behavior.

**Detection:** Update the version pin and test on a machine that previously ran the old version.

**Confidence:** MEDIUM -- npx caching behavior varies across npm versions.

**Phase:** Relevant when updating Specfy versions in later milestones.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Specfy integration (Phase 1) | npx hangs on first run (Pitfall 3) | Always pass `--yes` flag |
| Specfy integration (Phase 1) | Windows subprocess failure (Pitfall 1) | Resolve `npx.cmd` explicitly |
| Specfy integration (Phase 1) | JSON parsing fails intermittently (Pitfall 4) | Use `--output=<file>` instead of stdout |
| Specfy integration (Phase 1) | No Node.js installed (Pitfall 6) | Pre-flight dependency check with helpful error |
| Project scaffolding (Phase 1) | Entry point broken after install (Pitfall 9) | Test `pip install .` in clean venv early |
| Output formatting (Phase 1-2) | Rich output garbled in CI (Pitfall 10) | Detect non-terminal context, provide `--plain` flag |
| Security scanning (Phase 2+) | Specfy output format changes (Pitfall 7) | Internal data model + Pydantic validation |
| Version updates (ongoing) | Specfy breaking changes (Pitfall 5) | Pin version, define internal schema |

## Sources

- [Python CPython issue #109590: shutil.which on Windows](https://github.com/python/cpython/issues/109590)
- [CPython issue #137254: Windows subprocess PATH issues](https://github.com/python/cpython/issues/137254)
- [MCP Python SDK issue #1257: shell=True injection risk on Windows](https://github.com/modelcontextprotocol/python-sdk/issues/1257)
- [npm/cli issue #2226: npx --yes breaking change](https://github.com/npm/cli/issues/2226)
- [npm/cli issue #3781: npx install prompt hangs piped commands](https://github.com/npm/cli/issues/3781)
- [npm/cli issue #7295: npx slow with cached packages](https://github.com/npm/cli/issues/7295)
- [Specfy stack-analyser GitHub](https://github.com/specfy/stack-analyser)
- [Specfy issue #95: Rust misidentified as RenderScript](https://github.com/specfy/stack-analyser/issues/95)
- [Specfy issue #90: gettext misidentified as Modelica](https://github.com/specfy/stack-analyser/issues/90)
- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)
- [Bandit B602: subprocess with shell=True](https://docs.openstack.org/bandit/1.4.0/plugins/subprocess_popen_with_shell_equals_true.html)
- [Typer packaging guide](https://typer.tiangolo.com/tutorial/package/)
- [Python Packaging Guide: pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Typer exceptions documentation](https://typer.tiangolo.com/tutorial/exceptions/)
