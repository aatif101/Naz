# Technology Stack

**Project:** Naz - CLI Security Tool for Solo Developers
**Researched:** 2026-03-25
**Overall Confidence:** HIGH

## Recommended Stack

### Runtime & Language

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | >=3.12 | Runtime | 3.12 is the sweet spot: stable, performant (PEP 709 inlined comprehensions), wide adoption. 3.10 is Typer's minimum but 3.12 gives better error messages and performance. Pin minimum to 3.12, test on 3.13. | HIGH |
| Node.js | >=18 | Specfy runtime | Required for `npx @specfy/stack-analyser`. LTS 18+ is the minimum that supports modern npx behavior. | HIGH |

### CLI Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Typer | ^0.24.1 | CLI commands & argument parsing | Non-negotiable per project constraints. Current stable is 0.24.1 (Feb 2026). Built on Click, provides type-hint-based CLI definition, auto-completion, and built-in testing via `CliRunner`. | HIGH |
| Rich | ^14.3.3 | Terminal output formatting | Non-negotiable per project constraints. Current stable is 14.3.3 (Feb 2026). Tables, panels, syntax highlighting, progress bars, and tree views for scan results. Typer uses Rich internally. | HIGH |

### Data Modeling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Pydantic | ^2.12.5 | Data validation & serialization | Use Pydantic, not dataclasses. Naz parses untrusted JSON from subprocess output (Specfy) -- this is exactly Pydantic's strength. Built-in JSON serialization for the dual-output requirement (markdown + JSON). `model_validate_json()` parses directly from bytes. V2's Rust core makes validation fast enough that the "dataclasses are faster" argument is irrelevant for a CLI that shells out to Node.js. | HIGH |

**Why not dataclasses:** Dataclasses provide no runtime validation. When parsing Specfy's JSON output, you want type coercion, missing field handling, and clear error messages -- all built into Pydantic. You'd end up reimplementing half of Pydantic with manual `__post_init__` validation. For a CLI tool that processes external data, Pydantic is the correct choice.

### Subprocess Management

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| subprocess (stdlib) | N/A | Running Specfy via npx | Use `subprocess.run()` with `capture_output=True`, not asyncio. Naz runs one subprocess at a time (Specfy scan), waits for it, then processes output. Asyncio subprocess adds complexity for zero benefit here. Use `shutil.which("npx")` for Node.js detection. | HIGH |

**Key subprocess patterns for this project:**
- `subprocess.run(["npx", "@specfy/stack-analyser", path, "--output=json"], capture_output=True, text=True, timeout=120)` -- never use `shell=True`
- Check `returncode` before parsing stdout
- Parse stderr for error diagnostics
- Set `timeout` to prevent hanging on large repos
- Use `shutil.which("npx")` to verify Node.js is installed before attempting to run

**Why not asyncio subprocess:** The tool runs a single Specfy scan, waits for it, parses the result. There is no concurrency benefit. `subprocess.run()` is simpler, synchronous, and perfectly adequate. If future phases add parallel scanning with multiple tools, revisit then.

### JSON Parsing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| json (stdlib) | N/A | Initial JSON loading | Use stdlib `json.loads()` to parse Specfy's stdout, then pass the dict to Pydantic's `model_validate()`. No need for orjson or ujson -- Specfy output is small (KB range). | HIGH |
| Pydantic | ^2.12.5 | Structured parsing & validation | After `json.loads()`, use `ProjectProfile.model_validate(data)` for type-safe access. Or use `model_validate_json(raw_bytes)` to skip the intermediate dict. | HIGH |

### Packaging & Build

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| uv | latest | Package manager & project tooling | uv is the 2025/2026 standard Python package manager. 10-100x faster than pip, built-in venv management, lockfile support, project init with src layout. Created by Astral (same team as Ruff). Use `uv init --lib` for src layout, `uv add` for dependencies. | HIGH |
| hatchling | latest | Build backend | Modern, fast, minimal-config build backend. Works seamlessly with src layout and pyproject.toml. Preferred over setuptools (legacy baggage) and flit (less flexible). | MEDIUM |

**pyproject.toml is the only config file.** No setup.py, setup.cfg, or requirements.txt. All tool configuration (ruff, pytest, project metadata) goes in pyproject.toml.

### Project Structure

```
naz/
  pyproject.toml
  uv.lock
  src/
    naz/
      __init__.py
      __main__.py        # python -m naz support
      cli.py             # Typer app definition, commands
      models.py          # Pydantic models (ProjectProfile, etc.)
      scanner/
        __init__.py
        specfy.py        # Specfy subprocess wrapper
      output/
        __init__.py
        console.py       # Rich formatting for terminal output
        json_report.py   # JSON report generation
  tests/
    __init__.py
    conftest.py          # Shared fixtures
    test_cli.py          # CLI integration tests via CliRunner
    test_models.py       # Pydantic model tests
    test_specfy.py       # Specfy subprocess mock tests
    fixtures/
      specfy_output.json # Sample Specfy JSON for tests
```

**Why src layout:** Prevents accidental import of the local package instead of the installed one. This is the Python Packaging Authority recommendation. `uv init --lib` generates this layout automatically.

### Code Quality

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Ruff | ^0.15.7 | Linting + formatting | Single tool replaces flake8, black, isort, pyupgrade. 10-100x faster than alternatives. Configure in pyproject.toml under `[tool.ruff]`. Use both linting and formatting modes. | HIGH |
| mypy | ^1.14 | Static type checking | Type safety for Pydantic models and CLI code. Pydantic V2 has excellent mypy plugin support. Alternative: pyright, but mypy has broader community adoption. | MEDIUM |

