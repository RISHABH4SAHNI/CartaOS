# -*- coding: utf-8 -*-
# backend/tests/test_database_config.py

"""
Unit tests for the DatabaseConfig class.

Tests the integration between database persistence and configuration management.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from cartaos.config import DatabaseConfig, AppConfig
from cartaos.database import DatabaseManager


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
def in_memory_db_config():
    """Fixture that provides a DatabaseConfig with in-memory database."""
    config = DatabaseConfig(db_path=":memory:", fallback_to_env=False)
    return config


class TestDatabaseConfig:
    """Test cases for DatabaseConfig class."""

    def test_initialization_with_database(self, temp_db_path):
        """Test DatabaseConfig initialization with a working database."""
        config = DatabaseConfig(db_path=temp_db_path, fallback_to_env=False)

        assert config.database_available is True
        assert config.db_manager is not None
        assert config.app_config is None

    def test_initialization_with_fallback(self, monkeypatch):
        """Test DatabaseConfig initialization with fallback to AppConfig."""
        # Mock environment variables
        monkeypatch.setenv("GEMINI_API_KEY", "test_api_key")
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "/test/obsidian")

        # Mock database failure
        with patch('cartaos.config.get_database_manager', side_effect=Exception("DB Error")):
            config = DatabaseConfig(fallback_to_env=True)

        assert config.database_available is False
        assert config.db_manager is None
        assert config.app_config is not None
        assert isinstance(config.app_config, AppConfig)

    def test_initialization_without_fallback(self):
        """Test DatabaseConfig initialization without fallback when database fails."""
        with patch('cartaos.config.get_database_manager', side_effect=Exception("DB Error")):
            config = DatabaseConfig(fallback_to_env=False)

        assert config.database_available is False
        assert config.db_manager is None
        assert config.app_config is None

    def test_api_key_property_from_database(self, in_memory_db_config):
        """Test API key property when stored in database."""
        config = in_memory_db_config

        # Set API key in database
        config.api_key = "test_db_api_key"

        # Should retrieve from database
        assert config.api_key == "test_db_api_key"

    def test_api_key_property_fallback_to_env(self, monkeypatch):
        """Test API key property fallback to environment variables."""
        monkeypatch.setenv("GEMINI_API_KEY", "test_env_api_key")

        with patch('cartaos.config.get_database_manager', side_effect=Exception("DB Error")):
            config = DatabaseConfig(fallback_to_env=True)

        assert config.api_key == "test_env_api_key"

    def test_api_key_property_no_fallback(self):
        """Test API key property when no fallback is available."""
        with patch('cartaos.config.get_database_manager', side_effect=Exception("DB Error")):
            config = DatabaseConfig(fallback_to_env=False)

        assert config.api_key is None

    def test_obsidian_vault_path_property_from_database(self, in_memory_db_config):
        """Test Obsidian vault path property when stored in database."""
        config = in_memory_db_config

        # Set path in database
        config.obsidian_vault_path = "/test/vault/path"

        # Should retrieve from database
        assert config.obsidian_vault_path == "/test/vault/path"

    def test_obsidian_vault_path_property_fallback_to_env(self, monkeypatch):
        """Test Obsidian vault path property fallback to environment variables."""
        monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "/test/env/vault")

        with patch('cartaos.config.get_database_manager', side_effect=Exception("DB Error")):
            config = DatabaseConfig(fallback_to_env=True)

        assert config.obsidian_vault_path == "/test/env/vault"

    def test_summary_dir_with_obsidian_vault(self, in_memory_db_config, tmp_path):
        """Test summary directory path when Obsidian vault is configured."""
        config = in_memory_db_config

        # Create a temporary vault directory
        vault_path = tmp_path / "test_vault"
        vault_path.mkdir()

        config.obsidian_vault_path = str(vault_path)

        expected_summary_dir = vault_path / "Summaries"
        assert config.summary_dir == expected_summary_dir

    def test_summary_dir_without_obsidian_vault(self, in_memory_db_config):
        """Test summary directory path when Obsidian vault is not configured."""
        config = in_memory_db_config

        # Ensure no Obsidian vault path is set
        config.obsidian_vault_path = None

        from cartaos.config import ROOT_DIR
        expected_summary_dir = ROOT_DIR / "07_Processed" / "Summaries"
        assert config.summary_dir == expected_summary_dir

    def test_processed_pdf_dir_property(self, in_memory_db_config):
        """Test processed PDF directory property."""
        config = in_memory_db_config

        from cartaos.config import ROOT_DIR
        expected_dir = ROOT_DIR / "07_Processed"
        assert config.processed_pdf_dir == expected_dir

    def test_get_setting(self, in_memory_db_config):
        """Test generic setting retrieval."""
        config = in_memory_db_config

        # Set a custom setting
        config.set_setting("test_setting", "test_value", "Test description")

        # Retrieve the setting
        assert config.get_setting("test_setting") == "test_value"
        assert config.get_setting("nonexistent_setting", "default") == "default"

    def test_set_setting(self, in_memory_db_config):
        """Test generic setting storage."""
        config = in_memory_db_config

        # Set various types of settings
        assert config.set_setting("string_setting", "test_string") is True
        assert config.set_setting("int_setting", 42) is True
        assert config.set_setting("bool_setting", True) is True
        assert config.set_setting("none_setting", None) is True

        # Verify they are stored correctly
        assert config.get_setting("string_setting") == "test_string"
        assert config.get_setting("int_setting") == "42"  # Stored as string
        assert config.get_setting("bool_setting") == "True"  # Stored as string
        assert config.get_setting("none_setting") is None

    def test_get_all_settings(self, in_memory_db_config):
        """Test retrieval of all settings."""
        config = in_memory_db_config

        # Set multiple settings
        config.set_setting("setting1", "value1")
        config.set_setting("setting2", "value2")
        config.set_setting("setting3", "value3")

        all_settings = config.get_all_settings()

        assert "setting1" in all_settings
        assert "setting2" in all_settings
        assert "setting3" in all_settings
        assert all_settings["setting1"] == "value1"
        assert all_settings["setting2"] == "value2"
        assert all_settings["setting3"] == "value3"

    def test_setting_operations_without_database(self):
        """Test setting operations when database is not available."""
        with patch('cartaos.config.get_database_manager', side_effect=Exception("DB Error")):
            config = DatabaseConfig(fallback_to_env=False)

        # Should return False when trying to set
        assert config.set_setting("test", "value") is False

        # Should return default when trying to get
        assert config.get_setting("test", "default") == "default"

        # Should return empty dict for all settings
        assert config.get_all_settings() == {}