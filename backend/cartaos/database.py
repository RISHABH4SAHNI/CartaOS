# -*- coding: utf-8 -*-
# backend/cartaos/database.py

"""
Database access layer for CartaOS application.

This module provides a structured SQLite-based persistence layer for managing
application state including user settings, project metadata, and document processing queues.
Uses SQLAlchemy Core for type safety and easier schema management.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import sqlite3
from contextlib import contextmanager

from sqlalchemy import (
    create_engine, Table, Column, Integer, String, DateTime, Text, Boolean,
    MetaData, select, insert, update, delete, func
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database connections and operations for CartaOS.

    Provides CRUD operations for user settings, projects, and document queue management.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize the database manager.

        Args:
            db_path (Optional[Path]): Path to SQLite database file. 
                                     If None, uses default location in user's config directory.
        """
        if db_path is None:
            # Default to a reasonable location for the database
            from .config import ROOT_DIR
            db_path = ROOT_DIR / "cartaos.db"

        self.db_path = Path(db_path)
        self.engine: Optional[Engine] = None
        self.metadata = MetaData()

        # Define database schema
        self._define_schema()

    def _define_schema(self):
        """Define the database schema using SQLAlchemy Core."""

        # User settings table
        self.user_settings = Table(
            'user_settings',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('key', String(255), unique=True, nullable=False),
            Column('value', Text, nullable=True),
            Column('description', Text, nullable=True),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        )

        # Projects table for future project-based organization
        self.projects = Table(
            'projects',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String(255), nullable=False),
            Column('description', Text, nullable=True),
            Column('root_path', String(512), nullable=False),
            Column('is_active', Boolean, default=True),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        )

        # Document queue table to track processing pipeline
        self.document_queue = Table(
            'document_queue',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('file_path', String(512), nullable=False),
            Column('original_name', String(255), nullable=False),
            Column('current_stage', String(50), nullable=False),  # 00_Inbox, 02_Triage, etc.
            Column('status', String(50), default='pending'),  # pending, processing, completed, failed
            Column('priority', Integer, default=0),
            Column('error_message', Text, nullable=True),
            Column('metadata', Text, nullable=True),  # JSON string for additional data
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            Column('processed_at', DateTime, nullable=True),
        )

    def get_engine(self) -> Engine:
        """Get or create the database engine."""
        if self.engine is None:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            # Create engine with SQLite
            db_url = f"sqlite:///{self.db_path}"
            self.engine = create_engine(db_url, echo=False)

            logger.info(f"Database engine created for: {self.db_path}")

        return self.engine

    def initialize_database(self) -> bool:
        """
        Initialize the database by creating all tables if they don't exist.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        try:
            engine = self.get_engine()

            # Create all tables
            self.metadata.create_all(engine)

            # Initialize with default settings if this is a fresh database
            self._initialize_default_settings()

            logger.info("Database initialized successfully")
            return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            return False

    def _initialize_default_settings(self):
        """Initialize default user settings if they don't exist."""
        default_settings = [
            ("gemini_api_key", None, "Google Gemini API key for AI processing"),
            ("obsidian_vault_path", None, "Path to Obsidian vault for summary storage"),
            ("watch_folder_enabled", "false", "Enable automatic folder watching"),
            ("default_summary_format", "markdown", "Default format for generated summaries"),
            ("auto_ocr_enabled", "true", "Automatically run OCR on scanned PDFs"),
            ("max_file_size_mb", "50", "Maximum file size in MB for processing"),
        ]
        for key, value, description in default_settings:
            if not self.get_setting(key):
                self.set_setting(key, value, description)

    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        engine = self.get_engine()
        conn = engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    # User Settings CRUD Operations

    def get_setting(self, key: str) -> Optional[str]:
        """
        Retrieve a user setting value by key.

        Args:
            key (str): Setting key name.

        Returns:
            Optional[str]: Setting value or None if not found.
        """
        try:
            with self.get_connection() as conn:
                stmt = select(self.user_settings.c.value).where(
                    self.user_settings.c.key == key
                )
                result = conn.execute(stmt).scalar()
                return result
        except SQLAlchemyError as e:
            logger.error(f"Failed to get setting '{key}': {e}")
            return None

    def set_setting(self, key: str, value: Optional[str], description: Optional[str] = None) -> bool:
        """
        Set or update a user setting using an atomic upsert operation.

        Args:
            key (str): Setting key name.
            value (Optional[str]): Setting value.
            description (Optional[str]): Optional description of the setting.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert

            with self.get_connection() as conn:
                # Use an atomic "upsert" operation
                stmt = sqlite_insert(self.user_settings).values(
                    key=key, value=value, description=description
                )

                # On conflict (key already exists), update the value and timestamp
                update_stmt = stmt.on_conflict_do_update(
                    index_elements=['key'],
                    set_=dict(value=value, updated_at=datetime.utcnow())
                )

                conn.execute(update_stmt)
                conn.commit()
                return True

        except SQLAlchemyError as e:
            logger.error(f"Failed to set setting '{key}': {e}")
            return False

    def get_all_settings(self) -> Dict[str, str]:
        """
        Retrieve all user settings as a dictionary.

        Returns:
            Dict[str, str]: Dictionary of all settings (key -> value).
        """
        try:
            with self.get_connection() as conn:
                stmt = select(self.user_settings.c.key, self.user_settings.c.value)
                results = conn.execute(stmt).fetchall()
                return {row.key: row.value for row in results if row.value is not None}
        except SQLAlchemyError as e:
            logger.error(f"Failed to get all settings: {e}")
            return {}

    def delete_setting(self, key: str) -> bool:
        """
        Delete a user setting.

        Args:
            key (str): Setting key to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with self.get_connection() as conn:
                stmt = delete(self.user_settings).where(self.user_settings.c.key == key)
                conn.execute(stmt)
                conn.commit()
                return True
        except SQLAlchemyError as e:
            logger.error(f"Failed to delete setting '{key}': {e}")
            return False

    # Document Queue CRUD Operations

    def add_document_to_queue(
        self, 
        file_path: str, 
        original_name: str, 
        current_stage: str, 
        priority: int = 0,
        metadata: Optional[str] = None
    ) -> Optional[int]:
        """
        Add a document to the processing queue.

        Args:
            file_path (str): Full path to the document file.
            original_name (str): Original filename.
            current_stage (str): Current pipeline stage (e.g., '00_Inbox').
            priority (int): Processing priority (higher = more urgent).
            metadata (Optional[str]): JSON metadata string.

        Returns:
            Optional[int]: Document ID if successful, None otherwise.
        """
        try:
            with self.get_connection() as conn:
                stmt = insert(self.document_queue).values(
                    file_path=file_path,
                    original_name=original_name,
                    current_stage=current_stage,
                    priority=priority,
                    metadata=metadata
                )
                result = conn.execute(stmt)
                conn.commit()
                return result.lastrowid
        except SQLAlchemyError as e:
            logger.error(f"Failed to add document to queue: {e}")
            return None

    def get_documents_by_stage(self, stage: str) -> List[Dict[str, Any]]:
        """
        Get all documents in a specific processing stage.

        Args:
            stage (str): Pipeline stage name.

        Returns:
            List[Dict[str, Any]]: List of document records.
        """
        try:
            with self.get_connection() as conn:
                stmt = (
                    select(self.document_queue)
                    .where(self.document_queue.c.current_stage == stage)
                    .order_by(self.document_queue.c.priority.desc(), self.document_queue.c.created_at)
                )
                results = conn.execute(stmt).fetchall()
                return [dict(row._mapping) for row in results]
        except SQLAlchemyError as e:
            logger.error(f"Failed to get documents by stage '{stage}': {e}")
            return []


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(db_path: Optional[Path] = None) -> DatabaseManager:
    """
    Get the global database manager instance.

    Args:
        db_path (Optional[Path]): Database path for initialization (used only on first call).

    Returns:
        DatabaseManager: The database manager instance.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
        _db_manager.initialize_database()
    return _db_manager
