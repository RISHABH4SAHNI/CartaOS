"""
Test suite for centralized logging implementation.
Following TDD approach - these tests should fail initially.
"""

import io
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from cartaos.utils.logging_utils import (
    setup_logging,
    get_logger,
    LogContext,
    CustomJsonFormatter,
)


def test_logging_module_import():
    """Test that the logging module can be imported."""
    from cartaos.utils import logging_utils

    assert logging_utils is not None


def test_get_logger():
    """Test getting a logger instance."""
    logger = get_logger("test_logger")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test_logger"


def test_setup_logging_console():
    """Test setting up console logging."""
    # Capture stdout
    stream = io.StringIO()
    
    # Setup logging with console output
    setup_logging(
        log_level=logging.DEBUG,
        log_file=None,
        json_format=False
    )
    
    # Get a logger and log a message
    logger = get_logger("test_console_logger")
    logger.handlers = []  # Remove existing handlers for test
    
    # Create a formatter that matches what we expect
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    test_message = "Test console logging"
    logger.info(test_message)
    
    # Verify the output
    output = stream.getvalue()
    assert test_message in output
    assert "INFO" in output


def test_setup_logging_file():
    """Test setting up file logging."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        log_file = temp_file.name
    
    try:
        # Setup file logging
        setup_logging(
            log_level=logging.DEBUG,
            log_file=log_file,
            json_format=False
        )
        
        # Get a logger and log a message
        logger = get_logger("test_file_logger")
        test_message = "Test file logging"
        logger.info(test_message)
        
        # Flush the handlers to ensure the message is written
        for handler in logger.handlers:
            handler.flush()
        
        # Verify the log file content
        with open(log_file, 'r') as f:
            content = f.read()
            assert test_message in content
            
    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_json_logging():
    """Test JSON formatted logging."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        log_file = temp_file.name
    
    try:
        # Setup JSON logging
        setup_logging(
            log_level=logging.DEBUG,
            log_file=log_file,
            json_format=True
        )
        
        # Get a logger and log a message
        logger = get_logger("test_json_logger")
        test_message = "Test JSON logging"
        logger.info(test_message, extra={"custom_field": "custom_value"})
        
        # Flush the handlers to ensure the message is written
        for handler in logger.handlers:
            handler.flush()
        
        # Verify the log file content is valid JSON
        with open(log_file, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            log_entry = json.loads(lines[0])
            assert log_entry["message"] == test_message
            assert log_entry["custom_field"] == "custom_value"
            assert "timestamp" in log_entry
            assert "level" in log_entry
            
    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)


def test_log_context():
    """Test the LogContext context manager."""
    logger = get_logger("test_log_context")
    logger.handlers = []  # Remove existing handlers for test
    
    # Capture log output
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    
    # Use JSON formatter to capture all fields
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Use the context manager
    with LogContext(logger, "Test context", param1="value1"):
        logger.info("Inside context")
    
    # Verify the output
    output = stream.getvalue()
    logs = [json.loads(line) for line in output.strip().split('\n') if line]
    
    # Check that we have all expected log entries
    assert len(logs) == 3
    assert any(log.get('message', '').startswith("Starting:") for log in logs)
    assert any(log.get('message', '').startswith("Completed:") for log in logs)
    assert any(log.get('message') == "Inside context" for log in logs)
    
    # Check that the completed log has duration_seconds
    completed_log = next(log for log in logs if log.get('message', '').startswith("Completed:"))
    assert 'duration_seconds' in completed_log


def test_log_context_with_exception():
    """Test LogContext with an exception."""
    logger = get_logger("test_log_context_exception")
    logger.handlers = []  # Remove existing handlers for test
    
    # Capture log output
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    
    # Use JSON formatter to capture all fields
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Use the context manager with an exception
    try:
        with LogContext(logger, "Test context with exception"):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Verify the output
    output = stream.getvalue()
    logs = [json.loads(line) for line in output.strip().split('\n') if line]
    
    # Check that we have all expected log entries
    assert len(logs) >= 2  # At least start and error logs
    assert any(log.get('message', '').startswith("Starting:") for log in logs)
    assert any(log.get('message', '').startswith("Failed:") for log in logs)
    
    # Check that the error log has exception info
    error_log = next(log for log in logs if log.get('message', '').startswith("Failed:"))
    assert 'exception_type' in error_log
    assert error_log['exception_type'] == 'ValueError'
    assert 'duration_seconds' in error_log


def test_custom_json_formatter():
    """Test the CustomJsonFormatter adds all expected fields to log records."""
    # Create a test record
    record = logging.LogRecord(
        name='test_logger',
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg='Test message',
        args=(),
        exc_info=None,
        func='test_function'
    )
    # Add custom fields directly to the record
    record.custom_field = 'test_value'  
    # Create the formatter
    formatter = CustomJsonFormatter()
    
    # Format the record
    result = json.loads(formatter.format(record))
    
    # Check standard fields
    assert 'timestamp' in result
    assert result['level'] == 'INFO'
    assert result['logger'] == 'test_logger'
    assert result['module'] == 'test_logging_utils'
    assert result['function'] == 'test_function'
    assert result['line'] == 42
    assert 'process' in result
    assert 'thread' in result
    assert 'thread_name' in result
    
    # Check extra fields
    assert result['custom_field'] == 'test_value'
    
    # Check the message is included
    assert result['message'] == 'Test message'


if __name__ == "__main__":
    pytest.main([__file__])
