# Naz

## What This Is

Naz is a CLI security tool for solo developers. One command (`naz scan .`) scans a repository, detects its full technology stack, runs the right security tools, and outputs a structured report designed to be fed directly into AI coding agents (Claude, Cursor, etc.) to fix issues. Dual output: human-readable markdown + machine-readable JSON. The pitch: "You build the app, we handle the security."

## Core Value

A solo dev can run one command and get a clear, actionable security report that an AI agent can immediately act on — no security expertise required.

## Requirements

### Validated

- [x] Installable Python package with src layout and hatchling build backend — Validated in Phase 1: Project Foundation
- [x] `naz` CLI entry point registered via pyproject.toml and prints help — Validated in Phase 1: Project Foundation
- [x] Central ProjectProfile Pydantic model can be instantiated and serialized to JSON — Validated in Phase 1: Project Foundation

### Active

- [ ] `naz scan .` detects the full technology stack of a repository via Specfy stack-analyser
- [ ] Node.js dependency is checked before running Specfy; clear error if missing
- [ ] Specfy JSON output is parsed into Naz's internal project profile format
- [ ] Project profile includes: languages, frameworks, dependencies (with versions), infrastructure, services, detected technologies
- [ ] Clean terminal summary printed via Rich showing what was detected
- [ ] AI/LLM dependencies are specifically highlighted in the summary (openai, langchain, etc.)

### Out of Scope

- Security scanning (Layer 2) — building detection first, scanning comes after
- AI-specific detector (Part B) — Specfy integration must work first
- Report generation (Layer 3) — no scanning means no report yet
- PyPI publishing — not until the tool actually does something useful
- Secondary/fallback detection engines — Specfy is the only general detection engine
- Web UI or dashboard — CLI only

## Context

The target user is a solo dev or indie builder who vibe-coded an app and wants to secure it before shipping. They don't want to learn 6 different security tools. Naz combines general security scanning (secrets, dependencies, code patterns) with AI-specific security scanning (prompt injection risks, exposed LLM API keys, insecure agent configs, MCP server vulnerabilities). No other free CLI tool does both.

The long-term vision is "a standardized security test for vibe-coded apps" — something every AI-assisted project runs before shipping. The report is specifically designed so AI coding agents can action the fixes directly.

This milestone (v0.1) focuses solely on Layer 1, Part A: integrating Specfy's stack-analyser to detect what technologies a repo uses. No scanning, no reporting — just detection.

## Constraints

- **Language**: Python — user knows it well, it's the right fit for a CLI tool
- **CLI framework**: Typer — chosen, non-negotiable
- **Terminal output**: Rich — chosen, non-negotiable
- **Detection engine**: Specfy stack-analyser via npx subprocess — not ported to Python
- **Runtime dependency**: Node.js required on user's machine (for npx)
- **Code style**: Simple and readable — no over-abstraction, no clever patterns

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + Typer + Rich for CLI | User knows Python well, Typer/Rich are standard for modern Python CLIs | — Pending |
| Specfy via subprocess (not ported) | Leverage existing 700+ tech detection without rewriting; npx makes it zero-install | — Pending |
| Dual output (markdown + JSON) | Markdown for humans, JSON for CI/CD and tooling integration | — Pending |
| AI-agent-friendly report format | Core differentiator: reports designed to be copy-pasted into AI coding agents | — Pending |
| Node.js as required dependency | Specfy runs via npx; acceptable tradeoff for 700+ tech detection | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-25 after Phase 1 completion*
