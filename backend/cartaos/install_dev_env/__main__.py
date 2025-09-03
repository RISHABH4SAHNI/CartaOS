# install-dev-env/__main__.py

"""
CLI entry point for the installer package.
Parses arguments and runs the main installer logic.
"""

import argparse
import sys

from rich.panel import Panel

# Relative import from within the package
from .installer import DevInstaller


def main():
    """Parses command line arguments and starts the installation process."""
    parser = argparse.ArgumentParser(
        description="A robust, modular installer for the CartaOS development environment.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run all checks without making any system changes.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check dependencies without installing anything.",
    )

    args = parser.parse_args()

    installer = DevInstaller(
        dry_run=args.dry_run,
        check_only=args.check_only,
    )

    try:
        installer.run()
    except KeyboardInterrupt:
        installer.console.print(
            "\n[bold red]Installation cancelled by user.[/bold red]"
        )
        sys.exit(1)
    except Exception as e:
        installer.console.print(
            f"\n[bold red]An unexpected error occurred: {e}[/bold red]"
        )
        sys.exit(1)



if __name__ == "__main__":
    main()
