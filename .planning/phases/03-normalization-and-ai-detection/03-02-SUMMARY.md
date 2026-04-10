---
phase: 03-normalization-and-ai-detection
plan: 02
subsystem: detection
tags: [testing, normalizer, ai-detection, tech-categorization, pytest]
dependency_graph:
  requires: [src/naz/detection/normalizer.py, src/naz/models.py, src/naz/detection/exceptions.py, tests/fixtures/specfy_flat.json]
  provides: [tests/test_normalizer.py]
  affects: []
tech_stack:
  added: []
  patterns: [plain-pytest-functions, fixture-constant, focused-assertions]
key_files:
  created:
    - tests/test_normalizer.py
  modified: []
decisions:
  - "fixture test asserts javascript→other (not runtime) since 'javascript' is not in _TECH_CATEGORIES — accurate to implementation"
  - "18 plain pytest functions with no class nesting — matches project's simple and readable style"
metrics:
  duration: "2min"
  completed: "2026-04-10"
  tasks: 1
  files: 1
requirements:
  - DET-02
  - DET-03
  - DET-04
  - DET-05
---

# Phase 03 Plan 02: Normalizer Test Suite Summary

**One-liner:** 18-test pytest suite verifying all normalize() behaviors — DET-02 through DET-05 — including AI prefix matching, lenient field handling, and fixture integration.

## What Was Built

`tests/test_normalizer.py` — executable specification for the `normalize()` function. Covers:

1. **DET-02:** `normalize(raw_dict)` returns a `ProjectProfile` instance
2. **DET-03:** Technologies (with categories), languages dict, and dependencies (with versions) are all present in the result
3. **DET-04:** AI package routing — exact match (`openai`), prefix match (`langchain-openai`), false positive guard (`langchainwrapper` stays in dependencies), comprehensive AI list (anthropic, crewai, chromadb, transformers, ollama, mem0ai)
4. **DET-05:** Tech category assignment — runtime (`python`), framework (`django`), other (`unknownthing123`)
5. **Edge cases:** empty dict, null fields, missing fields, 2-element deps (no version), malformed 1-element deps skipped, non-dict raises `SpecfyError`
6. **Fixture integration:** `specfy_flat.json` produces correct `ProjectProfile` with accurate path, languages, technologies, and dependencies

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write normalizer test suite | 645c1f5 | tests/test_normalizer.py |

## Verification Results

- `uv run pytest tests/test_normalizer.py -v` — 18 passed, 0 failed
- `uv run pytest tests/ -v` — 42 passed, 0 failed (no regressions)

## Deviations from Plan

**1. [Rule 1 - Bug] Fixed fixture test assertion for javascript tech category**
- **Found during:** Task 1 (first test run)
- **Issue:** Test assumed "javascript" → "runtime" but `_TECH_CATEGORIES` in normalizer does not include "javascript" (only "node.js"/"nodejs"), so it correctly maps to "other"
- **Fix:** Updated assertion to `tech_map["javascript"] == "other"` — matches actual normalizer behavior, which is correct per D-08 (unknown techs → "other")
- **Files modified:** tests/test_normalizer.py
- **Commit:** 645c1f5 (same commit, fixed before committing)

## Known Stubs

None. This plan is a test suite only — no production code stubs introduced.

## Threat Flags

No new security surface introduced. Tests use controlled fixture data only (T-03-05 accepted per plan's threat model).

## Self-Check: PASSED

- `tests/test_normalizer.py` — FOUND
- Commit 645c1f5 — FOUND
- 18 tests passing — VERIFIED
- 42 total tests passing (no regressions) — VERIFIED
