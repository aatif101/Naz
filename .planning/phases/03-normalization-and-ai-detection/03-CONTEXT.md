# Phase 3: Normalization and AI Detection - Context

**Gathered:** 2026-04-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Transform raw Specfy dict → typed, categorized `ProjectProfile`. This phase owns the normalizer only — no terminal output (Phase 4), no CLI wiring (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### AI Package Detection
- **D-01:** AI detection is hardcoded name matching only — no LLM, no network calls, no version matching
- **D-02:** Match on package name prefix/exact (e.g. `"langchain"` catches `langchain-openai`, `langchain-community`)
- **D-03:** Broad list covering: LLM providers (openai, anthropic, google-generativeai, cohere, mistralai, together), agent frameworks (langchain*, langgraph, crewai, autogen*, agentops), RAG/vector (llamaindex, llama-index*, chromadb, pinecone-client, weaviate-client, qdrant-client, faiss-cpu), local inference (transformers, huggingface-hub, sentence-transformers, diffusers, ollama), orchestration (dspy-ai, instructor, haystack-ai, outlines), memory/tools (mem0ai, composio)
- **D-04:** Version is passthrough from Specfy — we never hardcode or filter on versions
- **D-05:** v0.2 enhancement (deferred): remote-maintained list fetched from GitHub/CDN with local cache fallback

### Tech Categorization
- **D-06:** Hardcoded dict mapping known tech names → categories
- **D-07:** Categories: `runtime`, `framework`, `database`, `infrastructure`, `devtools`, `ai_ml`
- **D-08:** Unknown techs (not in mapping dict) → category `"other"` — no errors, no warnings, no data loss

### Normalizer Location
- **D-09:** `src/naz/detection/normalizer.py` — keeps all detection logic together
- **D-10:** Public function: `normalize(raw: dict) -> ProjectProfile`
- **D-11:** `naz.detection.__init__` re-exports `normalize` alongside `run_specfy`

### Specfy Schema Handling
- **D-12:** Be lenient — if a field is missing or null in Specfy output, default to empty list/dict rather than raising
- **D-13:** Dependencies come in as `[manager, name, version]` tuples; version element may be absent → default to `None`
- **D-14:** Pydantic validation is the final gate — malformed data that passes normalization will fail at `ProjectProfile` instantiation

### Code Style
- **D-15:** Simple and readable — normalizer is one function with clear sections, no class hierarchy, no over-abstraction (per project constraint)

### Claude's Discretion
- Exact tech→category mapping dict entries
- AI package list exact strings and prefix logic
- Test fixture design for edge cases

</decisions>

<canonical_refs>
## Canonical References

- `.planning/PROJECT.md` — Project vision and constraints
- `.planning/REQUIREMENTS.md` — DET-02, DET-03, DET-04, DET-05
- `src/naz/models.py` — Existing `ProjectProfile`, `Technology`, `Dependency` models
- `src/naz/detection/runner.py` — Returns raw dict that normalizer consumes
- `tests/fixtures/specfy_flat.json` — Specfy `--flat` output shape

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ProjectProfile`, `Technology`, `Dependency` models already defined in `src/naz/models.py` — normalizer produces these directly
- `src/naz/detection/__init__.py` already re-exports from runner — extend to include `normalize`

### Established Patterns
- Simple flat functions (no classes) — matches runner.py style
- `from __future__ import annotations` at top of every module
- Tests use `unittest.mock.patch("subprocess.run")` pattern; normalizer tests will use plain dict fixtures

### Integration Points
- `src/naz/cli.py` scan command currently does `typer.echo(raw)` stub — Phase 3 does NOT touch cli.py (that's Phase 4/5)
- Normalizer output (`ProjectProfile`) is what Phase 4 consumes for rendering

</code_context>

<specifics>
## Specific Ideas

- `normalize()` takes the raw dict from `run_specfy()` and returns a `ProjectProfile`
- AI matching: iterate `raw["dependencies"]`, check if name matches any AI package prefix → route to `ai_dependencies`
- Tech categorization: check `raw["techs"]` list, map each to a `Technology(name=..., category=...)` via lookup dict
- Languages: pass `raw["languages"]` dict through directly (already `dict[str, int]`)

</specifics>

<deferred>
## Deferred Ideas

- **Remote AI package list (v0.2):** Fetch AI package list from a hosted JSON (GitHub/CDN) with local cache fallback — so the list stays fresh without shipping new Naz versions
- **Detection confidence scores (v2 req DET-08):** lockfile=high, manifest=medium, file extension=low

</deferred>

---

*Phase: 03-normalization-and-ai-detection*
*Context gathered: 2026-04-09*
