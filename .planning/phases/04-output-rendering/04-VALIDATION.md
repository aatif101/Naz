---
phase: 4
slug: output-rendering
status: ready
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-10
updated: 2026-04-10
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml (`[tool.pytest.ini_options]`) |
| **Quick run command** | `uv run pytest tests/test_renderer.py tests/test_cli_scan.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~3 seconds |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/test_renderer.py tests/test_cli_scan.py -x`
- **After every plan wave:** `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-T1 | 01 | 1 | OUT-01 | T-04-01, T-04-02, T-04-03 | rich.markup.escape() applied to all Specfy-derived strings | unit (TDD RED) | `uv run pytest tests/test_renderer.py -x` | ❌ W0 | ⬜ pending |
| 04-01-T2 | 01 | 1 | OUT-01 | T-04-01, T-04-02, T-04-03 | _console = Console() (stdout, no stderr=True); escape applied | unit (TDD GREEN) | `uv run python -c "from naz.renderer import render; print('ok')"` | ❌ W0 | ⬜ pending |
| 04-02-T1 | 02 | 2 | OUT-01, OUT-02 | T-04-06, T-04-08 | --json flag is bool; render() not called when json=True | integration | `uv run pytest tests/test_cli_scan.py -x` | ✅ (update) | ⬜ pending |
| 04-02-T2 | 02 | 2 | OUT-01, OUT-02 | T-04-06 | raw field excluded from JSON; json.loads() succeeds | integration | `uv run pytest tests/test_cli_scan.py tests/test_renderer.py -v` | ✅ (update) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/fixtures/specfy_ai.json` — AI-dependency fixture for test_render_ai_panel_when_present (Plan 01 Task 1 creates this)
- [ ] `tests/test_renderer.py` — 8 tests for OUT-01 panel rendering; must exist (and be RED) before renderer.py is written

*Note: pytest framework and CliRunner are already installed (dev dependencies in pyproject.toml). No framework install needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AI / LLM panel uses yellow border in a real terminal | OUT-01 | Color rendering requires a real TTY; CliRunner strips ANSI codes | Run `naz scan .` in a repo that has openai in dependencies; confirm yellow border visually |
| Rich output degrades gracefully when piped | OUT-01 | Pipe suppresses ANSI; verify plain text is still readable | Run `naz scan . \| cat` and confirm panels are readable plain text with no garbage escape codes |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity: every task has an automated verify — no 3 consecutive tasks without one
- [x] Wave 0 covers all MISSING references (specfy_ai.json and test_renderer.py are created in Plan 01 Task 1)
- [x] No watch-mode flags in any verify command
- [x] Feedback latency < 5s for quick run
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** ready for execution 2026-04-10
