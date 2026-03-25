# Project Research Summary

**Project:** Naz - CLI Security Tool for Solo Developers
**Domain:** CLI security tool -- project detection/profiling layer (Python, subprocess-based)
**Researched:** 2026-03-25
**Confidence:** HIGH

## Executive Summary

Naz is a Python CLI tool that profiles a repository's technology stack as the foundation for security scanning, with a particular focus on AI/LLM dependency detection. The expert approach for this type of tool is a pipeline architecture: a thin Typer CLI layer dispatches to an orchestrator, which shells out to Specfy (via npx) for technology detection, normalizes the JSON output into an internal Pydantic model, and renders results through Rich. The stack is well-established (Python 3.12+, Typer, Rich, Pydantic v2, uv) and every component has high community confidence. The core technical challenge is not the Python code itself but the subprocess boundary with Node.js/npx.

The recommended approach is to build inside-out: define the internal `ProjectProfile` Pydantic model first (this is the contract between all components), then build the Specfy subprocess runner with Windows-safe npx resolution, then the normalizer that flattens Specfy's nested tree into the profile, then Rich output, and finally the thin CLI/orchestrator wiring. AI/LLM dependency highlighting -- matching extracted dependencies against a curated package list -- is the core differentiator and should ship in v0.1 since it layers trivially on top of dependency extraction.

The top risks are all at the subprocess boundary: npx behaves differently on Windows (requires `.cmd` resolution), the interactive install prompt hangs the process without `--yes`, and stdout contamination from npm download progress breaks JSON parsing. All three have known, concrete mitigations that must be implemented from day one. The broader architectural risk is Specfy as a single point of failure, mitigated by version pinning and an internal data model that decouples downstream code from Specfy's output format.

## Key Findings

### Recommended Stack

The stack is Python-only with a Node.js subprocess dependency. All core libraries are mature, well-documented, and have high adoption. No exotic or risky technology choices.

**Core technologies:**
- **Python 3.12+**: Runtime -- best error messages, PEP 709 performance, broad support
- **Typer 0.24.1**: CLI framework -- type-hint-based commands, built-in testing via CliRunner
- **Rich 14.3.3**: Terminal output -- tables, panels, syntax highlighting for scan results
- **Pydantic v2.12.5**: Data modeling -- runtime validation of untrusted Specfy JSON, built-in JSON serialization
- **uv**: Package management -- fast, modern, lockfile support, replaces pip/poetry/venv
- **Ruff 0.15.7**: Linting and formatting -- single tool replacing black/flake8/isort
- **pytest 9.0.2**: Testing -- with CliRunner for CLI integration tests and subprocess mocking

**Critical version requirement:** Node.js 18+ must be available on PATH for npx to invoke Specfy.

### Expected Features

**Must have (table stakes for v0.1):**
- Manifest file detection via Specfy (the entire detection engine)
- Language, framework, and dependency extraction with versions
- Infrastructure and service detection (Docker, Terraform, cloud providers)
- AI/LLM dependency highlighting against curated package list (core differentiator)
- Clean Rich terminal output and structured JSON output
- Node.js runtime pre-flight check with actionable error messages

**Should have (v0.2 -- after core detection works):**
- Technology categorization into security-relevant groups (runtime vs dev vs infra vs AI)
- Project type classification (web app, API, CLI tool, ML pipeline)
- Component relationship mapping (Specfy edge data)
- Detection confidence scores (lockfile vs manifest vs file extension)
- AI-agent-optimized profile format (JSON/markdown designed for LLM consumption)

**Defer (v2+):**
- Profile caching, SBOM generation (CycloneDX/SPDX), monorepo intelligence, detection diffs

### Architecture Approach

The architecture follows a four-layer pipeline: CLI (Typer) -> Orchestrator -> Core (SpecfyRunner, Normalizer, Renderer) -> Models (Pydantic). The key architectural decision is that `ProjectProfile` is the central data contract -- detection produces it, output consumes it, and neither side knows about the other. This makes the system modular enough to add new detection engines or output formats without touching existing code.

**Major components:**
1. **CLI Layer (cli.py)** -- Typer command parsing, stays under 50 lines per command
2. **ScanOrchestrator (orchestrator.py)** -- coordinates the pipeline: prereqs, detection, normalization, rendering
3. **SpecfyRunner (detection/specfy.py)** -- subprocess wrapper, handles npx invocation, timeout, error capture
4. **Normalizer (detection/normalizer.py)** -- transforms nested Specfy JSON tree into flat ProjectProfile; the most complex component
5. **Renderer (output/terminal.py)** -- Rich tables and panels consuming ProjectProfile
6. **Models (models.py)** -- Pydantic models: ProjectProfile, Technology, Dependency

