---
phase: 01-project-foundation
plan: 02
subsystem: core-models
tags: [pydantic, models, testing, tdd, cli-tests]

requires:
  - phase: 01-01
    provides: pip-installable package with CLI entry point
provides:
  - ProjectProfile, Technology, Dependency Pydantic models
  - Full test suite (7 model + 4 CLI = 11 tests)
affects: [02-specfy-integration, all-future-phases]

tech-stack:
  added: [pydantic BaseModel, Field with exclude]
  patterns: [TDD red-green, Pydantic model_dump_json/model_validate_json, CliRunner testing]

key-files:
  created:
    - src/naz/models.py
    - tests/test_models.py
    - tests/test_cli.py
  modified: []

key-decisions:
  - "Typer no_args_is_help returns exit code 2, not 0 - test accepts both"

patterns-established:
  - "ProjectProfile is the central data model: detection produces it, output consumes it"
  - "raw field excluded from JSON serialization via Field(exclude=True)"
  - "TDD workflow: write failing tests first, then implement"

requirements-completed: [PKG-01, PKG-02]

duration: 2min
completed: 2026-03-25
---

# Phase 01 Plan 02: Pydantic Models and Test Suite Summary

**ProjectProfile, Technology, Dependency Pydantic models with full TDD test coverage and CLI integration tests**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-25T22:19:52Z
- **Completed:** 2026-03-25T22:21:20Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Created ProjectProfile as the central data model (detection produces it, output consumes it)
- Technology and Dependency sub-models with proper validation
- raw field excluded from JSON serialization for Specfy internals
- JSON roundtrip verified (model_dump_json -> model_validate_json)
- CLI integration tests with CliRunner covering --help, no-args, scan default, scan custom
- All 11 tests passing (7 model + 4 CLI)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing model tests** - `b56b253` (test)
2. **Task 1 (GREEN): Pydantic models implementation** - `abaa25f` (feat)
3. **Task 2: CLI integration tests** - `8a295b9` (feat)

## Files Created/Modified
- `src/naz/models.py` - ProjectProfile, Technology, Dependency Pydantic models
- `tests/test_models.py` - 7 unit tests for data models
- `tests/test_cli.py` - 4 CLI integration tests using CliRunner

## Decisions Made
- Typer's `no_args_is_help=True` returns exit code 2 (not 0) when invoked with no args -- test accepts both 0 and 2 to handle this behavior correctly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed no_args_is_help exit code expectation**
- **Found during:** Task 2 (CLI integration tests)
- **Issue:** Plan's test expected exit_code == 0 for no-args invocation, but Typer returns exit code 2 for no_args_is_help
- **Fix:** Changed assertion to accept exit_code in (0, 2)
- **Files modified:** tests/test_cli.py
- **Committed in:** 8a295b9

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minimal -- test assertion adjusted to match actual Typer behavior.

## Known Stubs
None -- all models are fully implemented with real fields and validation.

## Issues Encountered
None beyond the Typer exit code behavior handled above.

## User Setup Required
None.

## Next Phase Readiness
- ProjectProfile model ready to receive Specfy detection output
- Test infrastructure established with pytest and CliRunner
- All 11 tests green, ruff lint clean

## Self-Check: PASSED

All 3 created files verified on disk. All 3 task commits (b56b253, abaa25f, 8a295b9) verified in git log.

---
*Phase: 01-project-foundation*
*Completed: 2026-03-25*
