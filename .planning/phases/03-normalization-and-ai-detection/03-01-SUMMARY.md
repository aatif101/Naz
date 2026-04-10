---
phase: 03-normalization-and-ai-detection
plan: 01
subsystem: detection
tags: [normalizer, pydantic, ai-detection, tech-categorization]
dependency_graph:
  requires: [src/naz/models.py, src/naz/detection/exceptions.py]
  provides: [src/naz/detection/normalizer.py, normalize() function]
  affects: [src/naz/detection/__init__.py]
tech_stack:
  added: []
  patterns: [flat-function, pydantic-validation-gate, prefix-matching]
key_files:
  created:
    - src/naz/detection/normalizer.py
  modified:
    - src/naz/detection/__init__.py
decisions:
  - "AI package detection uses prefix matching (e.g. langchain catches langchain-openai) with trailing-hyphen guard to prevent false positives"
  - "Unknown techs get category 'other' — no exceptions, no data loss"
  - "normalize() is lenient on missing/null Specfy fields; Pydantic is the final validation gate"
metrics:
  duration: "5min"
  completed: "2026-04-09"
  tasks: 2
  files: 2
---

# Phase 03 Plan 01: Normalizer — Specfy Dict to ProjectProfile Summary

**One-liner:** Pydantic-validated normalizer that maps raw Specfy subprocess output to a typed ProjectProfile with AI dependency separation and tech categorization.

## What Was Built

`src/naz/detection/normalizer.py` — the boundary between raw subprocess data and the rest of Naz. It exposes a single public function `normalize(raw: dict) -> ProjectProfile` that:

1. Guards against non-dict input (raises `SpecfyError` — T-03-01 threat mitigation)
2. Extracts `path`, `languages`, `techs`, `dependencies`, and `childs` from Specfy's flat output
3. Maps each tech name to a category string via a hardcoded lookup dict (runtime, framework, database, infrastructure, devtools, ai_ml, or "other")
4. Routes dependencies into `ai_dependencies` vs `dependencies` using prefix matching against a 29-entry AI package list
5. Lets Pydantic serve as the final validation gate via `ProjectProfile(...)` construction

`src/naz/detection/__init__.py` — updated to re-export `normalize` alongside `run_specfy` in `__all__`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create normalizer.py with AI detection and tech categorization | 8bd7848 | src/naz/detection/normalizer.py |
| 2 | Re-export normalize in detection __init__.py | 3e77772 | src/naz/detection/__init__.py |

## Verification Results

All plan verification checks passed:
- `from naz.detection import normalize` works
- `normalize({})` returns ProjectProfile with all empty collections and path="."
- `normalize({"techs": ["python"], "dependencies": [["pip", "openai", "1.0"]]})` produces 1 tech (runtime), 0 regular deps, 1 ai_dependency
- `normalize({"dependencies": [["pip", "langchain-openai", "0.1"]]})` routes langchain-openai to ai_dependencies (prefix match)
- `normalize({"techs": ["unknownthing"]})` produces Technology(name="unknownthing", category="other") — no exception

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. `normalize()` is fully wired — it produces a complete `ProjectProfile` from real Specfy output. Phase 4 will consume this output for terminal rendering.

## Threat Flags

No new security surface introduced beyond what was planned in the threat model. All T-03-0x mitigations implemented as specified.

## Self-Check: PASSED

- `src/naz/detection/normalizer.py` — FOUND
- `src/naz/detection/__init__.py` — FOUND (modified)
- Commit 8bd7848 — FOUND
- Commit 3e77772 — FOUND
