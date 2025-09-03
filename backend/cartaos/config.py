# -*- coding: utf-8 -*-
# backend/cartaos/config.py

import os
from pathlib import Path
from typing import Dict, Literal, Optional, TypedDict, Any
import logging

from dotenv import load_dotenv

# Define the ROOT_DIR as the project's main folder (cartaos-cartaos)
# This path is calculated by going up 3 levels from config.py (config.py -> cartaos -> backend -> ROOT)
ROOT_DIR: Path = Path(__file__).parent.parent.parent

# Define the backend directory for convenience
BACKEND_DIR: Path = ROOT_DIR / "backend"

# Define the main package directory
CARTAOS_DIR: Path = BACKEND_DIR / "cartaos"

# Now, define all other important paths based on these bases
PROMPTS_DIR: Path = CARTAOS_DIR / "prompts"

# Pipeline directories
PIPELINE_STAGES: list[str] = [
    "00_Inbox",
    "02_Triage",
    "03_Lab",
    "04_ReadyForOCR",
    "05_ReadyForSummary",
    "06_TooLarge",
    "07_Processed",
]


class PipelineDirs:
    def __init__(self):
        self.pipeline_dirs = {
            "00_Inbox": ROOT_DIR / "00_Inbox",
            "02_Triage": ROOT_DIR / "02_Triage",
            "03_Lab": ROOT_DIR / "03_Lab",
            "04_ReadyForOCR": ROOT_DIR / "04_ReadyForOCR",
            "05_ReadyForSummary": ROOT_DIR / "05_ReadyForSummary",
            "06_TooLarge": ROOT_DIR / "06_TooLarge",
            "07_Processed": ROOT_DIR / "07_Processed",
        }


PIPELINE_DIRS = PipelineDirs()

# Example of how to access a specific directory:
# PIPELINE_DIRS["03_Lab"]


class AppConfig:
    """
    Application configuration class that loads all environment variables and settings.

    This class is responsible for loading configuration from .env files and environment
    variables. It should be instantiated once at the application's entry point and
    injected into components that need configuration.
    """

    def __init__(self, env_path: Optional[Path] = None) -> None:
        """
        Initialize the configuration by loading from .env file and environment variables.

        Args:
            env_path (Optional[Path]): Custom path to .env file. If None, uses default location.
        """
        # Load environment variables from .env file
        if env_path is None:
            env_path = BACKEND_DIR / ".env"

        load_dotenv(dotenv_path=env_path)

        # Load API configuration
        self.api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
        self.obsidian_vault_path: Optional[str] = os.getenv("OBSIDIAN_VAULT_PATH")

        # Set up directory paths
        self.processed_pdf_dir: Path = ROOT_DIR / "07_Processed"

        # Initialize with default; override if OBSIDIAN_VAULT_PATH is set
        self.summary_dir: Path = self.processed_pdf_dir / "Summaries"
        if self.obsidian_vault_path and Path(self.obsidian_vault_path).is_dir():
            self.summary_dir = Path(self.obsidian_vault_path) / "Summaries"


class DatabaseConfig:
    """
    Database-backed configuration class for persistent application settings.

    This class provides a higher-level interface for managing application configuration
    using the SQLite database for persistence. It integrates with the existing AppConfig
    while adding persistent storage capabilities.
    """

    def __init__(self, db_path: Optional[Path] = None, fallback_to_env: bool = True):
        """
        Initialize the database-backed configuration.

        Args:
            db_path (Optional[Path]): Path to SQLite database file. If None, uses default.
            fallback_to_env (bool): Whether to fall back to environment variables if database is unavailable.
        """
        self.fallback_to_env = fallback_to_env
        self.logger = logging.getLogger(__name__)

        # Initialize database manager
        try:
            from .database import get_database_manager
            self.db_manager = get_database_manager(db_path)
            self.database_available = True
        except Exception as e:
            self.logger.warning(f"Database initialization failed: {e}")
            self.database_available = False
            self.db_manager = None

        # Fallback to AppConfig if database is unavailable and fallback is enabled
        if not self.database_available and self.fallback_to_env:
            self.app_config = AppConfig()
        else:
            self.app_config = None

    @property
    def api_key(self) -> Optional[str]:
        """Get the Gemini API key from database or environment fallback."""
        if self.database_available:
            api_key = self.db_manager.get_setting("gemini_api_key")
            if api_key:
                return api_key

        if self.app_config:
            return self.app_config.api_key

        return None

    @api_key.setter
    def api_key(self, value: Optional[str]):
        """Set the Gemini API key in the database."""
        if self.database_available:
            self.db_manager.set_setting("gemini_api_key", value, "Google Gemini API key for AI processing")
        else:
            self.logger.warning("Cannot persist API key: database unavailable")

    @property
    def obsidian_vault_path(self) -> Optional[str]:
        """Get the Obsidian vault path from database or environment fallback."""
        if self.database_available:
            path = self.db_manager.get_setting("obsidian_vault_path")
            if path:
                return path

        if self.app_config:
            return self.app_config.obsidian_vault_path

        return None

    @obsidian_vault_path.setter
    def obsidian_vault_path(self, value: Optional[str]):
        """Set the Obsidian vault path in the database."""
        if self.database_available:
            self.db_manager.set_setting("obsidian_vault_path", value, "Path to Obsidian vault for summary storage")
        else:
            self.logger.warning("Cannot persist Obsidian vault path: database unavailable")

    @property
    def summary_dir(self) -> Path:
        """Get the summary directory path, respecting Obsidian vault setting."""
        obsidian_path = self.obsidian_vault_path

        if obsidian_path and Path(obsidian_path).is_dir():
            return Path(obsidian_path) / "Summaries"

        return ROOT_DIR / "07_Processed" / "Summaries"

    @property
    def processed_pdf_dir(self) -> Path:
        """Get the processed PDF directory path."""
        return ROOT_DIR / "07_Processed"

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting by key."""
        if self.database_available:
            value = self.db_manager.get_setting(key)
            if value is not None:
                return value

        return default

    def set_setting(self, key: str, value: Any, description: Optional[str] = None) -> bool:
        """Set a configuration setting."""
        if self.database_available:
            return self.db_manager.set_setting(key, str(value) if value is not None else None, description)
        else:
            self.logger.warning(f"Cannot persist setting '{key}': database unavailable")
            return False

    def get_all_settings(self) -> Dict[str, str]:
        """Get all configuration settings."""
        if self.database_available:
            return self.db_manager.get_all_settings()

        return {}
