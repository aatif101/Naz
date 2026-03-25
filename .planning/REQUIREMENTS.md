# Requirements: Naz

**Defined:** 2026-03-25
**Core Value:** A solo dev can run one command and get a clear, actionable security report that an AI agent can immediately act on — no security expertise required.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### CLI

- [ ] **CLI-01**: User can run `naz scan .` or `naz scan /path/to/repo` to scan a repository
- [ ] **CLI-02**: User sees a clear error with install instructions if Node.js is not installed

### Detection

- [ ] **DET-01**: Naz runs Specfy stack-analyser via npx subprocess against the target path
- [ ] **DET-02**: Specfy JSON output is parsed into Naz's internal project profile (Pydantic model)
- [ ] **DET-03**: Project profile includes languages, frameworks, dependencies with versions, infrastructure, and services
- [ ] **DET-04**: AI/LLM dependencies are identified and flagged separately (openai, langchain, anthropic, etc.)
- [ ] **DET-05**: Detected technologies are grouped into categories (runtime deps, dev tools, infrastructure, services, AI/ML)
- [ ] **DET-06**: Detection works correctly on Windows (npx .cmd resolution, install prompt handling)

### Output

- [ ] **OUT-01**: Clean Rich terminal summary showing detected stack, dependency counts, infrastructure, services, and AI/LLM components
- [ ] **OUT-02**: Machine-readable JSON output of the project profile

### Packaging

- [x] **PKG-01**: Project uses src layout with pyproject.toml, installable via `pip install`
- [x] **PKG-02**: `naz` CLI entry point is registered and works after install

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Detection Enhancements

- **DET-07**: Component relationship mapping (preserve Specfy's edges between components)
- **DET-08**: Detection confidence scores (lockfile=high, manifest=medium, file extension=low)
- **DET-09**: Project type classification (web app, API service, CLI tool, ML pipeline)

### Output Enhancements

- **OUT-03**: AI-agent-optimized profile format (self-describing JSON for AI coding agents)

### AI-Specific Detection (Part B)

- **AI-01**: Detect MCP server configurations and flag security concerns
- **AI-02**: Detect agent framework patterns (AutoGPT, CrewAI, LangGraph)
- **AI-03**: Detect prompt injection risk patterns

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Security scanning (Layer 2) | Building detection first, scanning comes after |
| Report generation (Layer 3) | No scanning means no report yet |
| Source code AST parsing | Massively increases complexity; belongs in scanning layer (Semgrep) |
| Auto-install missing tools | Installing system software without consent is hostile, especially for a security tool |
| Real-time file watching | Detection is point-in-time; file watching is IDE plugin territory |
| Remote repository scanning (GitHub URL) | Requires API auth, rate limiting, incomplete file access; user clones locally first |
| Custom detection rules | Premature abstraction; Specfy's 700+ rules cover virtually all cases |
| Build project to detect deps | Executing arbitrary build commands in untrusted repos is a security nightmare |
| PyPI publishing | Not until the tool actually does something useful |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 5 | Pending |
| CLI-02 | Phase 2 | Pending |
| DET-01 | Phase 2 | Pending |
| DET-02 | Phase 3 | Pending |
| DET-03 | Phase 3 | Pending |
| DET-04 | Phase 3 | Pending |
| DET-05 | Phase 3 | Pending |
| DET-06 | Phase 2 | Pending |
| OUT-01 | Phase 4 | Pending |
| OUT-02 | Phase 4 | Pending |
| PKG-01 | Phase 1 | Complete |
| PKG-02 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 12 total
- Mapped to phases: 12
- Unmapped: 0

---
*Requirements defined: 2026-03-25*
*Last updated: 2026-03-25 after roadmap creation*
