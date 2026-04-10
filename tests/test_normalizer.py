"""Tests for the normalize() function covering DET-02 through DET-05."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from naz.detection import normalize
from naz.detection.exceptions import SpecfyError
from naz.models import Dependency, ProjectProfile, Technology

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SPECFY_FLAT_FIXTURE = json.loads((FIXTURES_DIR / "specfy_flat.json").read_text())


# ---------------------------------------------------------------------------
# DET-02: ProjectProfile produced from raw dict
# ---------------------------------------------------------------------------


def test_normalize_returns_project_profile():
    result = normalize({"techs": [], "languages": {}, "dependencies": []})
    assert isinstance(result, ProjectProfile)


def test_normalize_empty_dict():
    result = normalize({})
    assert result.path == "."
    assert result.technologies == []
    assert result.languages == {}
    assert result.dependencies == []
    assert result.ai_dependencies == []


# ---------------------------------------------------------------------------
# DET-03: technologies, languages, dependencies with versions
# ---------------------------------------------------------------------------


def test_normalize_languages_passthrough():
    langs = {"Python": 1200, "JavaScript": 300}
    result = normalize({"languages": langs})
    assert result.languages == langs


def test_normalize_dependencies_basic():
    result = normalize({"dependencies": [["pip", "requests", "2.31.0"]]})
    assert len(result.dependencies) == 1
    dep = result.dependencies[0]
    assert dep.manager == "pip"
    assert dep.name == "requests"
    assert dep.version == "2.31.0"
    assert isinstance(dep, Dependency)


def test_normalize_dependency_no_version():
    result = normalize({"dependencies": [["pip", "requests"]]})
    assert len(result.dependencies) == 1
    dep = result.dependencies[0]
    assert dep.manager == "pip"
    assert dep.name == "requests"
    assert dep.version is None


# ---------------------------------------------------------------------------
# DET-04: AI packages route to ai_dependencies; non-AI stay in dependencies
# ---------------------------------------------------------------------------


def test_normalize_ai_exact_match():
    result = normalize({"dependencies": [["pip", "openai", "1.0.0"]]})
    assert len(result.ai_dependencies) == 1
    assert result.ai_dependencies[0].name == "openai"
    assert len(result.dependencies) == 0


def test_normalize_ai_prefix_match():
    result = normalize({"dependencies": [["pip", "langchain-openai", "0.1.0"]]})
    assert len(result.ai_dependencies) == 1
    assert result.ai_dependencies[0].name == "langchain-openai"
    assert len(result.dependencies) == 0


def test_normalize_ai_prefix_no_false_positive():
    # "langchainwrapper" has no hyphen after prefix → should NOT be flagged as AI
    result = normalize({"dependencies": [["pip", "langchainwrapper", "1.0"]]})
    assert len(result.ai_dependencies) == 0
    assert len(result.dependencies) == 1
    assert result.dependencies[0].name == "langchainwrapper"


def test_normalize_non_ai_stays_in_dependencies():
    deps = [
        ["pip", "typer", "0.24.0"],
        ["pip", "flask", "3.0.0"],
        ["pip", "requests", "2.31.0"],
    ]
    result = normalize({"dependencies": deps})
    assert len(result.dependencies) == 3
    assert len(result.ai_dependencies) == 0
    dep_names = {d.name for d in result.dependencies}
    assert dep_names == {"typer", "flask", "requests"}


def test_normalize_ai_comprehensive():
    """All major AI packages route to ai_dependencies (DET-04)."""
    ai_deps = [
        ["pip", "anthropic", "0.25.0"],
        ["pip", "crewai", "0.1.0"],
        ["pip", "chromadb", "0.4.0"],
        ["pip", "transformers", "4.40.0"],
        ["pip", "ollama", "0.1.0"],
        ["pip", "mem0ai", "0.0.1"],
    ]
    result = normalize({"dependencies": ai_deps})
    assert len(result.ai_dependencies) == 6
    assert len(result.dependencies) == 0
    ai_names = {d.name for d in result.ai_dependencies}
    assert ai_names == {"anthropic", "crewai", "chromadb", "transformers", "ollama", "mem0ai"}


# ---------------------------------------------------------------------------
# DET-05: tech categories — runtime, framework, database, infrastructure, devtools, ai_ml, other
# ---------------------------------------------------------------------------


def test_normalize_tech_runtime_category():
    result = normalize({"techs": ["python"]})
    assert len(result.technologies) == 1
    tech = result.technologies[0]
    assert tech.name == "python"
    assert tech.category == "runtime"
    assert isinstance(tech, Technology)


def test_normalize_tech_framework_category():
    result = normalize({"techs": ["django"]})
    assert len(result.technologies) == 1
    tech = result.technologies[0]
    assert tech.name == "django"
    assert tech.category == "framework"


def test_normalize_tech_unknown_is_other():
    result = normalize({"techs": ["unknownthing123"]})
    assert len(result.technologies) == 1
    tech = result.technologies[0]
    assert tech.name == "unknownthing123"
    assert tech.category == "other"


# ---------------------------------------------------------------------------
# Edge cases: null/missing fields, malformed entries (D-12, D-13)
# ---------------------------------------------------------------------------


def test_normalize_null_fields():
    result = normalize({"techs": None, "dependencies": None, "languages": None})
    assert result.technologies == []
    assert result.dependencies == []
    assert result.ai_dependencies == []
    assert result.languages == {}


def test_normalize_missing_fields():
    result = normalize({"id": "abc123", "name": "test"})
    assert result.technologies == []
    assert result.dependencies == []
    assert result.ai_dependencies == []
    assert result.languages == {}


def test_normalize_non_dict_raises():
    with pytest.raises(SpecfyError):
        normalize("not a dict")  # type: ignore[arg-type]


def test_normalize_malformed_dep_skipped():
    # Single-element dep entry should be skipped without exception
    result = normalize({"dependencies": [["pip"], ["pip", "requests", "2.31.0"]]})
    assert len(result.dependencies) == 1
    assert result.dependencies[0].name == "requests"


# ---------------------------------------------------------------------------
# Integration: specfy_flat.json fixture (DET-02, DET-03)
# ---------------------------------------------------------------------------


def test_normalize_specfy_flat_fixture():
    result = normalize(SPECFY_FLAT_FIXTURE)
    assert isinstance(result, ProjectProfile)
    # path from fixture: ["/", ""] → joined and stripped → "."
    assert result.path == "."
    # languages pass through
    assert result.languages == {"Python": 834, "JSON": 5}
    # techs: python → runtime, javascript → other (not in category map)
    assert len(result.technologies) == 2
    tech_names = {t.name for t in result.technologies}
    assert tech_names == {"python", "javascript"}
    tech_map = {t.name: t.category for t in result.technologies}
    assert tech_map["python"] == "runtime"
    assert tech_map["javascript"] == "other"
    # dependencies: typer, pydantic, express — none are AI packages
    assert len(result.dependencies) == 3
    assert len(result.ai_dependencies) == 0
    dep_names = {d.name for d in result.dependencies}
    assert dep_names == {"typer", "pydantic", "express"}
