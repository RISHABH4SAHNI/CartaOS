"""
Simplified installer that focuses on dependency checking and project environment setup
rather than system-level package installation.
"""

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import shell_utils as su


@dataclass
class DependencyStatus:
    """Status of a dependency check."""

    name: str
    available: bool
    path: Optional[str] = None
    installation_guide: Optional[str] = None
    details: Optional[str] = None


class InstallationGuide:
    """Provides platform-specific installation instructions for dependencies."""

    DEPENDENCY_PACKAGES = {
        "tesseract": {
            "Linux": {
                "apt": "sudo apt-get install tesseract-ocr",
                "dnf": "sudo dnf install tesseract",
                "pacman": "sudo pacman -S tesseract",
            },
            "Darwin": {"brew": "brew install tesseract"},
            "Windows": {
                "winget": "winget install UB-Mannheim.TesseractOCR",
                "choco": "choco install tesseract",
            },
        },
        "unpaper": {
            "Linux": {
                "apt": "sudo apt-get install unpaper",
                "dnf": "sudo dnf install unpaper",
                "pacman": "sudo pacman -S unpaper",
            },
            "Darwin": {"brew": "brew install unpaper"},
            "Windows": {
                "manual_install": "Please install unpaper using the official project page: https://www.flameeyes.eu/projects/unpaper"
            },
        },
        "scantailor-advanced": {
            "Linux": {
                "apt": "sudo apt-get install scantailor-advanced",
                "dnf": "sudo dnf install scantailor-advanced",
                "pacman": "sudo pacman -S scantailor-advanced",
            },
            "Darwin": {"brew": "brew install scantailor-advanced"},
            "Windows": {
                "manual_install": "Please download the installer from https://github.com/4lex4/scantailor-advanced/releases"
            },
        },
    }

    def get_installation_instructions(self, dependency: str) -> str:
        """Get platform-specific installation instructions for a dependency."""
        system = platform.system()

        if dependency not in self.DEPENDENCY_PACKAGES:
            return f"Please install {dependency} manually using your system package manager."

        packages = self.DEPENDENCY_PACKAGES[dependency].get(system, {})

        if not packages:
            return (
                f"No installation instructions available for {dependency} on {system}."
            )

        instructions = []
        for package_manager, command in packages.items():
            if package_manager == "manual_install":
                instructions.append(command)
            else:
                instructions.append(f"Using {package_manager}: {command}")

        return "\n".join(instructions)


class DependencyChecker:
    """Checks for required system dependencies."""

    REQUIRED_SYSTEM_DEPS = ["tesseract", "unpaper", "scantailor-advanced"]

    MIN_PYTHON_VERSION = (3, 9)

    def __init__(self):
        self.installation_guide = InstallationGuide()

    def check_system_dependency(self, dependency: str) -> DependencyStatus:
        """Check if a system dependency is available."""
        path = shutil.which(dependency)

        if path:
            return DependencyStatus(name=dependency, available=True, path=path)
        else:
            guide = self.installation_guide.get_installation_instructions(dependency)
            return DependencyStatus(
                name=dependency,
                available=False,
                path=None,
                installation_guide=guide,
                details="Not found in PATH",
            )

    def check_all_dependencies(
        self, dependencies: Optional[List[str]] = None
    ) -> Dict[str, DependencyStatus]:
        """Check all required system dependencies."""
        if dependencies is None:
            dependencies = self.REQUIRED_SYSTEM_DEPS

        results = {}
        for dep in dependencies:
            results[dep] = self.check_system_dependency(dep)

        return results

    def check_python_version(self) -> DependencyStatus:
        """Check if Python version meets requirements."""
        current_version = sys.version_info
        version_str = f"{current_version[0]}.{current_version[1]}.{current_version[2]}"

        if (current_version[0], current_version[1]) >= self.MIN_PYTHON_VERSION:
            return DependencyStatus(
                name="python",
                available=True,
                path=sys.executable,
                details=f"Python {version_str}",
            )
        else:
            min_version_str = (
                f"{self.MIN_PYTHON_VERSION[0]}.{self.MIN_PYTHON_VERSION[1]}"
            )
            return DependencyStatus(
                name="python",
                available=False,
                path=sys.executable,
                installation_guide=f"CartaOS requires Python {min_version_str}+. Current: {version_str}",
                details=f"Python {version_str}",
            )


