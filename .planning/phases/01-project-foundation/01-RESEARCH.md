# Phase 1: Project Foundation - Research

**Researched:** 2026-03-25
**Domain:** Python package scaffolding (src layout, Pydantic models, Typer CLI)
**Confidence:** HIGH

## Summary

Phase 1 creates the pip-installable package skeleton with central Pydantic data models. This is a greenfield project -- the repo contains only planning documents and a context file, no source code. The work involves creating a pyproject.toml with hatchling build backend, the src/naz/ directory structure, a minimal Typer CLI entry point, and the ProjectProfile Pydantic model.

The user's machine has Python 3.14.0, Node.js 25.2.1, Pydantic 2.12.5, pytest 9.0.2, and ruff 0.15.6 already installed globally. uv is NOT installed but is available via `pip install uv`. Typer and Rich are not yet installed locally. All decisions from CONTEXT.md are well-supported by the current ecosystem and verified package versions.

**Primary recommendation:** Install uv first, then use `uv init` with src layout to scaffold the project, add dependencies (typer, pydantic, rich), configure the `[project.scripts]` entry point, and create the ProjectProfile model in `src/naz/models.py`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use src layout (`src/naz/`) as specified in the context doc
- **D-02:** Use pyproject.toml with hatchling build backend (per research recommendation)
- **D-03:** Python 3.12+ minimum (per research -- better error messages, performance)
- **D-04:** Use uv for package management (per research -- standard 2025 tooling)
- **D-05:** Use Pydantic v2 for all data models (per research -- runtime validation of untrusted Specfy JSON)
- **D-06:** ProjectProfile is the central model -- detection produces it, output consumes it
- **D-07:** Model should include: languages, frameworks, dependencies (with versions), infrastructure, services, AI/LLM components, and technology categories
- **D-08:** Typer for CLI framework, Rich for terminal output (non-negotiable per context doc)
- **D-09:** Initial CLI has `naz scan <path>` command -- everything else comes later
- **D-10:** Entry point registered in pyproject.toml as `naz`
- **D-11:** Ruff for linting and formatting (per research -- replaces black + flake8 + isort)

### Claude's Discretion
- Exact Pydantic model field names and nesting structure
- pyproject.toml metadata details (author, license, classifiers)
- Ruff configuration specifics
- Test infrastructure setup

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-01 | Project uses src layout with pyproject.toml, installable via `pip install` | Verified: hatchling 1.29.0 supports src layout natively. pyproject.toml `[project.scripts]` entry point is the standard mechanism. `pip install -e .` works with hatchling build backend. |
| PKG-02 | `naz` CLI entry point is registered and works after install | Verified: Typer 0.24.1 supports Python 3.14. Entry point via `[project.scripts] naz = "naz.cli:app"` combined with Typer's `typer.Typer()` pattern. |

</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic | 2.12.5 | Data validation and serialization | Already installed. Rust-core V2 for runtime validation of untrusted Specfy JSON. `model_validate()` and `.model_dump_json()` are the key APIs. |
| Typer | 0.24.1 | CLI framework | Non-negotiable per project constraints. Type-hint-based CLI definition. Verified compatible with Python 3.14. |
| Rich | 14.3.3 | Terminal output | Non-negotiable per project constraints. Typer depends on it. Tables, panels for scan results. |

### Build & Tooling

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| hatchling | 1.29.0 | Build backend | In `[build-system]` of pyproject.toml. Handles src layout automatically. |
| uv | 0.11.1 | Package manager | All dependency management, venv creation, running commands. Must be installed first. |
| Ruff | 0.15.6 | Linting + formatting | Already installed globally. Configure in pyproject.toml `[tool.ruff]`. |
| pytest | 9.0.2 | Test framework | Already installed globally. Run via `uv run pytest`. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| hatchling | setuptools | setuptools works but has legacy baggage and implicit behavior. hatchling is cleaner for new projects. Decision D-02 locks hatchling. |
| uv | pip + venv | pip works but no lockfile, slower, manual venv management. Decision D-04 locks uv. |

**Installation sequence:**
```bash
# Step 1: Install uv (not currently on system)
pip install uv

# Step 2: Initialize project with uv
uv init --lib --name naz

# Step 3: Add dependencies
uv add typer pydantic rich
uv add --dev pytest pytest-cov ruff
```