### Critical Pitfalls

1. **npx on Windows requires .cmd resolution** -- `subprocess.run(["npx", ...])` fails on Windows because Python finds the extensionless bash script instead of `npx.cmd`. Fix: explicitly resolve `npx.cmd` on Windows via `shutil.which("npx.cmd")`.
2. **npx interactive install prompt hangs subprocess** -- First-time npx invocation prompts for confirmation, blocking the process indefinitely. Fix: always pass `--yes` flag.
3. **Specfy stdout contamination breaks JSON parsing** -- npm download progress and warnings pollute stdout alongside JSON. Fix: use `--output=<tempfile>` to write JSON to a file instead of capturing stdout.
4. **shell=True opens command injection** -- Working around Windows issues with `shell=True` enables command injection via special characters in paths. Fix: use list-based args with `shell=False` and explicit `.cmd` resolution.
5. **Specfy is a single point of failure** -- No fallback if Specfy is unpublished or changes output format. Fix: pin version (`@specfy/stack-analyser@1.27.6`), define internal data model independent of Specfy schema, validate output with Pydantic.

## Implications for Roadmap

Based on research, the v0.1 milestone should be split into 5 phases following the architecture's build order (inside-out) and the dependency graph from FEATURES.md.

### Phase 1: Project Scaffolding and Models

**Rationale:** Models are the central contract with zero dependencies. Every other component depends on them. Project structure, pyproject.toml, and tooling configuration must be correct from the start to avoid Pitfall 9 (entry point misconfiguration) and Pitfall 12 (Python version not declared).
**Delivers:** Working project skeleton with `uv`, src layout, pyproject.toml, Pydantic models (ProjectProfile, Technology, Dependency), and passing model unit tests.
**Features addressed:** Structured JSON output (schema defined), AI dependency data structure.
**Pitfalls avoided:** #9 (entry point), #12 (Python version).

### Phase 2: Specfy Integration (Subprocess Runner)

**Rationale:** The subprocess boundary is where all critical pitfalls live. This phase must be built carefully with Windows compatibility, `--yes` flag, `--output=<tempfile>`, and timeout handling baked in from the start. Isolating the runner makes it testable with mocked subprocess calls.
**Delivers:** SpecfyRunner class that invokes Specfy, handles all platform quirks, returns raw parsed JSON. Pre-flight Node.js/npx check with Rich error panels.
**Features addressed:** Manifest file detection, Node.js runtime check.
**Pitfalls avoided:** #1 (Windows npx), #2 (shell=True injection), #3 (npx install prompt), #4 (stdout contamination), #6 (missing Node.js), #8 (pipe deadlock), #13 (temp file cleanup).

### Phase 3: Normalizer and AI Dependency Detection

**Rationale:** The normalizer is the most complex component -- it must flatten Specfy's nested tree structure into the flat ProjectProfile model. AI dependency highlighting layers directly on top of dependency extraction (match against curated list). These belong together because they transform raw detection data into the internal profile.
**Delivers:** Normalizer that maps Specfy JSON to ProjectProfile, AI/LLM package matching, validated output via Pydantic.
**Features addressed:** Language identification, framework detection, dependency extraction with versions, infrastructure/service detection, AI/LLM dependency highlighting.
**Pitfalls avoided:** #5 (Specfy as SPOF -- internal model decouples), #7 (schema validation), #11 (Specfy misidentifications -- documented, not blocked).

### Phase 4: Rich Terminal Output

**Rationale:** Output rendering depends on a complete ProjectProfile. Build terminal output after the profile is fully populated. Must handle non-terminal contexts (CI/CD, piped output) from the start.
**Delivers:** Rich-formatted scan results: technology table, language breakdown, dependency list with AI highlights, summary panel.
**Features addressed:** Clean terminal output via Rich, structured machine-readable output (JSON).
**Pitfalls avoided:** #10 (Rich output in CI/piped contexts).

### Phase 5: CLI Wiring and End-to-End Integration

**Rationale:** The CLI and orchestrator are the thinnest layers -- they just wire everything together. Build last because they depend on all other components. This phase includes end-to-end testing with real Specfy output.
**Delivers:** Working `naz scan .` command with `--json` flag, complete pipeline from CLI input to formatted output.
**Features addressed:** All v0.1 features integrated and working end-to-end.
**Pitfalls avoided:** All Phase 1 pitfalls verified in integration.

