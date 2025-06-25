# Logging Configuration

This project uses a centralized logging configuration that writes logs to both console and files with automatic rotation.

## Overview

The logging system provides:
- **Console output**: Simple format for immediate feedback
- **File logging**: Detailed format with full context for debugging
- **Error logging**: Separate file for errors and critical issues
- **Automatic rotation**: Prevents log files from growing too large
- **Configurable levels**: Different log levels for different needs

## Files

- `logging_config.py`: Centralized logging configuration module
- `logs/`: Directory containing log files
  - `news_crawler.log`: General application logs
  - `news_crawler_errors.log`: Error and critical logs only

## Usage

### Basic Setup

```python
from logging_config import setup_logging, get_logger

# Initialize logging
setup_logging(log_level="INFO", app_name="my_app")
logger = get_logger(__name__)

# Use the logger
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred")
```

### Configuration Options

```python
setup_logging(
    log_level="INFO",           # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_dir="logs",             # Directory for log files
    app_name="news_crawler",    # Name for log file naming
    enable_console=True,        # Enable console output
    enable_file=True,           # Enable general log file
    enable_error_file=True      # Enable separate error log file
)
```

### Quick Setup

For simple applications:

```python
from logging_config import quick_setup, get_logger

quick_setup("DEBUG")  # Sets up logging with DEBUG level
logger = get_logger(__name__)
```

## Log Levels

- **DEBUG**: Detailed information for debugging
- **INFO**: General information about program execution
- **WARNING**: Indicates a potential problem
- **ERROR**: A more serious problem
- **CRITICAL**: A critical problem that may prevent the program from running

## Log Formats

### Console Format
```
2025-06-24 19:33:31,540 - INFO - Test message
```

### File Format (Detailed)
```
2025-06-24 19:33:31,540 - test - INFO - test_logging.py:25 - main - Test message
```

## File Rotation

Log files are automatically rotated when they reach:
- **General log**: 10MB with 5 backup files
- **Error log**: 5MB with 3 backup files

## Integration with Existing Code

### Main Application (main.py)
The main FastAPI application uses the logging configuration automatically.

### Database Management (db_manage.py)
The database management script includes logging for all operations.

### Google News Crawler
The crawler includes comprehensive logging for:
- Category matching
- Article parsing
- Full coverage processing
- Error handling

## Testing

Run the test script to see logging in action:

```bash
python test_logging.py
```

This will:
1. Set up logging with DEBUG level
2. Run the Google News crawler
3. Log all operations to both console and files
4. Show detailed debugging information

## Viewing Logs

### Console Output
Logs appear in real-time in the console when running the application.

### Log Files
Check the `logs/` directory for log files:
- `logs/news_crawler.log`: All application logs
- `logs/news_crawler_errors.log`: Only errors and critical issues

### Log Analysis
You can use standard tools to analyze logs:
```bash
# View recent logs
tail -f logs/news_crawler.log

# Search for errors
grep "ERROR" logs/news_crawler.log

# Count log entries by level
grep -c "INFO" logs/news_crawler.log
```

## Best Practices

1. **Use appropriate log levels**: Don't log everything as INFO
2. **Include context**: Use structured logging with relevant information
3. **Handle exceptions**: Always log exceptions with `exc_info=True`
4. **Monitor log sizes**: Check log rotation is working properly
5. **Review error logs**: Regularly check the error log file

## Customization

You can customize the logging configuration by modifying `logging_config.py`:

- Change log formats
- Adjust file sizes and rotation
- Add new handlers (e.g., email, syslog)
- Modify log levels for specific modules

## Troubleshooting

### No Logs Appearing
- Check that `setup_logging()` is called before any logging
- Verify the log directory exists and is writable
- Ensure log level is appropriate

### Large Log Files
- Check if rotation is working
- Review log level (DEBUG creates many logs)
- Consider filtering verbose third-party libraries

### Missing Error Logs
- Verify error log file is enabled
- Check that errors are being logged at ERROR level or higher
- Ensure exception handling includes logging 