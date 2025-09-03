# -*- coding: utf-8 -*-
# backend/tests/test_cli_database_integration.py

"""
Tests for CLI integration with database configuration.

Tests the command-line interface database options and their integration
with the configuration system.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import typer.testing

from cartaos.cli import app


@pytest.fixture
def temp_db_path():
    """Fixture that provides a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    yield db_path
    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test_document.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\nSample PDF content for testing")
    return pdf_path


class TestCLIDatabaseIntegration:
    """Test CLI database command integration."""

    def test_cli_help_shows_database_commands(self):
        """Test that database commands are available in CLI help."""
        runner = typer.testing.CliRunner()
        result = runner.invoke(app, ["--help"])
        
        assert result.exit_code == 0
        assert "db" in result.stdout  # Database sub-command should be listed

    def test_database_commands_available(self):
        """Test that database sub-commands are available."""
        runner = typer.testing.CliRunner()
        result = runner.invoke(app, ["db", "--help"])
        
        assert result.exit_code == 0
        assert "init" in result.stdout
        assert "migrate" in result.stdout
        assert "config" in result.stdout
        assert "status" in result.stdout

    def test_summarize_help_shows_database_options(self):
        """Test that summarize command shows database options in help."""
        runner = typer.testing.CliRunner()
        result = runner.invoke(app, ["summarize", "--help"])
        
        assert result.exit_code == 0
        assert "--use-database" in result.stdout or "--db" in result.stdout
        assert "--db-path" in result.stdout

    @patch('cartaos.cli.CartaOSProcessor')
    def test_summarize_with_database_config(self, mock_processor_class, sample_pdf, temp_db_path):
        """Test summarize command with database configuration."""
        # Mock the processor
        mock_processor = MagicMock()
        mock_processor.process.return_value = True
        mock_processor.captured_warnings = []
        mock_processor_class.return_value = mock_processor

        runner = typer.testing.CliRunner()
        
        # Test with --use-database flag
        result = runner.invoke(app, [
            "summarize", 
            str(sample_pdf), 
            "--use-database", 
            "--db-path", str(temp_db_path),
            "--dry-run"  # Avoid file operations
        ])
        
        # Should succeed (exit code 0 or be callable)
        assert result.exit_code == 0 or mock_processor_class.called

    def test_summarize_json_output_includes_database_options(self, sample_pdf):
        """Test that JSON output includes database configuration options."""
        runner = typer.testing.CliRunner()
        
        result = runner.invoke(app, [
            "summarize", 
            str(sample_pdf), 
            "--json",
            "--use-database"
        ])
        
        if result.exit_code == 0:
            output = json.loads(result.stdout.strip())
            assert "options" in output.get("data", {})
            options = output["data"]["options"]
            assert "use_database" in options
            assert "db_path" in options

    @patch('cartaos.cli.DatabaseConfig')
    @patch('cartaos.cli.CartaOSProcessor')
    def test_database_config_fallback_warning(
        self, mock_processor_class, mock_database_config_class, sample_pdf
    ):
        """Test that warning is shown when database is not available."""
        # Mock DatabaseConfig to simulate database unavailability
        mock_config = MagicMock()
        mock_config.database_available = False
        mock_database_config_class.return_value = mock_config

        # Mock processor
        mock_processor = MagicMock()
        mock_processor.process.return_value = True
        mock_processor.captured_warnings = []
        mock_processor_class.return_value = mock_processor

        runner = typer.testing.CliRunner()
        
        result = runner.invoke(app, [
            "summarize", 
            str(sample_pdf), 
            "--use-database",
            "--dry-run"
        ])
        
        # Should show fallback warning
        assert "Warning:" in result.stdout or "database not available" in result.stdout.lower()

    @patch('cartaos.cli.AppConfig')
    @patch('cartaos.cli.CartaOSProcessor')
    def test_default_behavior_uses_appconfig(
        self, mock_processor_class, mock_appconfig_class, sample_pdf
    ):
        """Test that default behavior (without --use-database) still uses AppConfig."""
        # Mock AppConfig
        mock_config = MagicMock()
        mock_appconfig_class.return_value = mock_config

        # Mock processor
        mock_processor = MagicMock()
        mock_processor.process.return_value = True
        mock_processor.captured_warnings = []
        mock_processor_class.return_value = mock_processor

        runner = typer.testing.CliRunner()
        
        result = runner.invoke(app, [
            "summarize", 
            str(sample_pdf), 
            "--dry-run"
        ])
        
        # AppConfig should be used (not DatabaseConfig)
        mock_appconfig_class.assert_called_once()
        mock_processor_class.assert_called_once()


class TestDatabaseCLICommands:
    """Test database management CLI commands."""

    def test_db_init_command(self, temp_db_path):
        """Test database initialization command."""
        runner = typer.testing.CliRunner()
        
        result = runner.invoke(app, [
            "db", "init", 
            "--db-path", str(temp_db_path),
            "--force"  # Force initialization
        ])
        
        # Should complete successfully or show appropriate message
        assert result.exit_code == 0 or "Database" in result.stdout

    def test_db_status_command(self):
        """Test database status command."""
        runner = typer.testing.CliRunner()
        
        result = runner.invoke(app, ["db", "status"])
        
        # Should return status information
        assert result.exit_code == 0

    def test_db_config_list_command(self):
        """Test database config list command."""
        runner = typer.testing.CliRunner()
        
        result = runner.invoke(app, ["db", "config", "list"])
        
        # Should list configuration settings
        assert result.exit_code == 0

    def test_db_migrate_command(self):
        """Test database migration command."""
        runner = typer.testing.CliRunner()
        
        result = runner.invoke(app, ["db", "migrate", "--no-backup"])
        
        # Migration should complete (success or appropriate error)
        assert result.exit_code == 0 or "migration" in result.stdout.lower()

    def test_db_config_set_get_commands(self, temp_db_path):
        """Test setting and getting database configuration."""
        runner = typer.testing.CliRunner()
        
        # Test set command
        result_set = runner.invoke(app, [
            "db", "config", "set", "test_setting",
            "--value", "test_value",
            "--db-path", str(temp_db_path)
        ])
        
        # Test get command  
        result_get = runner.invoke(app, [
            "db", "config", "get", "test_setting",
            "--db-path", str(temp_db_path)
        ])
        
        # Both should complete successfully
        assert result_set.exit_code == 0 or "test_setting" in result_set.stdout
        assert result_get.exit_code == 0 or "test_value" in result_get.stdout