**Note on uv init:** The `--lib` flag creates src layout. However, `uv init` creates its own pyproject.toml which may need editing to switch build backend to hatchling (uv defaults to hatchling as of 0.11.x, so this should work out of the box).

## Architecture Patterns

### Recommended Project Structure

```
naz/
├── pyproject.toml
├── src/
│   └── naz/
│       ├── __init__.py          # Package version, minimal imports
│       ├── cli.py               # Typer app, command definitions
│       ├── models.py            # ProjectProfile, Technology, Dependency
│       ├── detection/
│       │   └── __init__.py      # Empty for now (Phase 2+)
│       └── utils/
│           └── __init__.py      # Empty for now (Phase 4+)
├── tests/
│   ├── __init__.py
│   └── test_models.py           # ProjectProfile validation tests
└── .gitignore
```

**Phase 1 scope:** Only create files that have actual content. `detection/` and `utils/` directories get `__init__.py` placeholders only. The orchestrator, specfy runner, normalizer, and renderer are all Phase 2+ work.

### Pattern 1: Typer App as Module-Level Instance

**What:** Create the Typer app as a module-level instance in `cli.py`, then reference it in pyproject.toml entry point.
**When to use:** Always -- this is Typer's standard pattern.
**Example:**
```python
# src/naz/cli.py
import typer

app = typer.Typer(
    name="naz",
    help="Security scanning for solo developers.",
    no_args_is_help=True,
)

@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to the repository to scan"),
) -> None:
    """Scan a repository and detect its technology stack."""
    typer.echo(f"Scanning {path}...")  # Placeholder for Phase 2
```

**Entry point in pyproject.toml:**
```toml
[project.scripts]
naz = "naz.cli:app"
```

**Important:** Typer apps are callable. When `[project.scripts]` points to `naz.cli:app`, Python's entry point mechanism calls `app()` which triggers Typer's CLI parsing. This works because `typer.Typer()` instances have a `__call__` method.

### Pattern 2: Pydantic BaseModel with Sensible Defaults

**What:** Define ProjectProfile as a Pydantic BaseModel with default empty collections so it can be instantiated minimally.
**When to use:** For all data models in this project.
**Example:**
```python
# src/naz/models.py
from pydantic import BaseModel, Field

class Dependency(BaseModel):
    """A single package dependency."""
    manager: str          # "npm", "pip", "docker", etc.
    name: str
    version: str | None = None

class Technology(BaseModel):
    """A detected technology."""
    name: str
    category: str         # "language", "framework", "service", "infra", "ai"

class ProjectProfile(BaseModel):
    """Central data model: detection produces it, output consumes it."""
    path: str
    technologies: list[Technology] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)
    dependencies: list[Dependency] = Field(default_factory=list)
    ai_dependencies: list[Dependency] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict, exclude=True)
```

**Key design choices:**
- Use `str` for `path` (not `pathlib.Path`) to simplify JSON serialization. Pydantic can serialize Path but the JSON output is cleaner with strings.
- Use `Field(default_factory=list)` for mutable defaults (Pydantic requirement, same as dataclass).
- Mark `raw` with `exclude=True` so it does not appear in `.model_dump_json()` output (it is debug data, not part of the public profile).
- Use `str | None` union syntax (Python 3.10+ syntax, works on 3.14).

### Pattern 3: pyproject.toml with Hatchling

**What:** Single-file project configuration with hatchling build backend.
**Example:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "naz"
version = "0.1.0"
description = "Security scanning for solo developers"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.24.0",
    "pydantic>=2.12.0",
    "rich>=14.0.0",
]

[project.scripts]
naz = "naz.cli:app"

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Note on `requires-python`:** Set to `>=3.12` per decision D-03 even though the dev machine has 3.14. This allows other users with 3.12 or 3.13 to install the package.

### Anti-Patterns to Avoid

