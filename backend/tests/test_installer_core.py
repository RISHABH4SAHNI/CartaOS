# -*- coding: utf-8 -*-
"""
Tests for the simplified, robust development environment installer.

These tests cover the main DevInstaller class, ensuring it correctly checks
for dependencies and handles different execution modes like 'dry-run' and 'check-only'.
"""

import platform
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cartaos.install_dev_env.installer import (
    DevInstaller,
    DependencyChecker,
    DependencyStatus,
    InstallationGuide,
)

# --- Fixtures ---

@pytest.fixture
def mock_dependency_checker(monkeypatch):
    """Fixture to mock the DependencyChecker and its methods."""
    mock = MagicMock(spec=DependencyChecker)
    # Mock the methods that are called by DevInstaller.run()
    mock.check_python_version.return_value = DependencyStatus(name="python", available=True)
    mock.check_all_dependencies.return_value = {
        "tesseract": DependencyStatus(name="tesseract", available=True)
    }
    monkeypatch.setattr(
        "cartaos.install_dev_env.installer.DependencyChecker", lambda: mock
    )
    return mock


@pytest.fixture
def mock_dev_installer(mock_dependency_checker, tmp_path) -> DevInstaller:
    """Fixture to create a DevInstaller instance with a mocked dependency checker."""
    # Patch subprocess so that git commands don't fail in CI environments
    with patch(
        "cartaos.install_dev_env.installer.DevInstaller._detect_project_root",
        return_value=tmp_path,
    ):
        installer = DevInstaller(dry_run=False, check_only=False)
        installer.dependency_checker = mock_dependency_checker
        installer.console = MagicMock()
        return installer


# --- Tests for InstallationGuide ---

def test_installation_guide_linux():
    """Test that installation instructions for Linux are returned correctly."""
    guide = InstallationGuide()
    with patch("platform.system", return_value="Linux"):
        instructions = guide.get_installation_instructions("tesseract")
        assert "sudo apt-get install tesseract-ocr" in instructions
        assert "sudo dnf install tesseract" in instructions


# --- Tests for DependencyChecker ---

def test_dependency_checker_python_ok():
    """Test Python version check when version is sufficient."""
    checker = DependencyChecker()
    with patch.object(sys, "version_info", (3, 10, 0)):
        status = checker.check_python_version()
        assert status.available is True


def test_dependency_checker_python_fail():
    """Test Python version check when version is too old."""
    checker = DependencyChecker()
    with patch.object(sys, "version_info", (3, 8, 0)):
        status = checker.check_python_version()
        assert status.available is False
        assert "requires Python 3.9+" in status.installation_guide


def test_dependency_checker_system_dep_found():
    """Test system dependency check when the dependency is found."""
    checker = DependencyChecker()
    with patch("shutil.which", return_value="/usr/bin/tesseract"):
        status = checker.check_system_dependency("tesseract")
        assert status.available is True
        assert status.path == "/usr/bin/tesseract"


# --- Tests for DevInstaller ---

def test_dev_installer_run_success(mock_dev_installer, mock_dependency_checker):
    """Test a successful run of the DevInstaller."""
    # Mocks are configured in fixtures to return success
    with patch(
        "cartaos.install_dev_env.installer.DevInstaller.setup_project_environment",
        return_value=True,
    ) as mock_setup:
        success = mock_dev_installer.run()
        assert success is True
        mock_setup.assert_called_once()


def test_dev_installer_run_dep_check_fails(mock_dev_installer, mock_dependency_checker):
    """Test a failed run due to a missing system dependency."""
    mock_dependency_checker.check_all_dependencies.return_value = {
        "tesseract": DependencyStatus(name="tesseract", available=False)
    }
    with patch(
        "cartaos.install_dev_env.installer.DevInstaller.setup_project_environment"
    ) as mock_setup:
        success = mock_dev_installer.run()
        assert success is False
        mock_setup.assert_not_called()  # Should not attempt to set up project


def test_dev_installer_check_only_mode(mock_dev_installer, mock_dependency_checker):
    """Test that 'check-only' mode only runs dependency checks."""
    mock_dev_installer.check_only = True
    with patch(
        "cartaos.install_dev_env.installer.DevInstaller.setup_project_environment"
    ) as mock_setup:
        success = mock_dev_installer.run()
        assert success is True
        mock_setup.assert_not_called()


def test_dev_installer_dry_run_mode(mock_dev_installer, tmp_path):
    """Test that 'dry-run' mode does not execute installation commands."""
    mock_dev_installer.dry_run = True

    # Create dummy files so the dry-run logic is reached
    (tmp_path / "frontend").mkdir(exist_ok=True)
    (tmp_path / "frontend" / "package.json").touch()
    (tmp_path / "backend").mkdir(exist_ok=True)
    (tmp_path / "backend" / "pyproject.toml").touch()

    with patch("cartaos.install_dev_env.shell_utils.run_and_check") as mock_run:
        success = mock_dev_installer.setup_project_environment()
        assert success is True
        mock_run.assert_not_called()
        # Check that the console was instructed to print the dry-run message
        any_dry_run_call = any(
            "[cyan]DRY RUN:[/cyan]" in str(call.args[0])
            for call in mock_dev_installer.console.print.call_args_list
        )
        assert any_dry_run_call, "The 'DRY RUN' message was not printed to the console."


def test_setup_project_environment_success(mock_dev_installer, tmp_path):
    """Test successful setup of frontend and backend dependencies."""
    # Override the project_root from the fixture to use tmp_path
    mock_dev_installer.project_root = tmp_path

    with patch(
        "cartaos.install_dev_env.shell_utils.run_and_check", return_value="Success"
    ) as mock_run:
        # Create dummy package.json and pyproject.toml
        (tmp_path / "frontend").mkdir(parents=True, exist_ok=True)
        (tmp_path / "frontend" / "package.json").touch()
        (tmp_path / "backend").mkdir(parents=True, exist_ok=True)
        (tmp_path / "backend" / "pyproject.toml").touch()

        success = mock_dev_installer.setup_project_environment()

        assert success is True
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["npm", "ci"], cwd=tmp_path / "frontend")
        mock_run.assert_any_call(["poetry", "install"], cwd=tmp_path / "backend")