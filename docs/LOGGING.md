# Logging in CartaOS

This document outlines the logging standards and practices for the CartaOS project.

## Table of Contents
- [Logging Levels](#logging-levels)
- [Log Format](#log-format)
- [Usage](#usage)
- [Best Practices](#best-practices)
- [Configuration](#configuration)
- [Log Aggregation](#log-aggregation)

## Logging Levels

CartaOS uses the standard Python logging levels:

| Level     | When to Use |
|-----------|-------------|
| DEBUG     | Detailed information, typically of interest only when diagnosing problems |
| INFO      | Confirmation that things are working as expected |
| WARNING   | An indication that something unexpected happened, but the software is still working |
| ERROR     | Due to a more serious problem, the software has not been able to perform some function |
| CRITICAL  | A very serious error, indicating that the program itself may be unable to continue running |

## Log Format

Logs are structured in JSON format for easy parsing and integration with log management systems. Each log entry includes:

- `timestamp`: ISO 8601 formatted timestamp in UTC
- `level`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger`: Name of the logger
- `module`: Python module where the log was generated
- `function`: Function where the log was generated
- `line`: Line number where the log was generated
- `message`: The actual log message
- Additional context-specific fields

## Usage

### Basic Logging

```python
from cartaos.utils.logging_utils import get_logger

logger = get_logger(__name__)

def my_function():
    logger.debug("Detailed debug information")
    logger.info("Informational message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
```

### Logging with Context

```python
# Simple context
logger.info("Processing file", extra={"file_path": "/path/to/file", "size": 1024})

# Using LogContext for operations with duration tracking
with LogContext(logger, "Processing batch", batch_id=123, item_count=10) as ctx:
    # Your code here
    ctx.log("Processing item", item_id=456)
    # The context will automatically log completion with duration
```

## Best Practices

1. **Use Appropriate Log Levels**
   - DEBUG: For detailed debugging information
   - INFO: For normal operational messages
   - WARNING: For potentially problematic situations
   - ERROR: For serious problems that prevent normal operation
   - CRITICAL: For critical conditions that may cause application failure

2. **Include Context**
   - Always include relevant context in log messages
   - Use structured logging with key-value pairs
   - Avoid logging sensitive information

3. **Performance Considerations**
   - Use lazy evaluation for expensive log messages:
     ```python
     # Good
     logger.debug("Value: %s", expensive_function())
     
     # Bad (evaluates the function even if DEBUG is disabled)
     logger.debug(f"Value: {expensive_function()}")
     ```

## Configuration

Logging is configured in `cartaos/utils/logging_utils.py`. The default configuration:

- Logs to console in development
- Logs to both console and file in production
- Uses JSON formatting for structured logging
- Rotates log files when they reach 10MB
- Keeps 5 backup log files

## Log Aggregation

For production environments, it's recommended to use a log aggregation service. The JSON log format is compatible with most log management systems including:

- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- Graylog
- AWS CloudWatch Logs

### Example: ELK Stack Configuration

1. Configure Filebeat to collect logs:
   ```yaml
   filebeat.inputs:
   - type: log
     paths:
       - /var/log/cartaos/*.log
     json.keys_under_root: true
     json.add_error_key: true
     json.message_key: "message"
   
   output.logstash:
     hosts: ["logstash:5044"]
   ```

2. Configure Logstash to parse and forward logs:
   ```
   input {
     beats {
       port => 5044
     }
   }
   
   filter {
     if [@metadata][pipeline] {
       stdout { codec => rubydebug }
     }
   }
   
   output {
     elasticsearch {
       hosts => ["elasticsearch:9200"]
       index => "cartaos-logs-%{+YYYY.MM.dd}"
     }
   }
   ```

## Monitoring and Alerts

Set up alerts based on log patterns and error rates. Example alerts:

- Multiple ERROR or CRITICAL logs within a short time period
- Authentication failures
- Unhandled exceptions
- High latency in API responses

## Testing Logging

When writing tests, you can capture and assert on log messages:

```python
def test_logging(caplog):
    from cartaos.utils.logging_utils import get_logger
    
    logger = get_logger("test_logger")
    logger.info("Test message", extra={"key": "value"})
    
    assert "Test message" in caplog.text
    assert any(record.extra.get("key") == "value" for record in caplog.records)
```

## Troubleshooting

### Missing Logs
- Check log level configuration
- Verify log file permissions
- Ensure log directory exists

### Corrupted Log Files
- Check for incomplete JSON objects
- Verify log rotation is working correctly
- Ensure enough disk space is available

### Performance Issues
- Check for excessive DEBUG logging in production
- Verify log rotation settings
- Consider asynchronous logging for high-volume applications
