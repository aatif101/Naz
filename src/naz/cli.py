"""Naz CLI - Security scanning for solo developers."""

import typer

app = typer.Typer(
    name="naz",
    help="Security scanning for solo developers.",
    no_args_is_help=True,
)


@app.command()
def scan(
    path: str = typer.Argument(".", help="Path to the repository to scan"),
) -> None:
    """Scan a repository and detect its technology stack."""
    typer.echo(f"Scanning: {path}")


@app.command()
def version() -> None:
    """Show the current version of naz."""
    from naz import __version__

    typer.echo(f"naz {__version__}")
