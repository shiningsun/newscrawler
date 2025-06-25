# Scripts Directory

This directory contains utility scripts for managing and testing the news crawler application.

## Database Management Scripts

### `db_manage.py`
**Purpose**: Interactive database management utility
**Usage**: `python scripts/db_manage.py`
**Features**:
- Show database statistics
- Display recent articles
- Search articles by keywords
- Clean up old articles
- Reset database

### `setup_database.py`
**Purpose**: Initialize database tables
**Usage**: `python scripts/setup_database.py`
**Features**:
- Create all necessary database tables
- Drop existing tables (with confirmation)
- Test database connection

### `add_domain_column.py`
**Purpose**: Add domain column to articles table
**Usage**: `python scripts/add_domain_column.py`
**Features**:
- Adds a 'domain' column to the articles table
- Useful for database schema migrations

### `populate_domains.py`
**Purpose**: Populate domain column for existing articles
**Usage**: `python scripts/populate_domains.py`
**Features**:
- Extracts domain from article URLs
- Updates existing articles with domain information
- Useful after adding the domain column

### `remove_excluded_domains.py`
**Purpose**: Remove articles from excluded domains
**Usage**: `python scripts/remove_excluded_domains.py`
**Features**:
- Removes articles from domains in the exclusion list
- Helps maintain clean data

### `force_fix_db_schema.py`
**Purpose**: Force fix database schema issues
**Usage**: `python scripts/force_fix_db_schema.py`
**Features**:
- Fixes common database schema problems
- Handles data type mismatches
- Updates column constraints

## Testing Scripts

### `test_logging.py`
**Purpose**: Test logging configuration
**Usage**: `python scripts/test_logging.py`
**Features**:
- Demonstrates logging setup
- Tests Google News crawler with logging
- Shows log output to console and files

### `test_extractor.py`
**Purpose**: Test article content extraction
**Usage**: `python scripts/test_extractor.py`
**Features**:
- Tests article content extraction from URLs
- Demonstrates extraction capabilities
- Shows extraction results

### `test_db_connection.py`
**Purpose**: Test database connectivity
**Usage**: `python scripts/test_db_connection.py`
**Features**:
- Tests database connection
- Verifies database configuration
- Shows connection status

## Running Scripts

All scripts are designed to be run from the project root directory:

```bash
# From the project root (C:\code\newsCrawler)
python scripts/db_manage.py
python scripts/test_logging.py
python scripts/setup_database.py
```

## Script Requirements

All scripts automatically add the project root to the Python path, so they can import modules from the main application. Make sure you have:

1. **Virtual environment activated** (if using one)
2. **Dependencies installed** (`pip install -r requirements.txt`)
3. **Database configured** (check `config.py` and `database.py`)

## Script Categories

### **Essential Scripts** (for setup and maintenance)
- `setup_database.py` - Required for initial setup
- `db_manage.py` - Useful for ongoing maintenance

### **Migration Scripts** (for database schema changes)
- `add_domain_column.py`
- `populate_domains.py`
- `force_fix_db_schema.py`

### **Utility Scripts** (for data management)
- `remove_excluded_domains.py`

### **Testing Scripts** (for development and debugging)
- `test_logging.py`
- `test_extractor.py`
- `test_db_connection.py`

## Notes

- All scripts include proper error handling and logging
- Scripts are designed to be safe and include confirmation prompts for destructive operations
- Most scripts can be run multiple times safely
- Check individual script documentation for specific usage instructions 