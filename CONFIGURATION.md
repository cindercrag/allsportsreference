# Configuration Management

This document explains how to configure the All Sports Reference application using environment variables and configuration files.

## Overview

The application uses a flexible configuration system that:
- Loads settings from `.env` files
- Provides sensible defaults for all settings
- Supports environment variable overrides
- Validates configuration on startup
- Hides sensitive values in logs and debug output

## Configuration Files

### `.env` File
Create a `.env` file in the project root to customize settings:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sportsdb
DB_USER=postgres
DB_PASSWORD=your_secure_password

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE_MAX_SIZE=10 MB
LOG_FILE_RETENTION=30 days
ERROR_LOG_MAX_SIZE=5 MB
ERROR_LOG_RETENTION=60 days

# Data Directory Configuration
DATA_DIR=data
LOGS_DIR=logs

# Application Settings
APP_NAME=All Sports Reference
DEBUG=false
```

### `.env.example`
The `.env.example` file contains all available configuration options with default values. Copy this file to `.env` and modify as needed.

## Configuration Options

### Database Settings
- `DB_HOST`: Database server hostname (default: 'localhost')
- `DB_PORT`: Database server port (default: 5432)
- `DB_NAME`: Database name (default: 'sportsdb')
- `DB_USER`: Database username (default: 'postgres')
- `DB_PASSWORD`: Database password (default: 'password')

### Logging Settings
- `LOG_LEVEL`: Minimum log level (default: 'INFO')
  - Valid values: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_FILE_MAX_SIZE`: Maximum size before log rotation (default: '10 MB')
- `LOG_FILE_RETENTION`: How long to keep old log files (default: '30 days')
- `ERROR_LOG_MAX_SIZE`: Maximum size for error log (default: '5 MB')
- `ERROR_LOG_RETENTION`: Retention for error logs (default: '60 days')

### Directory Settings
- `DATA_DIR`: Directory for exported CSV files (default: 'data')
- `LOGS_DIR`: Directory for log files (default: 'logs')

### Application Settings
- `APP_NAME`: Application display name (default: 'All Sports Reference')
- `DEBUG`: Enable debug mode (default: false)
  - When true, shows configuration details on startup

### Sports URLs (Advanced)
- `NFL_BASE_URL`: NFL reference site base URL
- `NBA_BASE_URL`: NBA reference site base URL

## Usage Examples

### Basic Usage
```python
from config import config

# Get database configuration
db_config = config.database_config
db = SportsDatabase(**db_config)

# Or use the convenience method
db = SportsDatabase.from_config()
```

### Custom Configuration
```python
from config import Config

# Load from specific .env file
config = Config('/path/to/custom.env')

# Override specific values
db = SportsDatabase(
    host=config.db_host,
    password='different_password'
)
```

### Environment Variables
You can also set configuration via environment variables:
```bash
export DB_HOST=production-db.example.com
export LOG_LEVEL=WARNING
python app/main.py
```

## Security Considerations

1. **Never commit `.env` files to version control**
   - `.env` is already in `.gitignore`
   - Use `.env.example` for documentation

2. **Use strong passwords in production**
   - Generate random passwords for database access
   - Consider using environment-specific credentials

3. **Validate configuration**
   - The application validates configuration on startup
   - Invalid settings will prevent startup with clear error messages

4. **Hide sensitive values**
   - Debug output automatically hides passwords
   - Use `config.print_config(hide_sensitive=True)` for debugging

## Configuration Validation

The application automatically validates configuration:
- Database port must be a valid integer
- Log level must be valid (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Directories will be created if they don't exist
- Configuration errors prevent application startup

## Development vs Production

### Development
```bash
# .env for development
DEBUG=true
LOG_LEVEL=DEBUG
DB_HOST=localhost
```

### Production
```bash
# .env for production
DEBUG=false
LOG_LEVEL=INFO
DB_HOST=prod-db.example.com
LOG_FILE_RETENTION=90 days
```

## Troubleshooting

### Configuration Not Loading
1. Ensure `.env` file is in the project root
2. Check file permissions (must be readable)
3. Verify syntax (no spaces around =)

### Database Connection Issues
1. Verify database settings in `.env`
2. Check if PostgreSQL is running
3. Validate credentials and permissions

### Log Files Not Created
1. Check `LOGS_DIR` setting
2. Verify write permissions to logs directory
3. Check disk space availability

## Testing Configuration

Run the configuration test:
```bash
python app/config.py
```

This will display all current settings and validate the configuration.