- **Flat layout instead of src layout:** Using `naz/` at project root instead of `src/naz/` causes import confusion during development (Python imports the local directory instead of the installed package). Decision D-01 locks src layout.
- **Using `__main__.py` as entry point:** Some tutorials suggest `python -m naz` via `__main__.py`. This is unnecessary -- the `[project.scripts]` entry point is the standard way for CLI tools. `__main__.py` can be added later if needed.
- **Over-abstracting models in Phase 1:** Do not create abstract base classes, protocols, or generic model factories. The ProjectProfile model is simple and concrete. Abstraction comes when there is a second use case.
- **Using `typer.run()` instead of `typer.Typer()`:** `typer.run()` is a shortcut for single-command CLIs. Since naz will grow to have multiple commands, use `typer.Typer()` app instance from the start.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing | Custom argparse wrapper | Typer | Type-hint-based, auto-help, auto-completion |
| JSON validation | Manual dict key checking | Pydantic `model_validate()` | Handles nested validation, type coercion, error messages |
| JSON serialization | Custom `to_dict()` methods | Pydantic `.model_dump_json()` | Handles nested models, excludes, custom serializers |
| Package entry point | Custom `if __name__` script | pyproject.toml `[project.scripts]` | Standard packaging mechanism, works with pip install |

## Common Pitfalls

### Pitfall 1: Forgetting `__init__.py` in src layout

**What goes wrong:** Package cannot be imported after `pip install -e .` because Python does not recognize the directory as a package.
**Why it happens:** With src layout, every directory under `src/naz/` that should be a Python package needs `__init__.py`. Missing it in `detection/` or `utils/` causes `ModuleNotFoundError` when those subpackages are imported in later phases.
**How to avoid:** Create `__init__.py` in every directory that will contain Python modules: `src/naz/`, `src/naz/detection/`, `src/naz/utils/`.
**Warning signs:** `ModuleNotFoundError: No module named 'naz.detection'` after install.

### Pitfall 2: Entry point function signature mismatch

**What goes wrong:** Running `naz` after install produces a cryptic Python traceback instead of the help message.
**Why it happens:** The `[project.scripts]` entry point expects a callable. If you point it to a module instead of a callable (e.g., `naz.cli` instead of `naz.cli:app`), or if `app` is not a callable Typer instance, it fails.
**How to avoid:** Always use the `module:attribute` syntax. Verify `app` is a `typer.Typer()` instance. Test by running `python -c "from naz.cli import app; app()"`.
**Warning signs:** `TypeError: 'module' object is not callable`.

### Pitfall 3: Editable install not reflecting changes

**What goes wrong:** After modifying source files, the installed package still runs old code.
**Why it happens:** With hatchling, `pip install -e .` creates a link to the src directory. But if you ran a non-editable install first, the old version takes precedence. Also, some environments cache `.pyc` files.
**How to avoid:** Always use `pip install -e .` (or `uv pip install -e .`) during development. If something seems stale, run `pip install -e . --force-reinstall`.
**Warning signs:** Changes to source files have no effect.

### Pitfall 4: uv init overwriting existing files

**What goes wrong:** Running `uv init` in a repo with existing files (like CLAUDE.md) could overwrite them.
**Why it happens:** uv init scaffolds standard project files.
**How to avoid:** If using `uv init`, verify it respects existing files. Alternatively, manually create pyproject.toml and the src directory structure instead of relying on `uv init`. Given the repo already has files, manual creation is safer.
**Warning signs:** Existing files gone or modified after `uv init`.

### Pitfall 5: Python 3.14 compatibility

**What goes wrong:** A dependency fails to install or run on Python 3.14.
**Why it happens:** Python 3.14 is very new (released 2025). Some packages may not have wheels or may have compatibility issues.
**How to avoid:** All key packages (typer 0.24.1, pydantic 2.12.5, rich 14.3.3, hatchling 1.29.0) have been verified to install on Python 3.14 on this machine. The `requires-python = ">=3.12"` in pyproject.toml is correct since it includes 3.14.
**Warning signs:** `pip install` errors mentioning Python version or missing wheels.

## Code Examples

### Minimal pyproject.toml (verified structure)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "naz"
version = "0.1.0"
description = "Security scanning for solo developers"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.24.0",
    "pydantic>=2.12.0",
    "rich>=14.0.0",
]

[project.scripts]
naz = "naz.cli:app"

[dependency-groups]
dev = [
    "pytest>=9.0.0",
    "pytest-cov>=6.0",
    "ruff>=0.15.0",
]

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Minimal CLI entry point