### Phase Ordering Rationale

- Phases follow the architecture's dependency graph (models -> subprocess -> normalizer -> output -> CLI) to avoid rework.
- The subprocess boundary (Phase 2) is isolated early because it contains 6 of the 14 identified pitfalls. Getting this right first de-risks the entire project.
- The normalizer (Phase 3) is separated from the runner because it is the most complex transformation and deserves focused implementation.
- Output (Phase 4) and CLI (Phase 5) are deferred because they are the simplest layers and depend on everything else being stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Specfy Integration):** Needs research on exact Specfy output format for the pinned version, Windows npx.cmd behavior verification, and tempfile strategy. Test with real Specfy runs.
- **Phase 3 (Normalizer):** Needs research on Specfy's nested tree structure with real multi-component repos. The fixture JSON must be captured from actual runs, not hand-written.

Phases with standard patterns (skip deep research):
- **Phase 1 (Scaffolding):** Well-documented uv/hatchling/Pydantic patterns. Follow pyproject.toml template from STACK.md.
- **Phase 4 (Rich Output):** Standard Rich table/panel patterns. Typer + Rich integration is well-documented.
- **Phase 5 (CLI Wiring):** Standard Typer patterns. CliRunner testing is well-documented.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies are mature, well-documented, with specific version recommendations backed by PyPI/npm data |
| Features | HIGH | Feature landscape well-mapped against competitors (Snyk, Trivy, Semgrep). Clear differentiation via AI dependency detection. Specfy capabilities verified against its GitHub repo. |
| Architecture | HIGH | Pipeline pattern is standard for CLI tools wrapping external processes. Safety CLI (Python security tool) follows the same architecture. Build order is derived from clear dependency graph. |
| Pitfalls | HIGH | Critical pitfalls (#1-#4) are backed by specific GitHub issues (CPython, npm/cli, Specfy). Windows subprocess behavior is the highest-risk area and is well-documented. |

**Overall confidence:** HIGH

### Gaps to Address

- **Specfy output schema:** No formal JSON schema published. Must capture real output from a representative project and build Pydantic validation models from actual data, not just README examples.
- **Specfy on Windows:** While npx.cmd resolution is documented, Specfy-specific behavior on Windows (path handling, output encoding) has not been independently verified. Needs hands-on validation in Phase 2.
- **AI package list curation:** The curated list of AI/LLM package names across ecosystems (npm, PyPI, Go, etc.) does not exist yet. Must be researched and assembled during Phase 3 planning.
- **Specfy version pinning:** Recommended pinning to v1.27.6 but actual npx caching behavior with pinned versions needs validation on both Windows and Unix.

## Sources

### Primary (HIGH confidence)
- [Typer Official Documentation](https://typer.tiangolo.com/) -- CLI framework, testing, packaging
- [Pydantic Official Documentation](https://docs.pydantic.dev/latest/) -- data modeling, JSON validation
- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html) -- subprocess patterns
- [Python Packaging User Guide](https://packaging.python.org/en/latest/) -- src layout, pyproject.toml
- [Specfy stack-analyser GitHub](https://github.com/specfy/stack-analyser) -- detection capabilities, output format
- [CPython issue #109590](https://github.com/python/cpython/issues/109590) -- Windows shutil.which behavior
- [npm/cli issues #2226, #3781](https://github.com/npm/cli/issues/2226) -- npx install prompt behavior

### Secondary (MEDIUM confidence)
- [Safety CLI architecture (DeepWiki)](https://deepwiki.com/pyupio/safety) -- pipeline pattern reference
- [Snyk CLI detection docs (DeepWiki)](https://deepwiki.com/snyk/cli/5-package-manager-and-project-detection) -- competitor feature analysis
- [Trivy documentation](https://trivy.dev/docs/latest/) -- competitor feature analysis
- [uv Documentation](https://docs.astral.sh/uv/guides/projects/) -- package management
- [Ruff Documentation](https://docs.astral.sh/ruff/) -- linting/formatting

### Tertiary (LOW confidence)
- Specfy stdout contamination (Pitfall 4) -- inferred from npx behavior patterns, not verified against Specfy specifically
- AI/LLM package list scope -- no existing curated list found; must be assembled from ecosystem knowledge

---
*Research completed: 2026-03-25*
*Ready for roadmap: yes*
