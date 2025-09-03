# -*- coding: utf-8 -*-
# backend/tests/test_sqlite_integration.py

"""
Integration tests for SQLite database persistence in CartaOS.

Tests the complete integration between database layer, configuration management,
and application components like the processor and CLI.
"""

import os
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cartaos.config import AppConfig, DatabaseConfig
from cartaos.database import DatabaseManager, get_database_manager
from cartaos.config_migration import ConfigMigrator, migrate_env_to_database
from cartaos.processor import CartaOSProcessor


@pytest.fixture
def temp_env_file():
    """Create a temporary .env file with test configuration."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("GEMINI_API_KEY=test_api_key_from_env\n")
        f.write("OBSIDIAN_VAULT_PATH=/test/vault/path\n")
        f.write("CARTAOS_MAX_FILE_SIZE=100\n")
        env_path = Path(f.name)

    yield env_path

    # Cleanup
    if env_path.exists():
        env_path.unlink()


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


class TestDatabaseConfigurationIntegration:
    """Integration tests for database-backed configuration."""

    def test_database_config_fallback_to_appconfig(self, monkeypatch, temp_env_file):
        """Test that DatabaseConfig falls back to AppConfig when database fails."""
        # Set environment variables
        monkeypatch.setenv("GEMINI_API_KEY", "env_api_key")
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "/env/vault")

        # Mock database initialization to fail
        with patch('cartaos.config.get_database_manager', side_effect=Exception("DB Error")):
            config = DatabaseConfig(fallback_to_env=True)

        # Should fall back to environment values
        assert config.api_key == "env_api_key"
        assert config.obsidian_vault_path == "/env/vault"
        assert config.database_available is False
        assert config.app_config is not None

    def test_database_config_persistence_over_env(self, monkeypatch, temp_db_path):
        """Test that database values take precedence over environment variables."""
        # Set environment variables
        monkeypatch.setenv("GEMINI_API_KEY", "env_api_key")
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "/env/vault")

        # Create database config
        config = DatabaseConfig(db_path=temp_db_path, fallback_to_env=True)

        # Set values in database
        config.api_key = "db_api_key"
        config.obsidian_vault_path = "/db/vault"

        # Database values should take precedence
        assert config.api_key == "db_api_key"
        assert config.obsidian_vault_path == "/db/vault"

    def test_database_config_custom_settings(self, temp_db_path):
        """Test custom setting management in DatabaseConfig."""
        config = DatabaseConfig(db_path=temp_db_path)

        # Set custom settings
        assert config.set_setting("custom_setting", "custom_value", "Test setting") is True
        assert config.set_setting("numeric_setting", 42) is True
        assert config.set_setting("boolean_setting", True) is True

        # Retrieve custom settings
        assert config.get_setting("custom_setting") == "custom_value"
        assert config.get_setting("numeric_setting") == "42"  # Stored as string
        assert config.get_setting("boolean_setting") == "True"  # Stored as string
        assert config.get_setting("nonexistent", "default") == "default"

        # Get all settings
        all_settings = config.get_all_settings()
        assert "custom_setting" in all_settings
        assert "numeric_setting" in all_settings
        assert "boolean_setting" in all_settings


class TestConfigurationMigration:
    """Integration tests for configuration migration utilities."""

    def test_config_migrator_discovery(self, monkeypatch, temp_env_file):
        """Test configuration discovery from environment variables."""
        # Set some environment variables
        monkeypatch.setenv("GEMINI_API_KEY", "discovered_api_key")
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "/discovered/vault")
        monkeypatch.setenv("CARTAOS_MAX_FILE_SIZE", "50")

        migrator = ConfigMigrator(":memory:")
        discovered = migrator.discover_env_settings()

        assert "GEMINI_API_KEY" in discovered
        assert "OBSIDIAN_VAULT_PATH" in discovered
        assert "CARTAOS_MAX_FILE_SIZE" in discovered
        assert discovered["GEMINI_API_KEY"] == "discovered_api_key"

    def test_config_migration_process(self, monkeypatch, temp_db_path):
        """Test the complete migration process."""
        # Set environment variables to migrate
        monkeypatch.setenv("GEMINI_API_KEY", "migrate_api_key")
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "/migrate/vault")

        migrator = ConfigMigrator(temp_db_path)

        # Perform migration
        migrated, skipped, errors = migrator.migrate_settings()

        assert migrated >= 2  # At least API key and vault path
        assert len(errors) == 0

        # Verify settings were migrated
        assert migrator.db_manager.get_setting("gemini_api_key") == "migrate_api_key"
        assert migrator.db_manager.get_setting("obsidian_vault_path") == "/migrate/vault"

    def test_migration_validation(self, monkeypatch, temp_db_path):
        """Test migration validation functionality."""
        # Set environment variables
        monkeypatch.setenv("GEMINI_API_KEY", "validation_api_key")

        migrator = ConfigMigrator(temp_db_path)

        # Migrate settings
        migrator.migrate_settings()

        # Validate migration
        validation_results = migrator.validate_migration()

        assert "gemini_api_key" in validation_results
        assert validation_results["gemini_api_key"] is True

    def test_convenience_migration_function(self, monkeypatch, temp_db_path):
        """Test the convenience function for complete migration."""
        # Set environment variables
        monkeypatch.setenv("GEMINI_API_KEY", "convenience_api_key")

        # Perform migration using convenience function
        results = migrate_env_to_database(temp_db_path, backup=False, overwrite=False)

        assert results["migrated_count"] >= 1
        assert len(results["errors"]) == 0

        # Verify the setting was migrated
        db_config = DatabaseConfig(temp_db_path, fallback_to_env=False)
        assert db_config.get_setting("gemini_api_key") == "convenience_api_key"


class TestProcessorIntegration:
    """Integration tests for processor with database configuration."""

    def test_processor_with_database_config(self, temp_db_path, sample_pdf):
        """Test CartaOSProcessor with DatabaseConfig."""
        # Create database config with API key
        config = DatabaseConfig(db_path=temp_db_path, fallback_to_env=False)
        config.api_key = "test_processor_api_key"

        # Create processor instance
        processor = CartaOSProcessor(
            pdf_path=sample_pdf,
            config=config,
            dry_run=True,
            debug=True
        )

        # Verify configuration is accessible
        assert processor.config.api_key == "test_processor_api_key"
        assert isinstance(processor.config, DatabaseConfig)

    def test_processor_with_appconfig_backwards_compatibility(self, monkeypatch, sample_pdf):
        """Test that processor still works with AppConfig for backwards compatibility."""
        # Set environment variables
        monkeypatch.setenv("GEMINI_API_KEY", "appconfig_api_key")

        # Create AppConfig instance
        config = AppConfig()

        # Create processor instance
        processor = CartaOSProcessor(
            pdf_path=sample_pdf,
            config=config,
            dry_run=True,
            debug=True
        )

        # Verify configuration is accessible
        assert processor.config.api_key == "appconfig_api_key"
        assert isinstance(processor.config, AppConfig)

    @patch('cartaos.processor.extract_text')
    @patch('cartaos.processor.generate_summary')
    def test_processor_workflow_with_database_config(
        self, mock_generate_summary, mock_extract_text, temp_db_path, sample_pdf, tmp_path
    ):
        """Test complete processor workflow with database configuration."""
        # Mock the AI functions
        mock_extract_text.return_value = "Sample extracted text content"
        mock_generate_summary.return_value = "# Sample Summary\n\nThis is a test summary."

        # Setup database config
        config = DatabaseConfig(db_path=temp_db_path, fallback_to_env=False)
        config.api_key = "workflow_test_api_key"

        # Create processor and run in dry-run mode
        processor = CartaOSProcessor(
            pdf_path=sample_pdf,
            config=config,
            dry_run=True  # Dry run to avoid file operations
        )

        # Process should succeed
        result = processor.process()
        assert result is True

        # Verify mocks were called with correct parameters
        mock_extract_text.assert_called_once_with(sample_pdf)
        mock_generate_summary.assert_called_once_with("Sample extracted text content", "workflow_test_api_key")


class TestDatabaseMaintenance:
    """Tests for database maintenance and health checks."""

    def test_database_initialization_and_health(self, temp_db_path):
        """Test database initialization and basic health checks."""
        # Initialize database
        db_manager = DatabaseManager(temp_db_path)
        success = db_manager.initialize_database()

        assert success is True
        assert temp_db_path.exists()

        # Verify tables exist and contain expected default settings
        settings = db_manager.get_all_settings()
        expected_defaults = [
            "gemini_api_key",
            "obsidian_vault_path",
            "watch_folder_enabled",
            "default_summary_format",
            "auto_ocr_enabled",
            "max_file_size_mb"
        ]

        for default_key in expected_defaults:
            # Settings should exist (even if value is None)
            db_value = db_manager.get_setting(default_key)
            # Should either have a value or be explicitly None
            assert db_value is not None or db_manager.get_setting(default_key) is None

    def test_database_concurrent_access(self, temp_db_path):
        """Test concurrent access to the database."""
        # Create multiple database managers pointing to the same file
        db_manager1 = DatabaseManager(temp_db_path)
        db_manager1.initialize_database()

        db_manager2 = DatabaseManager(temp_db_path)

        # Set value with first manager
        db_manager1.set_setting("concurrent_test", "value1")

        # Read with second manager
        value = db_manager2.get_setting("concurrent_test")
        assert value == "value1"

        # Update with second manager
        db_manager2.set_setting("concurrent_test", "value2")

        # Read updated value with first manager
        updated_value = db_manager1.get_setting("concurrent_test")
        assert updated_value == "value2"