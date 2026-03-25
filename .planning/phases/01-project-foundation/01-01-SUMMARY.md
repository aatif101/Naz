---
phase: 01-project-foundation
plan: 01
subsystem: infra
tags: [python, typer, hatchling, uv, cli, packaging]

requires:
  - phase: none
    provides: greenfield project
provides:
  - pip-installable Python package with src layout
  - naz CLI entry point with scan and version subcommands
  - pyproject.toml with hatchling build backend
affects: [01-02, 02-specfy-integration, all-future-phases]

tech-stack:
  added: [typer 0.24.1, pydantic 2.12.5, rich 14.3.3, hatchling, uv, ruff, pytest]
  patterns: [src layout, pyproject.toml config, Typer CLI app pattern]

key-files:
  created:
    - pyproject.toml
    - src/naz/__init__.py
    - src/naz/cli.py
    - src/naz/detection/__init__.py
    - src/naz/utils/__init__.py
    - tests/__init__.py
    - .gitignore
    - uv.lock
  modified: []

key-decisions:
  - "Added version command to preserve Typer subcommand structure"

patterns-established:
  - "src layout: all source code under src/naz/"
  - "Typer app defined in src/naz/cli.py as app = typer.Typer()"
  - "Entry point: naz = naz.cli:app in pyproject.toml"

requirements-completed: [PKG-01, PKG-02]

duration: 2min
completed: 2026-03-25
---

# Phase 01 Plan 01: Package Skeleton Summary

**Pip-installable Python package with Typer CLI entry point, src layout, and hatchling build backend**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T22:16:27Z
- **Completed:** 2026-03-25T22:18:17Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Created pyproject.toml with hatchling build backend, dependency groups, ruff/pytest config
- Established src layout with naz package, detection and utils sub-packages
- CLI entry point working: `naz --help`, `naz scan`, `naz version` all functional
- Package installed via uv in editable mode with all dependencies

## Task Commits

Each task was committed atomically:

1. **Task 1: Create project skeleton and pyproject.toml** - `fda887d` (feat)
2. **Task 2: Create CLI entry point and install package** - `c5184e7` (feat)

## Files Created/Modified
- `pyproject.toml` - Project config with hatchling, dependencies, tool config
- `src/naz/__init__.py` - Package marker with __version__ = "0.1.0"
- `src/naz/cli.py` - Typer CLI app with scan and version commands
- `src/naz/detection/__init__.py` - Placeholder for detection module
- `src/naz/utils/__init__.py` - Placeholder for utils module
- `tests/__init__.py` - Test package marker
- `.gitignore` - Standard Python ignores
- `uv.lock` - Dependency lockfile from uv

## Decisions Made
- Added a `version` command alongside `scan` to force Typer to keep subcommand structure (single command causes Typer to flatten CLI, losing the `naz scan` subcommand pattern)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added version command to preserve subcommand structure**
- **Found during:** Task 2 (CLI entry point)
- **Issue:** Typer with a single @app.command() collapses the CLI to a flat structure, making `naz scan /path` fail (path treated as unexpected argument)
- **Fix:** Added a `version` command so Typer maintains the subcommand group pattern
- **Files modified:** src/naz/cli.py
- **Verification:** `naz scan /tmp/test` outputs "Scanning: /tmp/test", `naz --help` shows both scan and version commands
- **Committed in:** c5184e7

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor addition to preserve intended CLI behavior. No scope creep.

## Issues Encountered
None beyond the Typer subcommand collapse handled above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Package skeleton complete, ready for Pydantic models and Specfy integration
- All sub-packages (detection, utils) ready for population
- Dev tooling (pytest, ruff) installed and configured

## Self-Check: PASSED

All 8 created files verified on disk. Both task commits (fda887d, c5184e7) verified in git log.

---
*Phase: 01-project-foundation*
*Completed: 2026-03-25*
