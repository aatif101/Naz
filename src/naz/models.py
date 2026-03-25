"""Naz data models - central types that detection produces and output consumes."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Dependency(BaseModel):
    """A single package dependency."""

    manager: str
    name: str
    version: str | None = None


class Technology(BaseModel):
    """A detected technology."""

    name: str
    category: str


class ProjectProfile(BaseModel):
    """Central data model: detection produces it, output consumes it."""

    path: str
    technologies: list[Technology] = Field(default_factory=list)
    languages: dict[str, int] = Field(default_factory=dict)
    dependencies: list[Dependency] = Field(default_factory=list)
    ai_dependencies: list[Dependency] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    raw: dict = Field(default_factory=dict, exclude=True)
