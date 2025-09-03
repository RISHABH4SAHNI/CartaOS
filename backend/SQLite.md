# SQLite Database Integration for CartaOS

This document describes the SQLite database integration implementation for persistent configuration and state management in CartaOS.

## Overview

The SQLite integration provides a robust, persistent storage layer for application configuration, replacing the previous environment-variable-only approach while maintaining full backward compatibility.

## Architecture

### Core Components

1. **Database Layer** (`cartaos/database.py`)
   - SQLite database with SQLAlchemy Core
   - Tables: `user_settings`, `projects`, `document_queue`
   - CRUD operations for all data types

2. **Configuration Management** (`cartaos/config.py`)
   - `AppConfig`: Original environment-based configuration (unchanged)
   - `DatabaseConfig`: New database-backed configuration with env fallback

3. **Migration System** (`cartaos/config_migration.py`)
   - Utilities to migrate from environment variables to database
   - Backup and validation capabilities

4. **CLI Integration** (`cartaos/cli_database.py` + `cartaos/cli.py`)
   - Database management commands under `cartaos db`
   - Database options in main commands (e.g., `--use-database`)

## Usage

### Database Management

```bash
# Initialize database
cartaos db init

# Check database status  
cartaos db status

# Migrate existing configuration
cartaos db migrate

# Manage settings
cartaos db config set gemini_api_key "your-api-key"
cartaos db config list
cartaos db config get gemini_api_key
cartaos db config delete old_setting
```

### Using Database Configuration

```bash
# Use database-backed configuration
cartaos summarize document.pdf --use-database

# Specify custom database path
cartaos summarize document.pdf --use-database --db-path /path/to/custom.db

# Traditional environment-based (default behavior)
cartaos summarize document.pdf
```

## Database Schema

### user_settings
- `id`: Primary key
- `key`: Setting name (unique)
- `value`: Setting value (text)
- `description`: Setting description
- `created_at`, `updated_at`: Timestamps

### projects  
- `id`: Primary key
- `name`: Project name
- `description`: Project description
- `root_path`: Project root directory
- `is_active`: Active status
- `created_at`, `updated_at`: Timestamps

### document_queue
- `id`: Primary key
- `file_path`: Full path to document
- `original_name`: Original filename
- `current_stage`: Pipeline stage (00_Inbox, 02_Triage, etc.)
- `status`: Processing status (pending, processing, completed, failed)
- `priority`: Processing priority
- `error_message`: Error details (if any)
- `metadata`: JSON metadata
- `created_at`, `updated_at`, `processed_at`: Timestamps

## Configuration Settings

Default settings initialized in the database:

- `gemini_api_key`: Google Gemini API key for AI processing
- `obsidian_vault_path`: Path to Obsidian vault for summary storage
- `watch_folder_enabled`: Enable automatic folder watching
- `default_summary_format`: Default format for generated summaries
- `auto_ocr_enabled`: Automatically run OCR on scanned PDFs
- `max_file_size_mb`: Maximum file size in MB for processing

## Migration Process

The migration system automatically discovers environment variables and transfers them to the database:

```python
from cartaos.config_migration import migrate_env_to_database

# Perform complete migration
results = migrate_env_to_database(
    backup=True,        # Create backup before migration
    overwrite=False     # Don't overwrite existing database settings
)
```

Environment variable mapping:
- `GEMINI_API_KEY` → `gemini_api_key`
- `OBSIDIAN_VAULT_PATH` → `obsidian_vault_path`
- `CARTAOS_WATCH_FOLDER` → `watch_folder_enabled`
- `CARTAOS_MAX_FILE_SIZE` → `max_file_size_mb`
- `CARTAOS_SUMMARY_FORMAT` → `default_summary_format`
- `CARTAOS_AUTO_OCR` → `auto_ocr_enabled`

## Code Integration

### Using DatabaseConfig

```python
from cartaos.config import DatabaseConfig

# Create database-backed configuration
config = DatabaseConfig(fallback_to_env=True)

# Use with processor
from cartaos.processor import CartaOSProcessor
processor = CartaOSProcessor(pdf_path, config)
```

### Backwards Compatibility

Existing code using `AppConfig` continues to work unchanged:

```python
from cartaos.config import AppConfig

# Original environment-based configuration still works
config = AppConfig()
processor = CartaOSProcessor(pdf_path, config)
```

## Testing

Comprehensive test coverage includes:

1. **Unit Tests**
   - `test_database.py`: Database layer functionality
   - `test_database_config.py`: DatabaseConfig class
   - `test_sqlite_integration.py`: Full integration tests
   - `test_cli_database_integration.py`: CLI integration

2. **Test Categories**
   - Database CRUD operations
   - Configuration management
   - Migration utilities
   - CLI command functionality
   - Processor integration
   - Error handling and fallbacks

## File Structure

```
backend/
├── cartaos/
│   ├── database.py              # Database layer
│   ├── config.py                # Configuration classes  
│   ├── config_migration.py      # Migration utilities
│   ├── cli_database.py          # Database CLI commands
│   ├── cli.py                   # Main CLI (updated)
│   └── processor.py             # Processor (updated)
├── tests/
│   ├── test_database.py
│   ├── test_database_config.py
│   ├── test_sqlite_integration.py
│   └── test_cli_database_integration.py
├── pyproject.toml               # Dependencies (SQLAlchemy added)
└── DATABASE_INTEGRATION.md      # This documentation
```

## Performance Considerations

- Uses SQLite WAL mode for better concurrent access
- Connection pooling through SQLAlchemy
- In-memory database option for testing
- Lazy initialization of database connections

## Security Considerations

- Database file permissions follow OS security model
- No sensitive data stored in plain text (API keys should use keychain)
- SQL injection protection through SQLAlchemy Core
- Backup capabilities for configuration safety

## Future Enhancements

1. **Document Queue Management**
   - Track file processing states
   - Priority-based processing
   - Retry mechanisms for failed processing

2. **Project Management**
   - Project-based organization
   - Per-project configuration
   - Workspace isolation

3. **Advanced Features**
   - Configuration validation
   - Setting change history
   - Export/import capabilities
   - Database encryption options
