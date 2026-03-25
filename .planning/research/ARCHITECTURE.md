# Architecture Research

**Domain:** CLI security detection tool (Python, subprocess-based)
**Researched:** 2026-03-25
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      CLI Layer (Typer)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ scan cmd │  │ (future) │  │ (future) │                   │
│  └────┬─────┘  └──────────┘  └──────────┘                   │
├───────┴──────────────────────────────────────────────────────┤
│                    Orchestration Layer                        │
│  ┌──────────────────────────────────────────────────────┐    │
│  │              ScanOrchestrator                         │    │
│  │  (validates prereqs, runs detection, formats output)  │    │
│  └───────────┬──────────────────────┬───────────────────┘    │
├──────────────┴──────────────────────┴────────────────────────┤
│                      Core Layer                              │
│  ┌─────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ SpecfyRunner    │  │ Normalizer   │  │ Renderer       │  │
│  │ (subprocess)    │  │ (JSON→model) │  │ (Rich output)  │  │
│  └────────┬────────┘  └──────┬───────┘  └───────┬────────┘  │
├───────────┴─────────────────┴───────────────────┴────────────┤
│                      Models Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ ProjectProfile│  │ Technology   │  │ Dependency        │  │
│  │ (dataclass)   │  │ (dataclass)  │  │ (dataclass)       │  │
│  └──────────────┘  └──────────────┘  └───────────────────┘  │
└──────────────────────────────────────────────────────────────┘
         │
         │ subprocess.run
         ▼
┌──────────────────────┐
│  npx @specfy/        │
│  stack-analyser      │
│  (external process)  │
└──────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI Layer (Typer) | Parse commands, flags, arguments; dispatch to orchestrator | `typer.Typer()` app with `@app.command()` decorators |
| ScanOrchestrator | Coordinate the scan pipeline: check prereqs, run detection, normalize, render | Plain class that calls components in sequence |
| SpecfyRunner | Execute `npx @specfy/stack-analyser` as subprocess, capture stdout/stderr, handle errors | `subprocess.run()` with JSON capture |
| Normalizer | Transform raw Specfy JSON into internal `ProjectProfile` model | Pure function: `dict -> ProjectProfile` |
| Renderer | Display `ProjectProfile` to terminal using Rich | Rich Tables, Panels, Trees |
| Models | Data structures representing detected stack | Python `dataclass` or Pydantic `BaseModel` |

## Recommended Project Structure

```
naz/
├── src/
│   └── naz/
│       ├── __init__.py          # Package init, version
│       ├── cli.py               # Typer app, command definitions
│       ├── orchestrator.py      # ScanOrchestrator pipeline
│       ├── models.py            # ProjectProfile, Technology, Dependency dataclasses
│       ├── detection/
│       │   ├── __init__.py
│       │   ├── specfy.py        # SpecfyRunner: subprocess wrapper
│       │   └── normalizer.py    # Raw Specfy JSON → ProjectProfile
│       ├── output/
│       │   ├── __init__.py
│       │   ├── terminal.py      # Rich renderer for human-readable output
│       │   ├── json_report.py   # JSON output for AI agents (future)
│       │   └── markdown.py      # Markdown output for AI agents (future)
│       └── prereqs.py           # Node.js/npx availability checks
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_specfy.py           # Test with fixture JSON, no real subprocess
│   ├── test_normalizer.py
│   ├── test_models.py
│   └── fixtures/
│       └── specfy_output.json   # Real Specfy output captured for testing
├── pyproject.toml
└── .planning/
```

### Structure Rationale

