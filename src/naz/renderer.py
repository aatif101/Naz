"""Naz renderer -- formats a ProjectProfile as Rich terminal panels."""

from __future__ import annotations

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from naz.models import ProjectProfile

# stdout Console -- auto-detects TTY, strips ANSI when piped (D-12, D-13)
# IMPORTANT: do NOT use Console(stderr=True) here -- that is cli.py's error console
_console = Console()


def render(profile: ProjectProfile) -> None:
    """Render a ProjectProfile to the terminal as Rich panels.

    Section order (D-02): Header -> Languages -> Technologies -> Dependencies -> AI/LLM
    AI/LLM panel is omitted entirely when ai_dependencies is empty (D-07).
    Output goes to stdout so it can be piped and redirected (D-12).
    """
    # Header (D-03) -- escape path to prevent Rich markup injection (T-04-01)
    _console.print(f"\n[bold]Scan complete:[/bold] {escape(profile.path)}\n")

    # Languages (D-04)
    _render_languages(profile)

    # Technologies (D-05)
    _render_technologies(profile)

    # Dependencies (D-06)
    _render_dependencies(profile)

    # AI/LLM -- omit entirely if empty (D-07)
    if profile.ai_dependencies:
        _render_ai(profile)


def _render_languages(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Language")
    table.add_column("Lines", justify="right")
    if profile.languages:
        for lang, count in profile.languages.items():
            # escape language names from Specfy to prevent markup injection (T-04-02)
            table.add_row(escape(lang), str(count))
    else:
        table.add_row("[dim]None detected[/dim]", "")
    _console.print(Panel(table, title="Languages", border_style="blue"))


def _render_technologies(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Category")
    table.add_column("Technology")
    if profile.technologies:
        for tech in profile.technologies:
            # escape tech names and categories from Specfy (T-04-03)
            table.add_row(escape(tech.category), escape(tech.name))
    else:
        table.add_row("[dim]None detected[/dim]", "")
    _console.print(Panel(table, title="Technologies", border_style="blue"))


def _render_dependencies(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold")
    table.add_column("Manager")
    table.add_column("Package")
    table.add_column("Version")
    if profile.dependencies:
        for dep in profile.dependencies:
            # escape all Specfy-derived strings to prevent markup injection (T-04-02)
            table.add_row(
                escape(dep.manager),
                escape(dep.name),
                escape(dep.version) if dep.version else "\u2014",
            )
    else:
        table.add_row("[dim]None detected[/dim]", "", "")
    count = len(profile.dependencies)
    _console.print(Panel(table, title=f"Dependencies ({count})", border_style="blue"))


def _render_ai(profile: ProjectProfile) -> None:
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Manager")
    table.add_column("Package")
    table.add_column("Version")
    for dep in profile.ai_dependencies:
        # escape all Specfy-derived strings to prevent markup injection (T-04-02)
        table.add_row(
            escape(dep.manager),
            escape(dep.name),
            escape(dep.version) if dep.version else "\u2014",
        )
    count = len(profile.ai_dependencies)
    _console.print(Panel(
        table,
        title=f"[bold magenta]AI / LLM Components ({count})[/bold magenta]",
        border_style="yellow",
    ))
