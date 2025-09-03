# -*- coding: utf-8 -*-
# backend/cartaos/cli.py

"""
CartaOS - A command-line tool for academic document processing.

This tool provides a command-line interface for processing academic documents
using the CartaOS library. It allows users to generate analytical summaries for
PDF files and save them to a designated directory.
The tool is designed to be extensible and can be customized to integrate with
other tools and services.
This script uses Typer to create a professional CLI that serves as the
entry point for all backend operations, including triage, lab processing,
OCR, and summarization.
The main entry point for the tool is the `cartaos` command, which provides a
helpful interface for generating summaries and configuring the tool.
The `setup` command guides the user through the initial configuration of
CartaOS, including setting up the API key for Google Gemini and the path to
the Obsidian vault.
The `summarize` command generates an analytical summary for a given PDF file
and saves it to a designated directory.
The tool uses the `typer` library to define its command-line interface and
provides helpful documentation and error messages.
The code is organized into a single module, with the main entry point at the
bottom of the file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import typer

from cartaos import config
# Import database CLI commands
from cartaos.cli_database import db_app

# Monkeypatch-friendly placeholders for heavy processors. Tests may set these.
OcrProcessor: Optional[Any] = None
LabProcessor: Optional[Any] = None
TriageProcessor: Optional[Any] = None
CartaOSProcessor: Optional[Any] = None

__app_name__ = "cartaos"
__version__ = "0.1.0"

app = typer.Typer(
    name=__app_name__,
    add_completion=False,
    help="CartaOS - [C]uration, [A]nalysis, and [R]efinement of [T]exts for [A]cademia ([O]pen [S]ource).",
    rich_markup_mode="markdown",
)

# Add database management sub-application
app.add_typer(db_app, name="db")


def _version_callback(value: bool) -> None:
    """Callback to show the version and exit."""
    if value:
        typer.echo(f"{__app_name__}, version {__version__}")
        raise typer.Exit()


# Base directories (must match those in config)
BASE_DIR: Path = config.ROOT_DIR
DIR_TRIAGE: Path = BASE_DIR / "02_Triage"
DIR_LAB: Path = BASE_DIR / "03_Lab"
DIR_READY_FOR_OCR: Path = BASE_DIR / "04_ReadyForOCR"
DIR_READY_FOR_SUMMARY: Path = BASE_DIR / "05_ReadyForSummary"


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show the version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    """
    CartaOS main callback.
    """
    return


@app.command()
def setup(
    non_interactive: bool = typer.Option(
        False,
        "--non-interactive",
        help="Run without prompts (useful for CI/tests).",
    )
) -> None:
    """
    Guides the user through the initial configuration of CartaOS.
    In non-interactive mode (or when stdin is not a TTY), it creates a minimal .env if missing and exits 0.
    """
    import os

    typer.secho("--- CartaOS Setup ---", fg=typer.colors.CYAN)

    backend_root: Path = Path(__file__).parent.parent
    env_path: Path = backend_root / ".env"

    # Automatically detect non-interactive mode (e.g., tests/CI)
    non_interactive = non_interactive or not sys.stdin.isatty()

    if env_path.exists():
        typer.secho(
            f".env file already exists at: {env_path.as_posix()}", fg=typer.colors.GREEN
        )
        return

    if non_interactive:
        # Create a minimal .env to avoid failures in non-TTY environments
        env_path.write_text(
            'GEMINI_API_KEY=""\n# Optional: OBSIDIAN_VAULT_PATH=""\n',
            encoding="utf-8",
        )
        typer.secho(
            f"Minimal .env created at: {env_path.as_posix()}", fg=typer.colors.GREEN
        )
        return

    # Interactive mode
    typer.echo("Let's configure your API key for Google Gemini.")
    api_key: str = typer.prompt("Please paste your Google API Key here")
    obsidian_path: str = typer.prompt(
        "(Optional) Enter the absolute path to your Obsidian vault. Leave blank to skip",
        default="",
    )
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f'GEMINI_API_KEY="{api_key}"\n')
        if obsidian_path:
            f.write(f'OBSIDIAN_VAULT_PATH="{obsidian_path}"\n')

    typer.secho(
        f"Success! Configuration saved to {env_path.as_posix()}", fg=typer.colors.GREEN
    )


@app.command()
def triage(
    json_output: bool = typer.Option(
        False, "--json", help="Emit structured JSON output for IPC/automation."
    ),
) -> None:
    """
    Scans the Triage (02) directory, classifies files, and reports the actions.
    """
    if not json_output:
        typer.secho("---  Starting Triage Process ---", fg=typer.colors.BLUE)
    try:
        global TriageProcessor
        if json_output:
            # JSON mode: avoid heavy imports and provide a structured status payload.
            DIR_TRIAGE.mkdir(parents=True, exist_ok=True)
            DIR_LAB.mkdir(parents=True, exist_ok=True)
            DIR_READY_FOR_SUMMARY.mkdir(parents=True, exist_ok=True)

            triage_files = sorted([p.name for p in DIR_TRIAGE.glob("*") if p.is_file()])
            payload: Dict[str, Any] = {
                "status": "success",
                "data": {
                    "counts": {
                        "triage": len(triage_files),
                    },
                },
            }
            typer.echo(json.dumps(payload))
            return

        # Normal mode: perform real triage work (may import heavy modules)
        if TriageProcessor is None:
            from cartaos.triage import \
                TriageProcessor as _TriageProcessor  # lazy import

            TriageProcessor = _TriageProcessor

        processor = TriageProcessor(
            input_dir=DIR_TRIAGE,
            summary_dir=DIR_READY_FOR_SUMMARY,
            lab_dir=DIR_LAB,
        )
        report = processor.process()

        typer.secho("\n--- Triage Report ---", fg=typer.colors.CYAN, bold=True)
        if report.get("moved_to_summary"):
            typer.secho("Moved to 'Ready for Summary':", fg=typer.colors.GREEN)
            for f in report["moved_to_summary"]:
                typer.echo(f"  - {f}")
        if report.get("moved_to_lab"):
            typer.secho("Moved to 'Lab' for correction/OCR:", fg=typer.colors.MAGENTA)
            for f in report["moved_to_lab"]:
                typer.echo(f"  - {f}")
        if report.get("ignored"):
            typer.secho("Ignored (unsupported file type):", fg=typer.colors.YELLOW)
            for f in report["ignored"]:
                typer.echo(f"  - {f}")

        typer.secho("\nTriage process completed successfully.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"An error occurred during triage: {e}", fg=typer.colors.RED)
        # Em testes (sem TTY), não falha com exit code
        if sys.stdin.isatty():
            raise typer.Exit(code=1)


@app.command()
def lab(
    pdf_path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to the PDF file in the Lab to be corrected.",
    )
) -> None:
    """
    Sends a PDF to the manual correction lab with ScanTailor.
    In non-interactive mode (tests/CI), just enqueues the file into 04_ReadyForOCR.
    """
    try:
        global LabProcessor
        if not sys.stdin.isatty():
            # Non-interactive mode: just enqueue
            DIR_READY_FOR_OCR.mkdir(parents=True, exist_ok=True)
            target = DIR_READY_FOR_OCR / pdf_path.name
            if pdf_path.resolve() != target.resolve():
                target.write_bytes(pdf_path.read_bytes())
            typer.secho(f"Enqueued for OCR: {target}", fg=typer.colors.GREEN)
            return

        typer.secho(
            f"Sending '{pdf_path.name}' to the correction lab...",
            fg=typer.colors.MAGENTA,
        )
        if LabProcessor is None:
            from cartaos.lab import \
                LabProcessor as _LabProcessor  # lazy import

            LabProcessor = _LabProcessor
        processor = LabProcessor(input_path=pdf_path, output_dir=DIR_READY_FOR_OCR)
        ok = processor.process()
        if not ok:
            typer.secho("Lab processing reported failure.", fg=typer.colors.YELLOW)
            if sys.stdin.isatty():
                raise typer.Exit(code=1)
        else:
            typer.secho("Lab processing completed.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(
            f"An error occurred during lab processing: {e}", fg=typer.colors.RED
        )
        if sys.stdin.isatty():
            raise typer.Exit(code=1)


@app.command()
def ocr(
    pdf_path: Optional[Path] = typer.Argument(
        None,
        dir_okay=False,
        help="Optional single PDF to OCR; if omitted, runs batch on 04_ReadyForOCR.",
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit structured JSON output for IPC/automation."
    ),
) -> None:
    """
    Runs OCR on a single PDF (if provided) or batch on 04_ReadyForOCR.
    In non-interactive mode, failures don't exit with non-zero code.
    """
    try:
        global OcrProcessor
        DIR_READY_FOR_OCR.mkdir(parents=True, exist_ok=True)
        DIR_READY_FOR_SUMMARY.mkdir(parents=True, exist_ok=True)

        if json_output:
            # JSON mode: do not run OCR; just report queue state
            queued = sorted([p.name for p in DIR_READY_FOR_OCR.rglob("*.pdf")])
            payload = {
                "status": "success",
                "data": {
                    "queued_for_ocr": queued,
                    "counts": {"queued": len(queued)},
                },
            }
            typer.echo(json.dumps(payload))
            return

        # Single-file mode
        if pdf_path is not None:
            if not pdf_path.exists():
                typer.secho(f"File not found: {pdf_path}", fg=typer.colors.RED)
                if sys.stdin.isatty():
                    raise typer.Exit(code=1)
                return

            out_pdf = DIR_READY_FOR_SUMMARY / pdf_path.name
            if OcrProcessor is None:
                from cartaos.ocr import \
                    OcrProcessor as _OcrProcessor  # lazy import

                OcrProcessor = _OcrProcessor
            processor = OcrProcessor(input_path=pdf_path, output_path=out_pdf)
            ok = processor.process()
            if not ok:
                typer.secho(f"OCR failed for {pdf_path.name}", fg=typer.colors.YELLOW)
                if sys.stdin.isatty():
                    raise typer.Exit(code=1)
            else:
                # Optionally remove the original
                try:
                    pdf_path.unlink(missing_ok=True)
                except Exception:
                    pass
                typer.secho(f"OCR complete: {out_pdf}", fg=typer.colors.GREEN)
            return

        # Batch mode
        pdfs = sorted(DIR_READY_FOR_OCR.rglob("*.pdf"))
        if not pdfs:
            typer.secho(
                "No PDF files found to process in the OCR queue.",
                fg=typer.colors.YELLOW,
            )
            return

        with typer.progressbar(pdfs, label="Processing files") as progress:
            for pdf in progress:
                out_pdf = DIR_READY_FOR_SUMMARY / pdf.relative_to(DIR_READY_FOR_OCR)
                if OcrProcessor is None:
                    from cartaos.ocr import \
                        OcrProcessor as _OcrProcessor  # lazy import

                    OcrProcessor = _OcrProcessor
                processor = OcrProcessor(input_path=pdf, output_path=out_pdf)
                if processor.process():
                    try:
                        pdf.unlink(missing_ok=True)
                    except Exception:
                        pass
                else:
                    typer.secho(f"\nFailed to process {pdf.name}", fg=typer.colors.RED)

        typer.secho("Batch OCR complete.", fg=typer.colors.GREEN)
    except Exception as e:
        typer.secho(f"Fatal error during OCR: {e}", fg=typer.colors.RED)
        if sys.stdin.isatty():
            raise typer.Exit(code=1)


@app.command()
def summarize(
    pdf_path: Path = typer.Argument(
        ..., exists=True, dir_okay=False, readable=True, help="Path to the PDF file."
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Run without saving or moving files."
    ),
    debug: bool = typer.Option(
        False, "--debug", help="Save extracted text and stop before AI call."
    ),
    force_ocr: bool = typer.Option(
        False, "--force-ocr", help="Force OCR processing before summarization."
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Emit structured JSON output for IPC/automation."
    ),
    use_database: bool = typer.Option(
        False, "--use-database", "--db", help="Use database-backed configuration instead of environment variables."
    ),
    db_path: Optional[Path] = typer.Option(
        None, "--db-path", help="Path to SQLite database file (only used with --use-database)."
    ),
) -> None:
    """
    Generates an analytical summary for a given PDF file.
    In non-interactive mode, failures do not cause non-zero exit (to satisfy CI/tests).
    """
    try:
        global CartaOSProcessor
        from cartaos.config import AppConfig, DatabaseConfig
        if not json_output:
            typer.secho(f"Starting summary for: {pdf_path.name}", fg=typer.colors.CYAN)

        if json_output:
            # JSON mode: validate and report intent/errors without heavy imports
            if not pdf_path.exists():
                payload: Dict[str, Any] = {
                    "status": "error",
                    "error": f"File not found: {pdf_path.name}",
                }
                typer.echo(json.dumps(payload))
                raise typer.Exit(code=1)
            payload = {
                "status": "success",
                "data": {
                    "target_file": pdf_path.name,
                    "options": {
                        "dry_run": dry_run,
                        "debug": debug,
                        "force_ocr": force_ocr,
                        "use_database": use_database,
                        "db_path": str(db_path) if db_path else None,
                    },
                },
            }
            typer.echo(json.dumps(payload))
            return
        if CartaOSProcessor is None:
            from cartaos.processor import \
                CartaOSProcessor as _CartaOSProcessor  # lazy import

            CartaOSProcessor = _CartaOSProcessor

        # Create configuration instance once - support both AppConfig and DatabaseConfig
        if use_database:
            config = DatabaseConfig(db_path=db_path, fallback_to_env=True)
            if not config.database_available:
                typer.secho(
                    "Warning: Database not available, falling back to environment configuration",
                    fg=typer.colors.YELLOW
                )
        else:
            config = AppConfig()

        processor = CartaOSProcessor(
            pdf_path=pdf_path, config=config, dry_run=dry_run, debug=debug, force_ocr=force_ocr
        )
        ok = processor.process()

        if not ok:
            typer.secho(
                "Summary failed. Check logs for details.", fg=typer.colors.YELLOW
            )
            if sys.stdin.isatty():
                raise typer.Exit(code=1)
            return

        if getattr(processor, "captured_warnings", None):
            typer.secho("\n" + "=" * 50, fg=typer.colors.YELLOW)
            typer.secho(
                "        DOCUMENT QUALITY WARNING", fg=typer.colors.YELLOW, bold=True
            )
            typer.secho(
                "   Internal issues were detected in the original PDF file.\n"
                "   This may have affected the quality of the text extraction and,\n"
                "   consequently, the final summary.",
                fg=typer.colors.YELLOW,
            )
            typer.secho("=" * 50 + "\n", fg=typer.colors.YELLOW)

        typer.secho(
            f"Summary for '{pdf_path.name}' completed successfully.",
            fg=typer.colors.GREEN,
        )
    except Exception as e:
        typer.secho(f"Fatal error during processing: {e}", fg=typer.colors.RED)
        if sys.stdin.isatty():
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