- **`detection/`:** Isolates external tool integration. When future detection engines are added (AI-specific detector, fallback engines), they slot in here without touching other code. Each detector has its own runner + normalizer pair.
- **`output/`:** Separates rendering from logic. Dual output (terminal + JSON + markdown) is a core requirement. Each output format is its own module. The renderer receives a `ProjectProfile` and knows nothing about how it was created.
- **`models.py` at package root:** Models are shared across detection and output. Keeping them at the top level avoids circular imports and makes them the central contract between components.
- **`orchestrator.py` at package root:** The orchestrator is the only component that knows about all other components. It is the "glue" and lives at the top level to reflect this.
- **`prereqs.py` at package root:** Simple utility, called early in the pipeline. Does not deserve a subdirectory.

## Architectural Patterns

### Pattern 1: Pipeline Orchestration

**What:** The scan command follows a linear pipeline: validate prerequisites, run detection, normalize output, render results. Each step is a distinct function/method call.
**When to use:** Always -- this is the core execution flow.
**Trade-offs:** Simple and debuggable. Not parallel, but detection is a single subprocess call so parallelism adds nothing in v0.1.

**Example:**
```python
class ScanOrchestrator:
    def run(self, path: Path) -> ProjectProfile:
        self._check_prerequisites()          # Step 1: Node.js available?
        raw_output = self._run_detection(path) # Step 2: Call Specfy
        profile = self._normalize(raw_output)  # Step 3: JSON -> model
        self._render(profile)                  # Step 4: Rich output
        return profile
```

### Pattern 2: Subprocess Wrapper as Isolated Class

**What:** Wrap `subprocess.run()` in a dedicated class (`SpecfyRunner`) that handles invocation, timeout, error capture, and raw output return. The class knows nothing about what the output means -- it just runs the command and returns stdout.
**When to use:** Any time you call an external tool. Isolating the subprocess boundary makes testing trivial (mock the runner, feed fixture JSON).
**Trade-offs:** Slight indirection, but massive testability win. The real subprocess is only called in integration tests.

**Example:**
```python
@dataclass
class SpecfyResult:
    raw_json: dict
    exit_code: int
    stderr: str

class SpecfyRunner:
    def run(self, path: Path, timeout: int = 120) -> SpecfyResult:
        result = subprocess.run(
            ["npx", "@specfy/stack-analyser", str(path)],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            raise DetectionError(result.stderr)
        return SpecfyResult(
            raw_json=json.loads(result.stdout),
            exit_code=result.returncode,
            stderr=result.stderr,
        )
```

### Pattern 3: Internal Model as Contract

**What:** Define `ProjectProfile` as the single data contract between detection and output. Detection produces it; output consumes it. Neither side knows about the other.
**When to use:** Always. This is the architectural boundary that keeps the system modular.
**Trade-offs:** You must design the model upfront. Changes to it ripple to both sides. Worth it for decoupling.

**Example:**
```python
@dataclass
class Dependency:
    manager: str       # "npm", "pip", "docker", etc.
    name: str
    version: str | None

@dataclass
class Technology:
    name: str
    category: str      # "language", "framework", "service", "infra", etc.

@dataclass
class ProjectProfile:
    path: Path
    technologies: list[Technology]
    languages: dict[str, int]       # language -> file count
    dependencies: list[Dependency]
    ai_dependencies: list[Dependency]  # Subset flagged as AI/LLM related
    components: list[str]            # Named subcomponents detected
    raw: dict                        # Original Specfy output for debugging
```

## Data Flow

### Primary Scan Flow

```
User runs: naz scan .
    |
    v
[cli.py] parse args via Typer
    |
    v
[orchestrator.py] ScanOrchestrator.run(path=".")
    |
    +---> [prereqs.py] check_node_available()
    |         |
    |         +---> subprocess.run(["node", "--version"])
    |         |     Returns: True/False
    |         +---> If False: Rich error panel, sys.exit(1)
    |
    +---> [detection/specfy.py] SpecfyRunner.run(path)
    |         |
    |         +---> subprocess.run(["npx", "@specfy/stack-analyser", path])
    |         |     Returns: SpecfyResult(raw_json={...})
    |         +---> On error: raise DetectionError
    |
    +---> [detection/normalizer.py] normalize(raw_json)
    |         |
    |         +---> Walk Specfy JSON tree
    |         +---> Extract techs, languages, dependencies
    |         +---> Flag AI dependencies (openai, langchain, etc.)
    |         +---> Returns: ProjectProfile
    |
    +---> [output/terminal.py] render(profile)
              |
              +---> Rich Table: Technologies detected
              +---> Rich Table: Languages
              +---> Rich Table: Dependencies (with AI highlight)
              +---> Rich Panel: Summary stats
```

