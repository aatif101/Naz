# Naz — GSD Context Document

## What is Naz?

Naz is a CLI security tool for solo developers. The pitch: "You build the app, we handle the security." One command (`naz scan .`) scans your project and tells you what's wrong and how to fix it.

Naz is different from existing security tools because it combines general security scanning (secrets, dependencies, code patterns) WITH AI-specific security scanning (prompt injection risks, exposed LLM API keys, insecure agent configs, MCP server vulnerabilities). No other free CLI tool does both.

The target user is a solo dev or indie builder who vibe-coded an app and wants to secure it before shipping, but doesn't want to learn 6 different security tools.

---

## What I need help with right now

I am building **Layer 1: Project Detection** — the part of Naz that looks at a repository and figures out exactly what technologies, frameworks, dependencies, and infrastructure it uses. This information will later be used to decide which security scans to run.

I am starting with **Part A only**: integrating Specfy's stack-analyser.

---

## Part A: Specfy Integration

### What is Specfy stack-analyser?
- GitHub: https://github.com/specfy/stack-analyser
- It's an open-source tool (TypeScript/Node.js) that extracts 700+ technologies from any repository
- It detects languages, SaaS, cloud providers, infrastructure, dependencies, services, and relationships between components
- It outputs structured JSON
- You run it via: `npx @specfy/stack-analyser <PATH>`
- It reads package.json, docker-compose.yml, go.mod, requirements.txt, Terraform configs, Dockerfiles, etc.

### What I need to build

1. **Project setup**: Create a Python CLI project called `naz` using Typer for CLI and Rich for terminal output. Set up proper project structure with pyproject.toml.

2. **Specfy subprocess integration**: 
   - When user runs `naz scan .` or `naz scan /path/to/repo`
   - Naz should first check if Node.js is installed on the user's machine
   - If yes, run `npx @specfy/stack-analyser <path> --output=naz_scan.json` as a subprocess
   - Capture the JSON output
   - Parse it into a Python data structure

3. **Normalize the output**: 
   - Take Specfy's JSON and convert it into Naz's own internal "project profile" format
   - The project profile should contain: detected languages, frameworks, dependencies (with versions), infrastructure (Docker, cloud providers), services (databases, caches), and a list of detected technologies

4. **Print a clean summary**: 
   - Using Rich, print a readable summary of what was detected
   - Something like:
     ```
     Naz — Project Detection
     
     Stack: Python + FastAPI
     Dependencies: 47 packages detected
     Infrastructure: Docker, AWS (via Terraform)
     Services: PostgreSQL, Redis
     AI/LLM: openai, langchain detected
     ```

5. **Test against real repos**: 
   - Test the detection against a few different types of repos to see what Specfy catches and what it misses
   - Specifically interested in whether it catches AI/LLM related dependencies

### Technical decisions already made
- Language: Python
- CLI framework: Typer
- Terminal output: Rich
- Package name: naz
- Specfy is called as a subprocess via npx (NOT ported to Python)
- No secondary fallback detection — Specfy is the primary and only detection engine for general stack analysis
- Node.js is a required dependency (if not installed, show clear error message)

### What comes AFTER this (not building now, just for context)
- **Part B**: I will build my own AI-specific detector on top of Specfy's output (MCP configs, agent frameworks, prompt patterns, etc.)
- **Part C**: Combine Specfy + AI detector into a unified project profile
- **Layer 2**: Based on the project profile, orchestrate the right security tools (Gitleaks, Semgrep, OSV-Scanner, etc.)
- **Layer 3**: Generate a clean, actionable security report

### Project structure I'm expecting
```
naz/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   └── naz/
│       ├── __init__.py
│       ├── cli.py              # Typer CLI entry point
│       ├── detection/
│       │   ├── __init__.py
│       │   ├── specfy.py       # Specfy integration (subprocess + JSON parsing)
│       │   └── profile.py      # Project profile data structure
│       └── utils/
│           ├── __init__.py
│           └── display.py      # Rich display helpers
```

### Important notes
- This is a REAL project that will be published to PyPI. No hardcoded test data, no fake outputs, no placeholders.
- Everything must actually work when run against a real repository.
- I want to understand every piece of code — don't write anything overly clever or abstracted. Keep it simple and readable.
- I am a CS student, I know Python well, I just need help with the structure and getting started.

---

## About GSD setup

This is my first time using GSD (Get Shit Done). I need help:
1. Setting up the project from scratch
2. Understanding how to structure the work
3. Getting the Specfy integration working and tested

Please help me get started step by step. Don't build everything at once — walk me through it piece by piece so I understand what's happening.
