# -*- coding: utf-8 -*-
# backend/tests/test_database.py

"""
Unit tests for the database module.

Tests all CRUD operations and database functionality using in-memory SQLite
for fast and isolated testing.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

from cartaos.database import DatabaseManager, get_database_manager


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
def db_manager(temp_db_path):
    """Fixture that provides a DatabaseManager instance with a temporary database."""
    manager = DatabaseManager(temp_db_path)
    manager.initialize_database()
    return manager


@pytest.fixture
def in_memory_db():
    """Fixture that provides an in-memory database for fast testing."""
    manager = DatabaseManager(":memory:")
    manager.initialize_database()
    return manager


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    def test_database_initialization(self, temp_db_path):
        """Test that database is properly initialized."""
        manager = DatabaseManager(temp_db_path)

        # Initially, database file shouldn't exist
        assert not temp_db_path.exists()

        # After initialization, it should exist
        success = manager.initialize_database()
        assert success
        assert temp_db_path.exists()

        # Database should contain the expected tables
        engine = manager.get_engine()
        with engine.connect() as conn:
            # Check if tables exist by querying sqlite_master
            result = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            table_names = {row[0] for row in result}

            expected_tables = {'user_settings', 'projects', 'document_queue'}
            assert expected_tables.issubset(table_names)

    def test_default_settings_initialization(self, in_memory_db):
        """Test that default settings are properly initialized."""
        # Check that some expected default settings exist
        expected_defaults = [
            "gemini_api_key",
            "obsidian_vault_path", 
            "watch_folder_enabled",
            "default_summary_format",
            "auto_ocr_enabled",
            "max_file_size_mb"
        ]

        for key in expected_defaults:
            value = in_memory_db.get_setting(key)
            # Setting should exist (even if value is None)
            assert value is not None or in_memory_db.get_setting(key) == ""

    def test_setting_crud_operations(self, in_memory_db):
        """Test CRUD operations for user settings."""
        db = in_memory_db

        # Test setting a new value
        success = db.set_setting("test_key", "test_value", "Test description")
        assert success

        # Test retrieving the value
        value = db.get_setting("test_key")
        assert value == "test_value"

        # Test updating an existing value
        success = db.set_setting("test_key", "updated_value")
        assert success

        value = db.get_setting("test_key")
        assert value == "updated_value"

        # Test getting all settings
        all_settings = db.get_all_settings()
        assert "test_key" in all_settings
        assert all_settings["test_key"] == "updated_value"

        # Test deleting a setting
        success = db.delete_setting("test_key")
        assert success

        value = db.get_setting("test_key")
        assert value is None

    def test_setting_nonexistent_key(self, in_memory_db):
        """Test retrieving a non-existent setting."""
        value = in_memory_db.get_setting("nonexistent_key")
        assert value is None

    def test_setting_with_none_value(self, in_memory_db):
        """Test setting a None value."""
        success = in_memory_db.set_setting("null_key", None, "Null test")
        assert success

        value = in_memory_db.get_setting("null_key")
        assert value is None

    def test_setting_with_empty_string(self, in_memory_db):
        """Test setting an empty string value."""
        success = in_memory_db.set_setting("empty_key", "", "Empty test")
        assert success

        value = in_memory_db.get_setting("empty_key")
        assert value == ""

    def test_setting_with_special_characters(self, in_memory_db):
        """Test setting values with special characters."""
        special_value = "!@#$%^&*()_+-={}[]|\\:;\"'<>?,./"
        success = in_memory_db.set_setting("special_key", special_value)
        assert success

        value = in_memory_db.get_setting("special_key")
        assert value == special_value

    def test_setting_with_unicode(self, in_memory_db):
        """Test setting values with Unicode characters."""
        unicode_value = "测试 🔥 café naïve résumé"
        success = in_memory_db.set_setting("unicode_key", unicode_value)
        assert success

        value = in_memory_db.get_setting("unicode_key")
        assert value == unicode_value


class TestDocumentQueue:
    """Test cases for document queue operations."""

    def test_add_document_to_queue(self, in_memory_db):
        """Test adding a document to the processing queue."""
        db = in_memory_db

        doc_id = db.add_document_to_queue(
            file_path="/path/to/test.pdf",
            original_name="test.pdf", 
            current_stage="00_Inbox",
            priority=1,
            metadata='{"type": "research_paper"}'
        )

        assert doc_id is not None
        assert isinstance(doc_id, int)
        assert doc_id > 0

    def test_get_documents_by_stage(self, in_memory_db):
        """Test retrieving documents by processing stage."""
        db = in_memory_db

        # Add some test documents
        doc_id_1 = db.add_document_to_queue(
            "/path/to/doc1.pdf", "doc1.pdf", "00_Inbox", priority=2
        )
        doc_id_2 = db.add_document_to_queue(
            "/path/to/doc2.pdf", "doc2.pdf", "00_Inbox", priority=1
        )
        doc_id_3 = db.add_document_to_queue(
            "/path/to/doc3.pdf", "doc3.pdf", "02_Triage", priority=3
        )

        # Get documents by stage
        inbox_docs = db.get_documents_by_stage("00_Inbox")
        triage_docs = db.get_documents_by_stage("02_Triage")

        # Should have 2 documents in inbox, 1 in triage
        assert len(inbox_docs) == 2
        assert len(triage_docs) == 1

        # Documents should be ordered by priority (desc) then created_at
        assert inbox_docs[0]["priority"] >= inbox_docs[1]["priority"]

        # Check document data
        assert inbox_docs[0]["original_name"] in ["doc1.pdf", "doc2.pdf"]
        assert triage_docs[0]["original_name"] == "doc3.pdf"
        assert triage_docs[0]["current_stage"] == "02_Triage"

    def test_get_documents_empty_stage(self, in_memory_db):
        """Test getting documents from a stage with no documents."""
        docs = in_memory_db.get_documents_by_stage("99_NonExistent")
        assert docs == []

    def test_document_metadata_json(self, in_memory_db):
        """Test storing and retrieving JSON metadata."""
        db = in_memory_db

        metadata = {
            "author": "John Doe",
            "subject": "Machine Learning", 
            "pages": 42,
            "tags": ["AI", "research", "2024"]
        }

        doc_id = db.add_document_to_queue(
            "/path/to/ml_paper.pdf",
            "ml_paper.pdf",
            "00_Inbox", 
            metadata=json.dumps(metadata)
        )

        docs = db.get_documents_by_stage("00_Inbox")
        assert len(docs) == 1

        stored_metadata = json.loads(docs[0]["metadata"])
        assert stored_metadata == metadata

    def test_document_default_values(self, in_memory_db):
        """Test that documents are created with proper default values."""
        db = in_memory_db

        doc_id = db.add_document_to_queue(
            "/path/to/simple.pdf",
            "simple.pdf", 
            "00_Inbox"
        )

        docs = db.get_documents_by_stage("00_Inbox")
        doc = docs[0]

        # Check default values
        assert doc["status"] == "pending"
        assert doc["priority"] == 0
        assert doc["error_message"] is None
        assert doc["processed_at"] is None
        assert doc["created_at"] is not None
        assert doc["updated_at"] is not None


class TestGlobalDatabaseManager:
    """Test cases for the global database manager function."""

    def test_get_database_manager_singleton(self, temp_db_path):
        """Test that get_database_manager returns a singleton."""
        # Reset the global manager
        import cartaos.database
        cartaos.database._db_manager = None

        # Get manager twice with the same path
        manager1 = get_database_manager(temp_db_path)
        manager2 = get_database_manager()

        # Should be the same instance
        assert manager1 is manager2
        assert manager1.db_path == temp_db_path

    def test_database_file_creation(self, temp_db_path):
        """Test that the database file is created when using global manager."""
        # Reset the global manager
        import cartaos.database
        cartaos.database._db_manager = None

        # Database file shouldn't exist initially
        assert not temp_db_path.exists()

        # Get manager (should create and initialize database)
        manager = get_database_manager(temp_db_path)

        # Database file should now exist
        assert temp_db_path.exists()

        # Should be able to perform operations
        success = manager.set_setting("test", "value")
        assert success

        value = manager.get_setting("test")
        assert value == "value"
