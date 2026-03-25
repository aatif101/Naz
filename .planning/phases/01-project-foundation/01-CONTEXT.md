# Phase 1: Project Foundation - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Pip-installable package skeleton with the central Pydantic data models that all other components depend on. This is the foundation — every subsequent phase builds on the project structure and models defined here.

</domain>

<decisions>
## Implementation Decisions

### Project Structure
- **D-01:** Use src layout (`src/naz/`) as specified in the context doc
- **D-02:** Use pyproject.toml with hatchling build backend (per research recommendation)
- **D-03:** Python 3.12+ minimum (per research — better error messages, performance)
- **D-04:** Use uv for package management (per research — standard 2025 tooling)

### Data Models
- **D-05:** Use Pydantic v2 for all data models (per research — runtime validation of untrusted Specfy JSON)
- **D-06:** ProjectProfile is the central model — detection produces it, output consumes it
- **D-07:** Model should include: languages, frameworks, dependencies (with versions), infrastructure, services, AI/LLM components, and technology categories

### CLI Skeleton
- **D-08:** Typer for CLI framework, Rich for terminal output (non-negotiable per context doc)
- **D-09:** Initial CLI has `naz scan <path>` command — everything else comes later
- **D-10:** Entry point registered in pyproject.toml as `naz`

### Code Quality
- **D-11:** Ruff for linting and formatting (per research — replaces black + flake8 + isort)

### Claude's Discretion
- Exact Pydantic model field names and nesting structure
- pyproject.toml metadata details (author, license, classifiers)
- Ruff configuration specifics
- Test infrastructure setup

</decisions>

<canonical_refs>
## Canonical References

No external specs — requirements fully captured in decisions above and in:
- `.planning/PROJECT.md` — Project vision, constraints, key decisions
- `.planning/REQUIREMENTS.md` — PKG-01, PKG-02 requirements
- `.planning/research/STACK.md` — Recommended stack with versions and rationale
- `.planning/research/ARCHITECTURE.md` — Component boundaries and build order
- `naz-gsd-context.md` — Original context doc with project structure specification

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code

### Established Patterns
- None — this phase establishes the patterns

### Integration Points
- None — this is the foundation

</code_context>

<specifics>
## Specific Ideas

- Project structure should match the layout specified in naz-gsd-context.md (src/naz/ with detection/, utils/ subdirectories)
- Code must be simple and readable — no over-abstraction (per user preference)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-project-foundation*
*Context gathered: 2026-03-25*
