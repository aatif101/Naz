# Feature Research

**Domain:** CLI security tool -- project detection/profiling layer
**Researched:** 2026-03-25
**Confidence:** HIGH

## Feature Landscape

This research focuses specifically on Layer 1 (detection/profiling) -- the subsystem that identifies what technologies a repository uses before any security scanning begins. This is the foundation layer. Every feature of the scanning and reporting layers depends on detection accuracy.

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Manifest file detection** | Every security tool (Snyk, Trivy, Semgrep) auto-detects package.json, requirements.txt, go.mod, etc. Users expect zero configuration. | LOW | Specfy handles this natively across 700+ techs. Core mechanic is walking the filesystem for known filenames. |
| **Language identification** | Users expect the tool to know what languages are in the repo without being told. Trivy, Snyk, CodeQL all do this automatically. | LOW | Specfy detects languages from file extensions, manifests, and config files. Output includes language counts. |
| **Dependency extraction with versions** | SCA tools (Snyk, Trivy, OWASP Dependency-Check) all parse lockfiles to get exact dependency versions. Without versions, vulnerability matching is impossible. | MEDIUM | Specfy outputs `[package_manager, name, version]` tuples. Critical that lockfiles are preferred over manifests (lockfiles have pinned versions). |
| **Framework detection** | Knowing "this is a React app" or "this uses FastAPI" determines which security rules apply. Snyk and Specfy both do this. | LOW | Specfy detects frameworks from dependencies and config files (e.g., next.config.js = Next.js). |
| **Recursive directory walking** | Repos have nested structures. Snyk uses `--all-projects` with configurable `--detection-depth`. Trivy walks the full tree. Users expect all subdirectories scanned. | LOW | Specfy walks directories recursively and builds a component tree with parent/child relationships. |
| **Multi-language support** | Real projects use multiple languages (Python backend + JS frontend). Every major scanner handles polyglot repos. | LOW | Specfy handles this natively. Output includes per-component language breakdowns. |
| **Clean terminal output of results** | Users want to see what was detected in a readable format, not raw JSON. Every CLI tool has formatted output. | LOW | Already planned via Rich. Show languages, frameworks, dependency counts, and services detected. |
| **Structured machine-readable output** | CI/CD integration and downstream tool consumption require JSON output. Snyk outputs JSON, Trivy outputs JSON/SARIF. | LOW | Specfy outputs JSON natively. Naz wraps this into its own internal profile format. |
| **Error handling for missing runtimes** | If Node.js is not installed (required for Specfy/npx), the tool must fail with a clear, actionable error, not a cryptic stack trace. | LOW | Check for `node` and `npx` on PATH before invoking. Show install instructions on failure. |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **AI/LLM dependency highlighting** | No existing general security scanner flags AI-specific dependencies (openai, langchain, anthropic, transformers, llamaindex). Naz's core differentiator is treating AI deps as first-class security concerns. | MEDIUM | Maintain a curated list of AI/ML package names across ecosystems. Match against extracted dependencies. Flag with specific risk categories (API key exposure, prompt injection surface, agent config risks). |
| **AI-agent-optimized profile format** | Detection output designed to be consumed by AI coding agents (Claude, Cursor). No other tool does this. The profile should be self-describing enough that an AI agent can reason about what security scans to suggest. | MEDIUM | JSON schema with clear field names, descriptions of what each technology means for security. Markdown summary designed for copy-paste into AI chat. |
| **Infrastructure and service detection** | Beyond just code dependencies, detect Docker, Terraform, cloud providers, CI/CD configs, databases. Specfy does this but most security scanners focus only on package manifests. Knowing the full stack (not just code deps) enables infrastructure security scanning later. | LOW | Specfy already detects Docker, Terraform, GCP, AWS, Vercel, GitHub Actions, PostgreSQL, Redis, etc. Naz just needs to surface this clearly in the profile. |
| **Component relationship mapping** | Specfy outputs edges between components (e.g., "frontend calls backend", "backend uses database"). This structural information is unique and valuable for understanding attack surfaces. | MEDIUM | Specfy provides `edges` in output. Naz should preserve and expose these relationships. Useful for later scanning phases to understand data flow. |
| **Technology categorization** | Group detected technologies into meaningful security-relevant categories: "runtime dependencies" vs "dev tools" vs "infrastructure" vs "services" vs "AI/ML components". Most scanners dump a flat list. | LOW | Parse Specfy output into categories. Use dependency metadata (devDependencies vs dependencies) plus Specfy's tech categorization. |
| **Detection confidence scores** | Report how confident the detection is. Did we find a lockfile (high confidence) or just a config file reference (lower confidence)? Helps users and AI agents prioritize. | MEDIUM | Specfy provides some evidence metadata. Enhance with heuristics: lockfile present = high confidence, only manifest = medium, only file extension = low. |
| **Project type classification** | Beyond individual techs, classify the overall project: "Full-stack web app", "API service", "CLI tool", "ML pipeline", "Static site". This drives which scan profiles to apply. | MEDIUM | Derive from combination of detected frameworks, languages, and infrastructure. Rule-based classification using detected tech combinations. |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Source code AST parsing for detection** | "Parse the actual code to find imports and usage patterns for more accurate detection" | Massively increases complexity, runtime, and memory usage. Specfy deliberately avoids this for speed. AST parsing is the job of the *scanning* layer (Semgrep), not the *detection* layer. Mixing concerns leads to a slow, fragile detection phase. | Rely on manifest/config file detection (Specfy's approach). Source code analysis belongs in Layer 2 scanning. |
| **Auto-install missing tools** | "If Node.js is missing, install it automatically" | Installing system-level software without explicit consent is hostile. Package manager conflicts, permission issues, version conflicts. Security tool silently installing software is ironic. | Detect missing tools, print clear install instructions with exact commands for the user's OS. Link to official install pages. |
| **Real-time file watching** | "Watch for file changes and re-detect automatically" | Detection is a point-in-time operation that feeds into scanning. File watching adds complexity (debouncing, partial states) with no clear benefit for a CLI scan tool. This is IDE plugin territory. | Run `naz scan .` again. It should be fast enough that re-running is trivial. |
| **Remote repository scanning** | "Scan a GitHub URL without cloning" | Requires GitHub API auth, rate limiting, incomplete file access (can't read all manifests via API), and network dependency. Adds massive complexity for a v1 tool. | User clones the repo locally first, then runs `naz scan .`. Add a note in docs. |
| **Custom detection rules** | "Let users define their own technology detection patterns" | Premature abstraction. The 700+ rules in Specfy cover virtually all real-world cases. Custom rules add config complexity, documentation burden, and testing surface. No solo dev needs this. | If Specfy misses something, contribute upstream or handle it in the AI dependency list (which IS user-extensible). |
| **Version range resolution** | "Resolve semver ranges to exact versions by querying registries" | Requires network calls to npm/PyPI/etc., adds latency, requires auth for private registries, and fails offline. Lockfiles already have exact versions. | Use lockfile versions when available. Show manifest ranges only when no lockfile exists. Flag "no lockfile found" as a warning. |
| **Build the project to detect dependencies** | "Run npm install or pip install to get the full dependency tree" | Executing arbitrary build commands in an untrusted repo is a security nightmare for a security tool. Build systems are complex, fragile, and slow. | Parse lockfiles and manifests statically. Missing lockfile = warning, not a build trigger. |

## Feature Dependencies

```
[Manifest File Detection]
    +-- requires --> [Recursive Directory Walking]
    +-- requires --> [Multi-Language Support]

[Dependency Extraction with Versions]
    +-- requires --> [Manifest File Detection]

[Framework Detection]
    +-- requires --> [Manifest File Detection]

[AI/LLM Dependency Highlighting]
    +-- requires --> [Dependency Extraction with Versions]

[Technology Categorization]
    +-- requires --> [Framework Detection]
    +-- requires --> [Infrastructure and Service Detection]
    +-- requires --> [AI/LLM Dependency Highlighting]

[Project Type Classification]
    +-- requires --> [Technology Categorization]

[AI-Agent-Optimized Profile Format]
    +-- requires --> [Technology Categorization]
    +-- enhances --> [Project Type Classification]

[Component Relationship Mapping]
    +-- requires --> [Recursive Directory Walking]
    +-- enhances --> [Project Type Classification]

[Detection Confidence Scores]
    +-- enhances --> [Dependency Extraction with Versions]
    +-- enhances --> [AI-Agent-Optimized Profile Format]

[Clean Terminal Output]
    +-- requires --> [Technology Categorization]

[Structured Machine-Readable Output]
    +-- requires --> [Technology Categorization]
```

### Dependency Notes

- **AI/LLM Dependency Highlighting requires Dependency Extraction:** You need the full dependency list with names before you can match against the AI package list.
- **Technology Categorization requires multiple detectors:** It synthesizes language, framework, infrastructure, and AI detection into grouped categories.
- **Project Type Classification requires Technology Categorization:** Classification rules operate on categorized tech, not raw detection output.
- **AI-Agent-Optimized Profile Format requires Technology Categorization:** The profile is a structured view of categorized results, not raw Specfy JSON.
- **Detection Confidence Scores enhance multiple features:** Confidence metadata enriches both dependency data and the AI-facing profile.

## MVP Definition

### Launch With (v0.1 -- current milestone)

Minimum viable detection layer -- what is needed before any scanning can begin.

- [x] **Manifest file detection via Specfy** -- the entire detection engine; without this, nothing works
- [x] **Node.js runtime check** -- Specfy requires Node.js; fail clearly if missing
- [x] **Specfy JSON parsing into internal profile** -- raw Specfy output must be normalized into Naz's schema
- [x] **Language identification** -- included in Specfy output, must be surfaced
- [x] **Framework detection** -- included in Specfy output, must be surfaced
- [x] **Dependency extraction with versions** -- included in Specfy output, must be surfaced
- [x] **Infrastructure and service detection** -- included in Specfy output, must be surfaced
- [x] **AI/LLM dependency highlighting** -- core differentiator; match deps against curated AI package list
- [x] **Clean terminal output via Rich** -- show what was detected in a human-readable summary
- [x] **Structured JSON output** -- the internal profile format, ready for Layer 2 consumption

### Add After Validation (v0.2-v0.x)

Features to add once core detection is working and scanning layer is being built.

- [ ] **Technology categorization** -- group techs into security-relevant categories (runtime vs dev vs infra vs AI)
- [ ] **Project type classification** -- derive overall project type from detected tech combinations
- [ ] **Component relationship mapping** -- expose Specfy's edge data for attack surface understanding
- [ ] **Detection confidence scores** -- lockfile vs manifest vs file extension confidence levels
- [ ] **AI-agent-optimized profile format** -- enhance JSON/markdown output specifically for AI agent consumption

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Profile caching** -- cache detection results, invalidate on file changes (useful when scans take longer)
- [ ] **SBOM generation** -- output CycloneDX or SPDX format from detection results
- [ ] **Workspace/monorepo intelligence** -- understand npm/yarn/pnpm workspaces, Gradle multi-module, etc.
- [ ] **Fallback detection for non-Specfy ecosystems** -- handle edge cases Specfy misses (e.g., Zig, Clojure fully)
- [ ] **Detection diff** -- compare current detection against previous run, show what changed

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Manifest file detection (Specfy) | HIGH | LOW (delegate to Specfy) | P1 |
| Node.js runtime check | HIGH | LOW | P1 |
| Specfy JSON parsing to internal profile | HIGH | MEDIUM | P1 |
| Language identification | HIGH | LOW (from Specfy) | P1 |
| Framework detection | HIGH | LOW (from Specfy) | P1 |
| Dependency extraction with versions | HIGH | LOW (from Specfy) | P1 |
| Infrastructure/service detection | MEDIUM | LOW (from Specfy) | P1 |
| AI/LLM dependency highlighting | HIGH | LOW (curated list matching) | P1 |
| Clean terminal output (Rich) | HIGH | MEDIUM | P1 |
| Structured JSON output | HIGH | MEDIUM | P1 |
| Technology categorization | MEDIUM | LOW | P2 |
| Project type classification | MEDIUM | MEDIUM | P2 |
| Component relationship mapping | LOW | LOW (from Specfy) | P2 |
| Detection confidence scores | MEDIUM | MEDIUM | P2 |
| AI-agent-optimized profile format | HIGH | MEDIUM | P2 |
| Profile caching | LOW | MEDIUM | P3 |
| SBOM generation | LOW | HIGH | P3 |
| Monorepo intelligence | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch (v0.1)
- P2: Should have, add when scanning layer is built
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Snyk CLI | Trivy | Semgrep | Specfy (raw) | Naz (planned) |
|---------|----------|-------|---------|---------------|---------------|
| Language detection | Auto from manifests | Auto from manifests/lockfiles | Configured per language | Auto from files + manifests | Auto via Specfy |
| Dependency extraction | Full dep graph from lockfiles | Lockfile parsing | Not primary focus | Name + version tuples | Via Specfy + internal profile |
| Framework detection | Limited (knows package managers) | Not a focus | Rule-based patterns | 700+ tech rules | Via Specfy, categorized |
| Infrastructure detection | IaC scanning (Terraform, K8s) | IaC misconfiguration scanning | IaC rules available | Docker, Terraform, cloud providers | Via Specfy, surfaced clearly |
| AI dependency flagging | No special handling | No special handling | Custom rules possible | No special handling | Curated AI package list -- **unique** |
| Monorepo support | `--all-projects` + `--detection-depth` | Recursive scan | Per-language config | Component tree with edges | Via Specfy tree |
| Output format | JSON, SARIF | JSON, SARIF, table, CycloneDX | JSON, SARIF, text | JSON (custom schema) | JSON + Markdown (AI-optimized) |
| AI-agent-friendly output | No | No | No | No | **Core differentiator** |
| Zero-config detection | Yes (auto-detect) | Yes (auto-detect) | Requires language config | Yes (auto-detect) | Yes (auto-detect via Specfy) |

### Key Competitive Insight

Snyk and Trivy treat detection as an invisible prerequisite to scanning -- it happens automatically but is not exposed as a user-facing feature. Naz makes detection a **visible, valuable first step** because:
1. Solo devs often do not know their full stack (especially vibe-coded projects)
2. The detection profile itself is useful for AI agents even before scanning
3. AI dependency highlighting is a unique lens no competitor offers

## Sources

- [Snyk CLI Package Manager and Project Detection](https://deepwiki.com/snyk/cli/5-package-manager-and-project-detection) -- detailed detection flow and manifest priority
- [Specfy stack-analyser GitHub](https://github.com/specfy/stack-analyser) -- detection capabilities, output format, supported languages
- [Trivy Filesystem Scanning](https://trivy.dev/docs/latest/guide/target/filesystem/) -- how Trivy detects project types from lockfiles
- [Trivy Language Coverage](https://trivy.dev/docs/latest/coverage/language/) -- supported ecosystems
- [GitLab Dependency Scanning Docs](https://docs.gitlab.com/user/application_security/dependency_scanning/) -- detection phase and SBOM generation
- [Promptfoo Code Scanning](https://www.promptfoo.dev/code-scanning/github-action/) -- AI-specific security scanning
- [Snyk vs Trivy Comparison 2026](https://www.aikido.dev/blog/snyk-vs-trivy) -- feature comparison
- [AI Code Security Tools Comparison](https://sanj.dev/post/ai-code-security-tools-comparison) -- Snyk vs Semgrep vs CodeQL
- [LLM Security Tools Overview](https://www.lakera.ai/blog/llm-security-tools) -- AI-specific security landscape
- [Open-Source AI/LLM Security Tools Guide](https://slashllm.com/resources/ai-security-tools-guide) -- comprehensive AI security tooling

---
*Feature research for: CLI security tool -- project detection/profiling layer*
*Researched: 2026-03-25*
