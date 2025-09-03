# -*- coding: utf-8 -*-
# backend/cartaos/cli_database.py

"""
Database management CLI commands for CartaOS.

This module provides command-line interface commands for managing the SQLite database,
including configuration migration, settings management, and database maintenance.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .config import DatabaseConfig, ROOT_DIR
from .config_migration import migrate_env_to_database, ConfigMigrator
from .database import get_database_manager

# Create a sub-application for database commands
db_app = typer.Typer(
    name="db",
    help="Database management commands for CartaOS configuration and state."
)

console = Console()


@db_app.command()
def init(
    db_path: Optional[Path] = typer.Option(
        None, "--db-path", "-d", help="Path to SQLite database file"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force initialization even if database exists"
    )
) -> None:
    """
    Initialize the CartaOS database with default tables and settings.
    """
    try:
        if db_path is None:
            db_path = ROOT_DIR / "cartaos.db"

        if db_path.exists() and not force:
            console.print(f"[yellow]Database already exists at {db_path}[/yellow]")
            console.print("Use --force to reinitialize")
            raise typer.Exit(1)

        db_manager = get_database_manager(db_path)

        if db_manager.initialize_database():
            console.print(f"[green]✓[/green] Database initialized at: {db_path}")

            # Show summary of default settings
            settings = db_manager.get_all_settings()
            if settings:
                console.print(f"\n[blue]Default settings initialized:[/blue]")
                for key, value in settings.items():
                    display_value = value if value else "[dim]<not set>[/dim]"
                    console.print(f"  {key}: {display_value}")
        else:
            console.print("[red]✗[/red] Failed to initialize database")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error initializing database: {e}[/red]")
        raise typer.Exit(1)


@db_app.command()
def migrate(
    db_path: Optional[Path] = typer.Option(
        None, "--db-path", "-d", help="Path to SQLite database file"
    ),
    backup: bool = typer.Option(
        True, "--backup/--no-backup", help="Create backup before migration"
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", "-o", help="Overwrite existing database settings"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output results in JSON format"
    )
) -> None:
    """
    Migrate configuration settings from environment variables to database.
    """
    try:
        results = migrate_env_to_database(db_path, backup=backup, overwrite=overwrite)

        if json_output:
            typer.echo(json.dumps(results, indent=2))
            return

        # Display results in a nice format
        console.print(Panel.fit(
            "[bold blue]Configuration Migration Results[/bold blue]",
            border_style="blue"
        ))

        if results["backup_path"]:
            console.print(f"[green]✓[/green] Backup created: {results['backup_path']}")

        migrated = results["migrated_count"]
        skipped = results["skipped_count"]
        errors = results["errors"]

        console.print(f"[green]✓[/green] Settings migrated: {migrated}")
        if skipped > 0:
            console.print(f"[yellow]○[/yellow] Settings skipped: {skipped}")

        if errors:
            console.print(f"[red]✗[/red] Errors: {len(errors)}")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")

        if migrated == 0 and skipped == 0 and not errors:
            console.print("[dim]No configuration settings found to migrate[/dim]")

    except Exception as e:
        console.print(f"[red]Error during migration: {e}[/red]")
        raise typer.Exit(1)


@db_app.command()
def config(
    action: str = typer.Argument(..., help="Action: get, set, list, delete"),
    key: Optional[str] = typer.Argument(None, help="Configuration key"),
    value: Optional[str] = typer.Option(None, "--value", "-v", help="Configuration value"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Setting description"),
    db_path: Optional[Path] = typer.Option(
        None, "--db-path", help="Path to SQLite database file"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output in JSON format"
    )
) -> None:
    """
    Manage configuration settings in the database.

    Actions:
    - get <key>: Retrieve a setting value
    - set <key> --value <value>: Set a setting value
    - list: List all settings
    - delete <key>: Delete a setting
    """
    try:
        db_config = DatabaseConfig(db_path, fallback_to_env=False)

        if not db_config.database_available:
            console.print("[red]Database is not available[/red]")
            raise typer.Exit(1)

        db_manager = db_config.db_manager

        if action == "get":
            if not key:
                console.print("[red]Key is required for 'get' action[/red]")
                raise typer.Exit(1)

            value_result = db_manager.get_setting(key)

            if json_output:
                typer.echo(json.dumps({key: value_result}))
            else:
                if value_result is not None:
                    console.print(f"{key}: {value_result}")
                else:
                    console.print(f"[yellow]Setting '{key}' not found[/yellow]")

        elif action == "set":
            if not key or value is None:
                console.print("[red]Key and --value are required for 'set' action[/red]")
                raise typer.Exit(1)

            success = db_manager.set_setting(key, value, description)

            if json_output:
                typer.echo(json.dumps({"success": success, "key": key, "value": value}))
            else:
                if success:
                    console.print(f"[green]✓[/green] Set {key} = {value}")
                else:
                    console.print(f"[red]✗[/red] Failed to set {key}")

        elif action == "list":
            settings = db_manager.get_all_settings()

            if json_output:
                typer.echo(json.dumps(settings, indent=2))
            else:
                if settings:
                    table = Table(title="Configuration Settings")
                    table.add_column("Key", style="cyan")
                    table.add_column("Value", style="green")

                    for key, value in settings.items():
                        display_value = value if value else "[dim]<not set>[/dim]"
                        table.add_row(key, display_value)

                    console.print(table)
                else:
                    console.print("[dim]No settings found[/dim]")

        elif action == "delete":
            if not key:
                console.print("[red]Key is required for 'delete' action[/red]")
                raise typer.Exit(1)

            success = db_manager.delete_setting(key)

            if json_output:
                typer.echo(json.dumps({"success": success, "key": key, "action": "deleted"}))
            else:
                if success:
                    console.print(f"[green]✓[/green] Deleted setting: {key}")
                else:
                    console.print(f"[red]✗[/red] Failed to delete setting: {key}")

        else:
            console.print(f"[red]Unknown action: {action}[/red]")
            console.print("Valid actions: get, set, list, delete")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error managing configuration: {e}[/red]")
        raise typer.Exit(1)


@db_app.command()
def status(
    db_path: Optional[Path] = typer.Option(
        None, "--db-path", help="Path to SQLite database file"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output in JSON format"
    )
) -> None:
    """
    Show database status and health information.
    """
    try:
        db_config = DatabaseConfig(db_path, fallback_to_env=False)

        status_info = {
            "database_available": db_config.database_available,
            "database_path": str(db_config.db_manager.db_path) if db_config.database_available else None,
            "settings_count": len(db_config.get_all_settings()) if db_config.database_available else 0,
        }

        if json_output:
            typer.echo(json.dumps(status_info, indent=2))
        else:
            status_color = "green" if db_config.database_available else "red"
            status_text = "Available" if db_config.database_available else "Not Available"

            console.print(Panel.fit(
                f"[bold]Database Status[/bold]\n\n"
                f"Status: [{status_color}]{status_text}[/{status_color}]\n"
                f"Path: {status_info['database_path'] or 'N/A'}\n"
                f"Settings: {status_info['settings_count']}",
                border_style=status_color
            ))

    except Exception as e:
        console.print(f"[red]Error checking database status: {e}[/red]")
        raise typer.Exit(1)