### Specfy JSON to ProjectProfile Mapping

Specfy outputs a nested tree of components. The normalizer must flatten this:

```
Specfy JSON (hierarchical)          ProjectProfile (flat)
─────────────────────────           ────────────────────────
{                                   ProjectProfile(
  name: "root",                       path=Path("."),
  childs: [                           technologies=[
    {                                   Technology("fastify", "framework"),
      techs: ["fastify","nodejs"],      Technology("nodejs", "runtime"),
      languages: {ts: 50},             ],
      dependencies: [                   languages={"typescript": 50},
        ["npm","fastify","4.0"],        dependencies=[
        ["npm","openai","4.2"],           Dependency("npm","fastify","4.0"),
      ]                                   Dependency("npm","openai","4.2"),
    }                                   ],
  ]                                     ai_dependencies=[
}                                         Dependency("npm","openai","4.2"),
                                        ],
                                      )
```

### Key Data Flows

1. **Detection flow:** CLI command -> Orchestrator -> SpecfyRunner (subprocess boundary) -> raw JSON -> Normalizer -> ProjectProfile
2. **Output flow:** ProjectProfile -> Renderer(s) -> terminal / JSON file / markdown file
3. **Error flow:** Any stage can raise -> Orchestrator catches -> Rich error display -> exit code

## Anti-Patterns

### Anti-Pattern 1: Parsing Specfy Output in the CLI Layer

**What people do:** Parse JSON and format output directly in `cli.py`, mixing command parsing with business logic.
**Why it's wrong:** Makes the CLI untestable without running the actual subprocess. Couples argument parsing to data transformation. Adding a second output format means duplicating parsing logic.
**Do this instead:** CLI layer calls orchestrator. Orchestrator calls runner, normalizer, renderer. CLI layer stays thin (under 50 lines per command).

### Anti-Pattern 2: Passing Raw Dicts Instead of Models

**What people do:** Pass the raw Specfy JSON dict through the entire system, accessing keys with `data["childs"][0]["techs"]` everywhere.
**Why it's wrong:** No type safety, no autocomplete, no validation. Specfy output changes break code silently at runtime. Every consumer re-interprets the same nested structure.
**Do this instead:** Normalize once into `ProjectProfile` at the boundary. Everything downstream works with typed dataclasses. If Specfy changes, only the normalizer changes.

### Anti-Pattern 3: Hardcoding npx Path or Assuming Shell

**What people do:** `subprocess.run("npx @specfy/stack-analyser .", shell=True)`
**Why it's wrong:** `shell=True` is a security risk (command injection via path names). Hardcoding `npx` fails on systems where it is not on PATH. Breaks on Windows where `npx` might be `npx.cmd`.
**Do this instead:** Use `shutil.which("npx")` to locate the binary. Pass args as a list, never as a shell string. On Windows, use `shutil.which("npx.cmd")` as fallback or set `shell=True` only on Windows with validated args.

### Anti-Pattern 4: Monolithic Single-File Architecture