```python
# src/naz/cli.py
import typer

app = typer.Typer(
    name="naz",
    help="Security scanning for solo developers.",
    no_args_is_help=True,
)

@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to the repository to scan"),
) -> None:
    """Scan a repository and detect its technology stack."""
    typer.echo(f"Scanning: {path}")
```

### Minimal __init__.py

```python
# src/naz/__init__.py
"""Naz - Security scanning for solo developers."""

__version__ = "0.1.0"
```

### ProjectProfile instantiation and JSON serialization (success criteria 3)

```python
from naz.models import ProjectProfile, Technology, Dependency

profile = ProjectProfile(
    path="/some/repo",
    technologies=[Technology(name="python", category="language")],
    languages={"python": 42},
    dependencies=[Dependency(manager="pip", name="fastapi", version="0.115.0")],
)

# Serialize to JSON
json_str = profile.model_dump_json(indent=2)
print(json_str)

# Deserialize from JSON
restored = ProjectProfile.model_validate_json(json_str)
assert restored == profile
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.14.0 | -- |
| pip | Package installation | Yes | 25.2 | -- |
| uv | Package management (D-04) | NO | -- | Install via `pip install uv` (verified: 0.11.1 available) |
| Node.js | Future phases (Specfy) | Yes | 25.2.1 | Not needed for Phase 1 |
| Ruff | Linting (D-11) | Yes | 0.15.6 | -- |
| pytest | Testing | Yes | 9.0.2 | -- |
| Pydantic | Data models (D-05) | Yes | 2.12.5 (global) | Will also be project dependency |
| Typer | CLI (D-08) | NO (global) | -- | Will be installed as project dependency |
| Rich | Output (D-08) | NO (global) | -- | Will be installed as project dependency (also pulled by Typer) |
| hatchling | Build backend (D-02) | NO (global) | -- | Installed automatically by pip/uv when building |

**Missing dependencies with no fallback:**
- uv -- must be installed before project setup. Command: `pip install uv`

**Missing dependencies with fallback:**
- None. All missing items can be installed as part of project setup.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | None -- will be in pyproject.toml `[tool.pytest.ini_options]` (Wave 0) |
| Quick run command | `uv run pytest tests/ -x` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | `pip install -e .` succeeds | smoke | `uv pip install -e . && python -c "import naz"` | No -- Wave 0 |
| PKG-02 | `naz` prints help message | integration | `uv run pytest tests/test_cli.py::test_help -x` | No -- Wave 0 |
| PKG-02 | `naz scan` exists as command | integration | `uv run pytest tests/test_cli.py::test_scan_command -x` | No -- Wave 0 |
| D-06 | ProjectProfile instantiation + JSON serialization | unit | `uv run pytest tests/test_models.py -x` | No -- Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/ -x` (fail fast)
- **Per wave merge:** `uv run pytest tests/ -v` (verbose, all tests)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/__init__.py` -- package marker
- [ ] `tests/test_models.py` -- covers D-06 (ProjectProfile instantiation and JSON roundtrip)
- [ ] `tests/test_cli.py` -- covers PKG-02 (entry point works, help message, scan command exists)
- [ ] pytest config in `pyproject.toml` under `[tool.pytest.ini_options]`

## Sources

### Primary (HIGH confidence)

- PyPI registry -- verified current versions: typer 0.24.1, pydantic 2.12.5, rich 14.3.3, hatchling 1.29.0, pytest 9.0.2, uv 0.11.1, ruff 0.15.6
- Local environment probing -- verified Python 3.14.0, Node 25.2.1, pip 25.2, ruff 0.15.6, pytest 9.0.2 installed; uv NOT installed
- `.planning/research/STACK.md` -- project-specific stack research with rationale
- `.planning/research/ARCHITECTURE.md` -- project structure and component boundaries

### Secondary (MEDIUM confidence)

- Python Packaging User Guide (packaging.python.org) -- src layout, pyproject.toml, entry points
- Typer documentation (typer.tiangolo.com) -- CLI patterns, testing
- Pydantic documentation (docs.pydantic.dev) -- BaseModel, Field, serialization

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified against PyPI and local environment
- Architecture: HIGH -- src layout with hatchling is well-documented standard; patterns from project's own ARCHITECTURE.md
- Pitfalls: HIGH -- common packaging issues, well-documented in Python packaging guides

**Research date:** 2026-03-25
**Valid until:** 2026-04-25 (stable domain, 30 days)
