# Roadmap: Naz

## Overview

Naz v0.1 delivers one thing: run `naz scan .` and get a complete technology profile of a repository. The build follows an inside-out strategy -- data models first, then the Specfy subprocess boundary (where all the hard problems live), then normalization and AI detection, then output rendering, and finally CLI wiring. Each phase produces a testable, verifiable component. By the end, a solo dev can pip-install naz, point it at a repo, and see exactly what technologies are in use.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Project Foundation** - Installable package skeleton with Pydantic data models
- [ ] **Phase 2: Specfy Integration** - Subprocess runner that invokes Specfy safely on all platforms
- [ ] **Phase 3: Normalization and AI Detection** - Transform raw Specfy output into a structured, categorized project profile
- [ ] **Phase 4: Output Rendering** - Rich terminal summary and machine-readable JSON output
- [ ] **Phase 5: CLI Wiring and End-to-End** - Working `naz scan .` command tying all components together

## Phase Details

### Phase 1: Project Foundation
**Goal**: A pip-installable package skeleton exists with the central data models that all other components depend on
**Depends on**: Nothing (first phase)
**Requirements**: PKG-01, PKG-02
**Success Criteria** (what must be TRUE):
  1. Running `pip install -e .` in the repo succeeds without errors
  2. Running `naz` in a terminal prints a help message (entry point works)
  3. A ProjectProfile Pydantic model can be instantiated and serialized to JSON
**Plans:** 2 plans
Plans:
- [x] 01-01-PLAN.md — Package skeleton with pyproject.toml, src layout, Typer CLI entry point
- [x] 01-02-PLAN.md — Pydantic data models (ProjectProfile) and full test suite

### Phase 2: Specfy Integration
**Goal**: Naz can invoke Specfy via npx and get raw detection results back, handling all platform quirks and failure modes
**Depends on**: Phase 1
**Requirements**: DET-01, DET-06, CLI-02
**Success Criteria** (what must be TRUE):
  1. Running the Specfy runner against a real repository returns parsed JSON detection data
  2. Running the Specfy runner on Windows resolves npx.cmd correctly and produces the same results as Unix
  3. Running the Specfy runner without Node.js installed produces a clear error message with install instructions
  4. The subprocess never hangs (npx --yes flag, timeout enforced)
**Plans**: TBD

### Phase 3: Normalization and AI Detection
**Goal**: Raw Specfy output is transformed into a complete, categorized ProjectProfile with AI/LLM dependencies specifically identified
**Depends on**: Phase 2
**Requirements**: DET-02, DET-03, DET-04, DET-05
**Success Criteria** (what must be TRUE):
  1. Given Specfy JSON output, a ProjectProfile is produced containing languages, frameworks, dependencies with versions, infrastructure, and services
  2. AI/LLM packages (openai, langchain, anthropic, etc.) are flagged as AI dependencies in the profile
  3. Detected technologies are grouped into categories: runtime deps, dev tools, infrastructure, services, AI/ML
  4. The ProjectProfile validates successfully via Pydantic (no malformed data passes through)
**Plans**: TBD

### Phase 4: Output Rendering
**Goal**: Users see a clear, formatted terminal summary of their project's technology stack, and can get machine-readable JSON
**Depends on**: Phase 3
**Requirements**: OUT-01, OUT-02
**Success Criteria** (what must be TRUE):
  1. A Rich-formatted terminal summary displays the detected stack, dependency counts, infrastructure, services, and AI/LLM components
  2. A JSON output of the complete ProjectProfile can be produced for machine consumption
  3. Output renders correctly when piped or in non-terminal contexts (no Rich markup in plain text)
**Plans**: TBD

### Phase 5: CLI Wiring and End-to-End
**Goal**: A user can run `naz scan .` and get a complete scan result -- the full pipeline works end-to-end
**Depends on**: Phase 4
**Requirements**: CLI-01
**Success Criteria** (what must be TRUE):
  1. Running `naz scan .` in a repository with a known tech stack produces a correct, complete terminal summary
  2. Running `naz scan /path/to/repo` works with an absolute path argument
  3. Running `naz scan .` with `--json` flag outputs valid JSON to stdout
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Project Foundation | 0/2 | Planning complete | - |
| 2. Specfy Integration | 0/0 | Not started | - |
| 3. Normalization and AI Detection | 0/0 | Not started | - |
| 4. Output Rendering | 0/0 | Not started | - |
| 5. CLI Wiring and End-to-End | 0/0 | Not started | - |
