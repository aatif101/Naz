---
phase: 01
slug: project-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `python -m pytest tests/ -q --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PKG-01 | integration | `pip install -e . && python -c "import naz"` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | PKG-02 | integration | `naz --help` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | PKG-01 | unit | `python -m pytest tests/test_models.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — test package init
- [ ] `tests/test_models.py` — stubs for ProjectProfile model validation
- [ ] pytest configured in pyproject.toml

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `naz` prints help message | PKG-02 | CLI entry point depends on install | Run `pip install -e .` then `naz --help` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
