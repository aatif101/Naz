---
phase: 2
slug: specfy-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/test_detection.py -x -q` |
| **Full suite command** | `uv run pytest -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_detection.py -x -q`
- **After every plan wave:** Run `uv run pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 0 | DET-01 | — | N/A | unit | `uv run pytest tests/test_detection.py -x -q` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DET-01 | — | N/A | unit | `uv run pytest tests/test_detection.py::test_run_specfy_success -x -q` | ✅ | ⬜ pending |
| 02-01-03 | 01 | 1 | DET-06 | — | N/A | unit | `uv run pytest tests/test_detection.py::test_windows_npx_resolution -x -q` | ✅ | ⬜ pending |
| 02-01-04 | 01 | 1 | CLI-02 | — | N/A | unit | `uv run pytest tests/test_detection.py::test_node_not_found_error -x -q` | ✅ | ⬜ pending |
| 02-01-05 | 01 | 2 | DET-01 | — | N/A | integration | `uv run pytest tests/test_detection.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_detection.py` — stubs for DET-01, DET-06, CLI-02
- [ ] `tests/fixtures/specfy_output.json` — sample Specfy output fixture

*Wave 0 must create test file stubs before implementation begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| First-run message appears before npx | DET-01 | Requires live npx execution | Run `naz scan .` in fresh environment, verify "Downloading stack analyser (first run only)..." appears |
| Windows npx.cmd resolves correctly | DET-06 | Requires Windows environment | Run on Windows, confirm result identical to Unix |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
