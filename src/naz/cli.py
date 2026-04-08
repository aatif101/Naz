"""Naz CLI - Security scanning for solo developers."""

import typer
from rich.console import Console
from rich.panel import Panel

from naz.detection import (
    NodeNotFoundError,
    SpecfyError,
    SpecfyTimeoutError,
    run_specfy,
)

app = typer.Typer(
    name="naz",
    help="Security scanning for solo developers.",
    no_args_is_help=True,
)

console = Console(stderr=True)


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to the repository to scan"),
) -> None:
    """Scan a repository and detect its technology stack."""
    try:
        raw = run_specfy(path)
    except NodeNotFoundError:
        console.print(Panel(
            "Node.js is not installed.\n\n"
            "Install from [link=https://nodejs.org]https://nodejs.org[/link]"
            " then run: [bold]naz scan .[/bold]",
            title="[red]Error: Node.js Required[/red]",
            border_style="red",
        ))
        raise typer.Exit(code=1)
    except SpecfyTimeoutError:
        console.print(Panel(
            "Stack analysis timed out after 120 seconds.\n\n"
            "Try scanning a smaller directory.",
            title="[red]Error: Timeout[/red]",
            border_style="red",
        ))
        raise typer.Exit(code=1)
    except SpecfyError as exc:
        detail = exc.stderr[:500] if exc.stderr else str(exc)
        console.print(Panel(
            f"Stack analysis failed.\n\n{detail}",
            title="[red]Error: Analysis Failed[/red]",
            border_style="red",
        ))
        raise typer.Exit(code=1)

    # Phase 3 will replace this with ProjectProfile conversion
    typer.echo(raw)


@app.command()
def version() -> None:
    """Show the current version of naz."""
    from naz import __version__

    typer.echo(f"naz {__version__}")