**What people do:** Put everything in one `main.py` -- CLI, subprocess call, JSON parsing, Rich output.
**Why it's wrong:** Works for a prototype but prevents adding scanners, output formats, or detection engines later. Naz's roadmap explicitly includes Layer 2 (scanning) and Layer 3 (reporting), which require the modular boundaries set up now.
**Do this instead:** Use the component structure from day one. The overhead of 6-8 files vs 1 file is negligible. The payoff when adding scanning is enormous.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Specfy stack-analyser | `subprocess.run(["npx", "@specfy/stack-analyser", path])` | Requires Node.js. npx downloads on first run (slow). Output is JSON to stdout. No documented error codes -- must handle non-zero exit + stderr. |
| Node.js runtime | `shutil.which("node")` + `subprocess.run(["node", "--version"])` | Prerequisite check. Must run before Specfy. Clear error message if missing. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI -> Orchestrator | Direct method call | CLI passes parsed args (Path, flags). Orchestrator returns ProjectProfile or raises. |
| Orchestrator -> SpecfyRunner | Direct method call | Orchestrator passes Path. Runner returns SpecfyResult (raw JSON + metadata). |
| SpecfyRunner -> External Process | subprocess.run | This is the key isolation boundary. Everything outside this boundary is pure Python with no side effects. |
| Normalizer -> Models | Pure function | `normalize(dict) -> ProjectProfile`. No side effects, trivially testable. |
| Orchestrator -> Renderer | Direct method call | Passes ProjectProfile. Renderer writes to console (Rich) or file (JSON/markdown). |

## Build Order (Dependency Graph)

Components should be built in this order based on dependencies:

```
Phase 1: models.py              (no dependencies, needed by everything)
Phase 2: prereqs.py             (no dependencies, but needed early in pipeline)
Phase 3: detection/specfy.py    (depends on models for SpecfyResult)
Phase 4: detection/normalizer.py (depends on models + specfy output structure)
Phase 5: output/terminal.py     (depends on models for ProjectProfile)
Phase 6: orchestrator.py        (depends on all above)
Phase 7: cli.py                 (depends on orchestrator)
```

**Rationale:** Build from the inside out. Models first because they are the contract. Detection next because you cannot normalize what you have not captured. Output next because you need something to render. Orchestrator last because it glues everything together. CLI last because it is the thinnest layer.

**Key implication for roadmap:** The normalizer is the most complex component (Specfy's nested tree structure must be flattened and categorized). It deserves its own focused implementation step, not combined with the subprocess runner.

## Scaling Considerations

| Concern | Now (v0.1) | Future (v0.3+) | Notes |
|---------|------------|-----------------|-------|
| Multiple detection engines | Single (Specfy) | Specfy + AI-specific + fallback | Detection interface stays the same: `run(path) -> result`, `normalize(result) -> ProjectProfile`. New engines implement same interface. |
| Multiple output formats | Terminal only | Terminal + JSON + Markdown | All renderers consume `ProjectProfile`. Add new renderer module, register in orchestrator. |
| Multiple scan types | Detection only | Detection + vulnerability + secrets | Orchestrator gains new pipeline stages. Each scanner is isolated like SpecfyRunner. |
| Large monorepos | Single Specfy call | Possible timeout/memory issues | Specfy handles large repos via its tree structure. Add configurable timeout. |

## Sources

- [Specfy stack-analyser GitHub](https://github.com/specfy/stack-analyser) -- output format, CLI usage, tech coverage
- [Safety CLI architecture (DeepWiki)](https://deepwiki.com/pyupio/safety) -- pipeline pattern, modular scanner design, multi-format output
- [Typer documentation](https://typer.tiangolo.com/) -- CLI framework patterns
- [Real Python: Python subprocess](https://realpython.com/python-subprocess/) -- subprocess wrapper patterns
- [codecentric: Modern CMD tool with Python using Typer and Rich](https://www.codecentric.de/en/knowledge-hub/blog/lets-build-a-modern-cmd-tool-with-python-using-typer-and-rich) -- Typer + Rich integration
- [libvcs SubprocessCommand](https://libvcs.git-pull.com/internals/subprocess.html) -- dataclass-based subprocess wrapper pattern

---
*Architecture research for: Naz CLI security detection tool*
*Researched: 2026-03-25*