**Why not black + flake8 + isort:** Ruff does all three, faster, in one tool. The Python ecosystem has consolidated around Ruff. No reason to use the individual tools anymore.

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | ^9.0.2 | Test framework | Industry standard. Current stable is 9.0.2 (Dec 2025). Requires Python >=3.10. | HIGH |
| pytest-cov | ^6.0 | Coverage reporting | Standard coverage plugin for pytest. | HIGH |
| typer.testing.CliRunner | (bundled) | CLI integration testing | Built into Typer. Create runner, invoke app with args, assert on exit_code, stdout, stderr. Use `mix_stderr=False` to test error output separately. | HIGH |

**Testing strategy:**
- **Unit tests:** Pydantic model validation, JSON parsing logic
- **Integration tests:** CliRunner for end-to-end CLI behavior
- **Mock subprocess:** Use `unittest.mock.patch("subprocess.run")` to mock Specfy output in tests. Store fixture JSON files in `tests/fixtures/`
- **No need for:** pytest-asyncio (no async), pytest-mock (stdlib mock is sufficient), tox (uv handles environments)

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| shutil (stdlib) | N/A | `shutil.which("npx")` | Node.js detection before running Specfy | HIGH |
| pathlib (stdlib) | N/A | Path manipulation | All file/directory path handling. Never use os.path. | HIGH |
| typing (stdlib) | N/A | Type annotations | Used throughout, especially with Pydantic models | HIGH |
| enum (stdlib) | N/A | Enumerations | Technology categories, severity levels, output formats | HIGH |

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| Click (directly) | Typer wraps Click. Use Typer's API, not Click's. Don't import Click directly. |
| argparse | Legacy. Typer is the modern replacement. |
| dataclasses | No runtime validation. Pydantic is the right choice for parsing external JSON. |
| asyncio | No concurrency needed in v0.1. One subprocess, one parse, one output. |
| Poetry | uv is faster, simpler, and the emerging standard. Poetry's resolver is slow and its lock format is non-standard. |
| pip + requirements.txt | Legacy workflow. pyproject.toml + uv.lock is the modern standard. |
| black / flake8 / isort | Ruff replaces all three. Don't install separate tools. |
| orjson / ujson | Overkill for parsing KB-sized Specfy output. stdlib json is fine. |
| setuptools | Legacy build backend with too much implicit behavior. Use hatchling. |
| tox | uv handles virtual environments and test running. `uv run pytest` is sufficient. |
| rich-click | Typer already integrates Rich. Adding rich-click creates conflicts. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| Data modeling | Pydantic v2 | dataclasses | No runtime validation, no JSON serialization, would need manual validation code |
| Data modeling | Pydantic v2 | attrs | Less ecosystem support, no built-in JSON schema, Pydantic is the Python standard for data validation |
| Package manager | uv | Poetry | Slower resolver, non-standard lock format, heavier install |
| Package manager | uv | pip + venv | No lockfile, no dependency resolution, manual venv management |
| Build backend | hatchling | setuptools | Legacy, complex configuration, implicit behavior |
| Build backend | hatchling | flit | Less flexible for CLI entry points, fewer features |
| Linter/formatter | Ruff | black + flake8 | Multiple tools, slower, more config files |
| Type checker | mypy | pyright | Either works, but mypy has broader community adoption and better Pydantic plugin |
| Subprocess | subprocess.run | asyncio.subprocess | No concurrency benefit for single sequential subprocess calls |

## Installation

```bash
# Initialize project (if starting fresh)
uv init --lib naz
cd naz

# Core dependencies
uv add typer rich pydantic

# Dev dependencies
uv add --dev pytest pytest-cov ruff mypy

# Run the tool
uv run naz scan .

# Run tests
uv run pytest

# Run linter
uv run ruff check src/
uv run ruff format src/
```

## pyproject.toml Template

```toml
[project]
name = "naz"
version = "0.1.0"
description = "CLI security tool for solo developers"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.24.1",
    "rich>=14.3.3",
    "pydantic>=2.12.5",
]

[project.scripts]
naz = "naz.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/naz"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
src = ["src"]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]

[tool.mypy]
python_version = "3.12"
plugins = ["pydantic.mypy"]
strict = true
```

## Specfy Integration Details

**Package:** `@specfy/stack-analyser` (npm)
**Invocation:** `npx @specfy/stack-analyser <path> --output=<filename>`
**Output:** JSON with structure containing `id`, `name`, `path`, `tech`, `techs`, `languages`, `dependencies` (tuples of `[package_manager, package_name, version]`), `edges`, `childs`
**Key consideration:** First npx invocation downloads the package (~cold start). Subsequent runs use cached version. Warn users about the first-run delay.

## Sources

- [Python Packaging User Guide - src layout vs flat layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)
- [Python Packaging User Guide - Writing pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [Typer Official Documentation](https://typer.tiangolo.com/)
- [Typer PyPI - v0.24.1](https://pypi.org/project/typer/)
- [Rich GitHub - v14.3.3](https://github.com/Textualize/rich)
- [Pydantic Official Documentation](https://docs.pydantic.dev/latest/)
- [Pydantic PyPI - v2.12.5](https://pypi.org/project/pydantic/)
- [pytest PyPI - v9.0.2](https://pypi.org/project/pytest/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [uv Documentation](https://docs.astral.sh/uv/guides/projects/)
- [Specfy stack-analyser GitHub](https://github.com/specfy/stack-analyser)
- [Typer Testing Documentation](https://typer.tiangolo.com/tutorial/testing/)
- [Python subprocess Documentation](https://docs.python.org/3/library/subprocess.html)
