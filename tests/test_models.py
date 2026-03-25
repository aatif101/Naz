"""Tests for Naz data models."""

from naz.models import Dependency, ProjectProfile, Technology


def test_project_profile_minimal():
    """ProjectProfile can be created with just a path."""
    profile = ProjectProfile(path="/some/repo")
    assert profile.path == "/some/repo"
    assert profile.technologies == []
    assert profile.languages == {}
    assert profile.dependencies == []
    assert profile.ai_dependencies == []
    assert profile.components == []


def test_project_profile_full():
    """ProjectProfile with full data serializes to JSON."""
    profile = ProjectProfile(
        path="/repo",
        technologies=[Technology(name="python", category="language")],
        languages={"python": 42},
        dependencies=[Dependency(manager="pip", name="fastapi", version="0.115.0")],
        ai_dependencies=[Dependency(manager="pip", name="openai", version="1.0.0")],
        components=["backend"],
    )
    json_str = profile.model_dump_json()
    assert '"python"' in json_str
    assert '"fastapi"' in json_str


def test_project_profile_json_roundtrip():
    """JSON serialization roundtrip preserves data."""
    profile = ProjectProfile(
        path="/repo",
        technologies=[Technology(name="react", category="framework")],
        dependencies=[Dependency(manager="npm", name="react", version="18.0.0")],
    )
    json_str = profile.model_dump_json()
    restored = ProjectProfile.model_validate_json(json_str)
    assert restored == profile


def test_technology_model():
    """Technology requires name and category."""
    tech = Technology(name="python", category="language")
    assert tech.name == "python"
    assert tech.category == "language"


def test_dependency_version_optional():
    """Dependency.version defaults to None."""
    dep = Dependency(manager="pip", name="requests")
    assert dep.version is None


def test_raw_excluded_from_json():
    """raw field is excluded from JSON serialization."""
    profile = ProjectProfile(path="/repo", raw={"specfy": "data"})
    json_str = profile.model_dump_json()
    assert "specfy" not in json_str
    assert profile.raw == {"specfy": "data"}


def test_ai_dependencies_separate():
    """ai_dependencies is independent from dependencies."""
    profile = ProjectProfile(
        path="/repo",
        dependencies=[Dependency(manager="pip", name="flask")],
        ai_dependencies=[Dependency(manager="pip", name="openai")],
    )
    assert len(profile.dependencies) == 1
    assert len(profile.ai_dependencies) == 1
    assert profile.dependencies[0].name == "flask"
    assert profile.ai_dependencies[0].name == "openai"
