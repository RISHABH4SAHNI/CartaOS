# -*- coding: utf-8 -*-
# backend/cartaos/config_migration.py

"""
Configuration migration utilities for CartaOS.

This module provides utilities to migrate configuration settings from environment
variables and .env files to the SQLite database, ensuring smooth transition to
the new persistent storage system.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv

from .config import AppConfig, DatabaseConfig, BACKEND_DIR
from .database import get_database_manager, DatabaseManager

logger = logging.getLogger(__name__)


class ConfigMigrator:
    """
    Handles migration of configuration settings from environment variables to database.
    """

    # Mapping of environment variable names to database setting keys
    ENV_TO_DB_MAPPING = {
        "GEMINI_API_KEY": "gemini_api_key",
        "OBSIDIAN_VAULT_PATH": "obsidian_vault_path",
        "CARTAOS_WATCH_FOLDER": "watch_folder_enabled",
        "CARTAOS_MAX_FILE_SIZE": "max_file_size_mb",
        "CARTAOS_SUMMARY_FORMAT": "default_summary_format",
        "CARTAOS_AUTO_OCR": "auto_ocr_enabled",
    }

    # Default descriptions for migrated settings
    SETTING_DESCRIPTIONS = {
        "gemini_api_key": "Google Gemini API key for AI processing",
        "obsidian_vault_path": "Path to Obsidian vault for summary storage",
        "watch_folder_enabled": "Enable automatic folder watching",
        "max_file_size_mb": "Maximum file size in MB for processing",
        "default_summary_format": "Default format for generated summaries",
        "auto_ocr_enabled": "Automatically run OCR on scanned PDFs",
    }

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the configuration migrator.

        Args:
            db_path (Optional[Path]): Path to SQLite database file.
        """
        self.db_manager = get_database_manager(db_path)
        self.logger = logging.getLogger(__name__)

    def discover_env_settings(self, env_path: Optional[Path] = None) -> Dict[str, str]:
        """
        Discover configuration settings from environment variables and .env file.

        Args:
            env_path (Optional[Path]): Path to .env file. If None, uses default location.

        Returns:
            Dict[str, str]: Dictionary of discovered settings (env_var -> value).
        """
        discovered = {}

        # Load from .env file
        if env_path is None:
            env_path = BACKEND_DIR / ".env"

        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)

        # Check for mapped environment variables
        for env_var, db_key in self.ENV_TO_DB_MAPPING.items():
            value = os.getenv(env_var)
            if value is not None:
                discovered[env_var] = value

        return discovered

    def migrate_settings(
        self, 
        env_settings: Optional[Dict[str, str]] = None,
        overwrite_existing: bool = False
    ) -> Tuple[int, int, List[str]]:
        """
        Migrate settings from environment variables to database.

        Args:
            env_settings (Optional[Dict[str, str]]): Settings to migrate. If None, auto-discovers.
            overwrite_existing (bool): Whether to overwrite existing database settings.

        Returns:
            Tuple[int, int, List[str]]: (migrated_count, skipped_count, error_messages)
        """
        if env_settings is None:
            env_settings = self.discover_env_settings()

        migrated = 0
        skipped = 0
        errors = []

        for env_var, value in env_settings.items():
            if env_var not in self.ENV_TO_DB_MAPPING:
                self.logger.warning(f"Unknown environment variable: {env_var}")
                continue

            db_key = self.ENV_TO_DB_MAPPING[env_var]
            description = self.SETTING_DESCRIPTIONS.get(db_key, f"Migrated from {env_var}")

            # Check if setting already exists
            existing_value = self.db_manager.get_setting(db_key)
            if existing_value is not None and not overwrite_existing:
                self.logger.info(f"Skipping {db_key}: already exists in database")
                skipped += 1
                continue

            # Migrate the setting
            success = self.db_manager.set_setting(db_key, value, description)
            if success:
                self.logger.info(f"Migrated {env_var} -> {db_key}: {value}")
                migrated += 1
            else:
                error_msg = f"Failed to migrate {env_var} -> {db_key}"
                self.logger.error(error_msg)
                errors.append(error_msg)

        return migrated, skipped, errors

    def create_backup_config(self, backup_path: Optional[Path] = None) -> Path:
        """
        Create a backup of current environment-based configuration.

        Args:
            backup_path (Optional[Path]): Path for backup file. If None, auto-generates.

        Returns:
            Path: Path to created backup file.
        """
        if backup_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = BACKEND_DIR / f".env.backup_{timestamp}"

        # Read current .env file
        env_path = BACKEND_DIR / ".env"
        if env_path.exists():
            backup_path.write_text(env_path.read_text())
            self.logger.info(f"Created configuration backup: {backup_path}")
        else:
            # Create backup with current environment variables
            env_settings = self.discover_env_settings()
            backup_content = "# CartaOS Configuration Backup\n"
            backup_content += f"# Created: {datetime.now().isoformat()}\n\n"

            for env_var, value in env_settings.items():
                backup_content += f"{env_var}={value}\n"

            backup_path.write_text(backup_content)
            self.logger.info(f"Created environment backup: {backup_path}")

        return backup_path

    def validate_migration(self) -> Dict[str, bool]:
        """
        Validate that migrated settings are correctly stored in database.

        Returns:
            Dict[str, bool]: Dictionary of setting_key -> validation_success.
        """
        validation_results = {}

        for env_var, db_key in self.ENV_TO_DB_MAPPING.items():
            env_value = os.getenv(env_var)
            db_value = self.db_manager.get_setting(db_key)

            if env_value is not None:
                # Setting exists in environment, should exist in database
                validation_results[db_key] = (db_value == env_value)
            else:
                # Setting doesn't exist in environment, mark as valid
                validation_results[db_key] = True

        return validation_results


def migrate_env_to_database(
    db_path: Optional[Path] = None, 
    backup: bool = True,
    overwrite: bool = False
) -> Dict[str, Union[int, List[str]]]:
    """
    Convenience function to perform complete configuration migration.

    Args:
        db_path (Optional[Path]): Database file path.
        backup (bool): Whether to create a backup before migration.
        overwrite (bool): Whether to overwrite existing database settings.

    Returns:
        Dict[str, Union[int, List[str]]]: Migration results summary.
    """
    migrator = ConfigMigrator(db_path)

    results = {
        "backup_path": None,
        "migrated_count": 0,
        "skipped_count": 0,
        "errors": []
    }

    # Create backup if requested
    if backup:
        results["backup_path"] = str(migrator.create_backup_config())

    # Perform migration
    migrated, skipped, errors = migrator.migrate_settings(overwrite_existing=overwrite)
    results["migrated_count"] = migrated
    results["skipped_count"] = skipped
    results["errors"] = errors

    # Validate migration
    validation = migrator.validate_migration()
    failed_validations = [k for k, v in validation.items() if not v]
    if failed_validations:
        results["errors"].extend([f"Validation failed for: {k}" for k in failed_validations])

    return results