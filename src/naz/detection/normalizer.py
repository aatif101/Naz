"""Normalizer -- transforms raw Specfy dict into a typed ProjectProfile."""

from __future__ import annotations

from naz.detection.exceptions import SpecfyError
from naz.models import Dependency, ProjectProfile, Technology

# ---------------------------------------------------------------------------
# AI/LLM package detection (D-01, D-02, D-03)
# Matching is by exact name OR by prefix (e.g. "langchain" matches
# "langchain-openai", "langchain-community", etc.).
# ---------------------------------------------------------------------------
_AI_PREFIXES: tuple[str, ...] = (
    # LLM providers
    "openai",
    "anthropic",
    "google-generativeai",
    "cohere",
    "mistralai",
    "together",
    # Agent frameworks
    "langchain",
    "langgraph",
    "crewai",
    "autogen",
    "agentops",
    # RAG / vector stores
    "llamaindex",
    "llama-index",
    "chromadb",
    "pinecone-client",
    "weaviate-client",
    "qdrant-client",
    "faiss-cpu",
    # Local inference / HuggingFace
    "transformers",
    "huggingface-hub",
    "sentence-transformers",
    "diffusers",
    "ollama",
    # Orchestration / tooling
    "dspy-ai",
    "instructor",
    "haystack-ai",
    "outlines",
    # Memory / composition
    "mem0ai",
    "composio",
)


def _is_ai_package(name: str) -> bool:
    """Return True if package name matches any AI prefix (per D-02)."""
    lower = name.lower()
    return any(lower == prefix or lower.startswith(prefix + "-") for prefix in _AI_PREFIXES)


# ---------------------------------------------------------------------------
# Tech categorization (D-06, D-07, D-08)
# ---------------------------------------------------------------------------
_TECH_CATEGORIES: dict[str, str] = {
    # Runtime
    "python": "runtime",
    "node.js": "runtime",
    "nodejs": "runtime",
    "ruby": "runtime",
    "java": "runtime",
    "go": "runtime",
    "rust": "runtime",
    "php": "runtime",
    "elixir": "runtime",
    "scala": "runtime",
    "kotlin": "runtime",
    "swift": "runtime",
    "r": "runtime",
    # Frameworks
    "django": "framework",
    "flask": "framework",
    "fastapi": "framework",
    "express": "framework",
    "next.js": "framework",
    "nextjs": "framework",
    "react": "framework",
    "vue": "framework",
    "angular": "framework",
    "svelte": "framework",
    "nuxt": "framework",
    "rails": "framework",
    "spring": "framework",
    "laravel": "framework",
    "gin": "framework",
    "echo": "framework",
    "fiber": "framework",
    # Database
    "postgresql": "database",
    "postgres": "database",
    "mysql": "database",
    "sqlite": "database",
    "mongodb": "database",
    "redis": "database",
    "elasticsearch": "database",
    "cassandra": "database",
    "dynamodb": "database",
    "cockroachdb": "database",
    "supabase": "database",
    "prisma": "database",
    "sqlalchemy": "database",
    # Infrastructure
    "docker": "infrastructure",
    "kubernetes": "infrastructure",
    "terraform": "infrastructure",
    "ansible": "infrastructure",
    "nginx": "infrastructure",
    "apache": "infrastructure",
    "github actions": "infrastructure",
    "gitlab ci": "infrastructure",
    "circleci": "infrastructure",
    # Dev tools
    "webpack": "devtools",
    "vite": "devtools",
    "esbuild": "devtools",
    "eslint": "devtools",
    "prettier": "devtools",
    "jest": "devtools",
    "pytest": "devtools",
    "ruff": "devtools",
    "typescript": "devtools",
    "babel": "devtools",
    "poetry": "devtools",
    "uv": "devtools",
    "pip": "devtools",
    "npm": "devtools",
    "yarn": "devtools",
    "pnpm": "devtools",
    # AI/ML
    "pytorch": "ai_ml",
    "tensorflow": "ai_ml",
    "scikit-learn": "ai_ml",
    "keras": "ai_ml",
    "jax": "ai_ml",
    "xgboost": "ai_ml",
    "lightgbm": "ai_ml",
    "numpy": "ai_ml",
    "pandas": "ai_ml",
    "jupyter": "ai_ml",
}


def _categorize_tech(name: str) -> str:
    """Map a tech name to a category string (per D-06, D-08)."""
    return _TECH_CATEGORIES.get(name.lower(), "other")


# ---------------------------------------------------------------------------
# Public API (D-10)
# ---------------------------------------------------------------------------


def normalize(raw: dict) -> ProjectProfile:
    """Transform raw Specfy flat dict into a validated ProjectProfile.

    Args:
        raw: Dict returned by run_specfy(). Any field may be absent or null.

    Returns:
        Validated ProjectProfile.

    Raises:
        SpecfyError: If raw is not a dict.
    """
    if not isinstance(raw, dict):
        raise SpecfyError("Specfy output must be a dict")

    # path: use Specfy's path list joined, or empty string if absent (D-12)
    path_list: list[str] = raw.get("path") or []
    path = "/".join(str(p) for p in path_list).strip("/") or "."

    # languages: pass through directly -- already dict[str, int] (D-12)
    languages: dict[str, int] = raw.get("languages") or {}

    # techs -> Technology list with categories (D-05, D-06, D-07, D-08)
    techs_raw: list[str] = raw.get("techs") or []
    technologies = [
        Technology(name=t, category=_categorize_tech(t))
        for t in techs_raw
        if isinstance(t, str) and t.strip()
    ]

    # dependencies: split into regular + ai (D-03, D-04, D-13)
    deps_raw: list[list] = raw.get("dependencies") or []
    dependencies: list[Dependency] = []
    ai_dependencies: list[Dependency] = []

    for entry in deps_raw:
        if not isinstance(entry, (list, tuple)) or len(entry) < 2:
            continue  # lenient -- skip malformed entries (D-12)
        manager = str(entry[0])
        name = str(entry[1])
        version = str(entry[2]) if len(entry) > 2 and entry[2] is not None else None

        dep = Dependency(manager=manager, name=name, version=version)
        if _is_ai_package(name):
            ai_dependencies.append(dep)
        else:
            dependencies.append(dep)

    # components: list of component names from Specfy (D-12)
    components_raw = raw.get("childs") or []
    components = [str(c) for c in components_raw if c]

    # Pydantic is the final validation gate (D-14)
    return ProjectProfile(
        path=path,
        technologies=technologies,
        languages=languages,
        dependencies=dependencies,
        ai_dependencies=ai_dependencies,
        components=components,
        raw=raw,
    )