class DevInstaller:
    """Simplified installer focused on checking dependencies and setting up project environment."""

    def __init__(self, dry_run: bool = False, check_only: bool = False):
        self.dry_run = dry_run
        self.check_only = check_only
        self.console = Console()
        self.dependency_checker = DependencyChecker()
        self.installation_guide = InstallationGuide()
        self.project_root = self._detect_project_root()

    def _detect_project_root(self) -> Path:
        """Detect the project root directory."""
        # Try to find project root using git
        try:
            result = su.run_and_check(
                ["git", "rev-parse", "--show-toplevel"],
            )
            return Path(result.strip())
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to looking for project markers
            current = Path.cwd()
            markers = {".git", "pyproject.toml", "package.json", "README.md"}

            for parent in [current] + list(current.parents):
                if any((parent / marker).exists() for marker in markers):
                    return parent

            # Last resort: use current directory
            return current

    def check_system_dependencies(self) -> bool:
        """Check all required system dependencies."""
        self.console.print(
            Panel.fit("[bold blue]Checking System Dependencies[/bold blue]")
        )

        # Check Python version first
        python_status = self.dependency_checker.check_python_version()
        if not python_status.available:
            self.console.print(f"[red]✗[/red] {python_status.installation_guide}")
            return False
        else:
            self.console.print(f"[green]✓[/green] Python: {python_status.details}")

        # Check system dependencies
        results = self.dependency_checker.check_all_dependencies()

        all_available = True
        for dep_name, status in results.items():
            if status.available:
                self.console.print(f"[green]✓[/green] {dep_name}: {status.path}")
            else:
                self.console.print(f"[red]✗[/red] {dep_name}: Not found")
                self.console.print(f"    {status.installation_guide}")
                all_available = False

        return all_available

    def setup_project_environment(self) -> bool:
        """Set up the project development environment."""
        if self.check_only:
            return True

        self.console.print(
            Panel.fit("[bold blue]Setting Up Project Environment[/bold blue]")
        )

        # Check for Node.js
        if not shutil.which("node"):
            self.console.print(
                "[red]✗[/red] Node.js not found. Please install Node.js LTS."
            )
            return False
        else:
            self.console.print("[green]✓[/green] Node.js found")

        # Check for Poetry
        if not shutil.which("poetry"):
            self.console.print("[red]✗[/red] Poetry not found. Please install Poetry.")
            return False
        else:
            self.console.print("[green]✓[/green] Poetry found")

        success = True

        # Install frontend dependencies
        frontend_dir = self.project_root / "frontend"
        if (frontend_dir / "package.json").exists():
            if not self.dry_run:
                self.console.print("Installing frontend dependencies...")
                try:
                    su.run_and_check(
                        ["npm", "ci"], cwd=frontend_dir
                    )
                    self.console.print(
                        "[green]✓[/green] Frontend dependencies installed"
                    )
                except subprocess.CalledProcessError as e:
                    self.console.print(
                        f"[red]✗[/red] Frontend install failed: {e.stderr}"
                    )
                    success = False
            else:
                self.console.print(
                    "[cyan]DRY RUN:[/cyan] Would install frontend dependencies"
                )

        # Install backend dependencies
        backend_dir = self.project_root / "backend"
        if (backend_dir / "pyproject.toml").exists():
            if not self.dry_run:
                self.console.print("Installing backend dependencies...")
                try:
                    su.run_and_check(
                        ["poetry", "install"],
                        cwd=backend_dir,
                    )
                    self.console.print(
                        "[green]✓[/green] Backend dependencies installed"
                    )
                except subprocess.CalledProcessError as e:
                    self.console.print(
                        f"[red]✗[/red] Backend install failed: {e.stderr}"
                    )
                    success = False
            else:
                self.console.print(
                    "[cyan]DRY RUN:[/cyan] Would install backend dependencies"
                )

        return success

    def generate_summary_report(
        self, status_results: Dict[str, DependencyStatus]
    ) -> str:
        """Generate a summary report of dependency status."""
        lines = ["Dependency Status Summary:", "=" * 30]

        for name, status in status_results.items():
            if status.available:
                lines.append(f"✓ {name}: {status.path or 'Available'}")
            else:
                lines.append(f"✗ {name}: {status.details or 'Not available'}")
                if status.installation_guide:
                    lines.append(f"  Install: {status.installation_guide}")

        return "\n".join(lines)

    def run(self) -> bool:
        """Run the simplified installer."""
        self.console.print(
            Panel.fit(
                "[bold blue]🔧 CartaOS Simplified Development Environment Setup[/bold blue]"
            )
        )

        # Always check system dependencies
        deps_ok = self.check_system_dependencies()

        if not deps_ok:
            self.console.print("\n[red]Some system dependencies are missing.[/red]")
            self.console.print("Please install the missing dependencies and run again.")
            return False

        # If check-only mode, stop here
        if self.check_only:
            self.console.print(
                "\n[green]✓ All system dependencies are available![/green]"
            )
            return True

        # Set up project environment
        env_ok = self.setup_project_environment()

        if env_ok:
            self.console.print(
                "\n[green]🎉 Development environment setup complete![/green]"
            )
            return True
        else:
            self.console.print("\n[red]Project environment setup failed.[/red]")
            return False
