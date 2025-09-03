#!/usr/bin/env python3
"""
CLI entry point for the simplified installer.
"""
from pathlib import Path

import typer

from .installer import DevInstaller

app = typer.Typer(
    name="cartaos-setup",
    help="CartaOS Development Environment Setup Tool",
    add_completion=False,
)


@app.command()
def setup(
    check_only: bool = typer.Option(
        False,
        "--check-only",
        "-c",
        help="Only check dependencies without installing anything",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be done without actually doing it",
    ),
):
    """
    Set up the CartaOS development environment.

    This tool checks for required system dependencies and sets up the project environment.
    It does NOT install system packages - instead it provides clear instructions for
    missing dependencies.
    """
    installer = DevInstaller(dry_run=dry_run, check_only=check_only)

    success = installer.run()

    if not success:
        raise typer.Exit(1)

    typer.echo("Setup completed successfully!")


@app.command()
def check():
    """
    Check system dependencies without installing anything.

    This is equivalent to running 'setup --check-only'.
    """
    installer = DevInstaller(check_only=True)

    success = installer.run()

    if not success:
        raise typer.Exit(1)

    typer.echo("All dependencies are available!")


if __name__ == "__main__":
    app()
