"""
Configuration management for All Sports Reference application.

This module handles loading configuration from environment variables
and provides default values for all application settings.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class Config:
    """
    Configuration class that loads settings from environment variables
    with sensible defaults.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration by loading environment variables.
        
        Parameters
        ----------
        env_file : str, optional
            Path to .env file to load. If None, looks for .env in current directory.
        """
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env file in current directory or parent directories
            current_dir = Path.cwd()
            for path in [current_dir] + list(current_dir.parents):
                env_path = path / '.env'
                if env_path.exists():
                    load_dotenv(env_path)
                    break
    
    # Database Configuration
    @property
    def db_host(self) -> str:
        return os.getenv('DB_HOST', 'localhost')
    
    @property
    def db_port(self) -> int:
        return int(os.getenv('DB_PORT', '5432'))
    
    @property
    def db_name(self) -> str:
        return os.getenv('DB_NAME', 'sportsdb')
    
    @property
    def db_user(self) -> str:
        return os.getenv('DB_USER', 'postgres')
    
    @property
    def db_password(self) -> str:
        return os.getenv('DB_PASSWORD', 'password')
    
    @property
    def database_config(self) -> Dict[str, Any]:
        """Get complete database configuration as dictionary."""
        return {
            'host': self.db_host,
            'port': self.db_port,
            'database': self.db_name,
            'user': self.db_user,
            'password': self.db_password
        }
    
    # Logging Configuration
    @property
    def log_level(self) -> str:
        return os.getenv('LOG_LEVEL', 'INFO').upper()
    
    @property
    def log_file_max_size(self) -> str:
        return os.getenv('LOG_FILE_MAX_SIZE', '10 MB')
    
    @property
    def log_file_retention(self) -> str:
        return os.getenv('LOG_FILE_RETENTION', '30 days')
    
    @property
    def error_log_max_size(self) -> str:
        return os.getenv('ERROR_LOG_MAX_SIZE', '5 MB')
    
    @property
    def error_log_retention(self) -> str:
        return os.getenv('ERROR_LOG_RETENTION', '60 days')
    
    # Directory Configuration
    @property
    def data_dir(self) -> Path:
        return Path(os.getenv('DATA_DIR', 'data'))
    
    @property
    def logs_dir(self) -> Path:
        return Path(os.getenv('LOGS_DIR', 'logs'))
    
    # Application Settings
    @property
    def app_name(self) -> str:
        return os.getenv('APP_NAME', 'All Sports Reference')
    
    @property
    def debug(self) -> bool:
        return os.getenv('DEBUG', 'false').lower() in ('true', '1', 'yes', 'on')
    
    # Sports Reference URLs (with overrides)
    @property
    def nfl_base_url(self) -> str:
        return os.getenv('NFL_BASE_URL', 'https://www.pro-football-reference.com')
    
    @property
    def nba_base_url(self) -> str:
        return os.getenv('NBA_BASE_URL', 'http://www.basketball-reference.com')
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get complete logging configuration.
        
        Returns
        -------
        Dict[str, Any]
            Logging configuration dictionary
        """
        return {
            'level': self.log_level,
            'logs_dir': self.logs_dir,
            'log_file_max_size': self.log_file_max_size,
            'log_file_retention': self.log_file_retention,
            'error_log_max_size': self.error_log_max_size,
            'error_log_retention': self.error_log_retention
        }
    
    def validate_config(self) -> bool:
        """
        Validate that all required configuration is present and valid.
        
        Returns
        -------
        bool
            True if configuration is valid
        """
        try:
            # Validate database port is a number
            if not isinstance(self.db_port, int) or self.db_port <= 0:
                raise ValueError(f"Invalid database port: {self.db_port}")
            
            # Validate log level is valid
            valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.log_level not in valid_log_levels:
                raise ValueError(f"Invalid log level: {self.log_level}. Must be one of {valid_log_levels}")
            
            # Validate directories can be created
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def print_config(self, hide_sensitive: bool = True) -> None:
        """
        Print current configuration (for debugging).
        
        Parameters
        ----------
        hide_sensitive : bool
            Whether to hide sensitive values like passwords
        """
        print("=" * 60)
        print(f"{self.app_name} Configuration")
        print("=" * 60)
        
        print("\nDatabase:")
        print(f"  Host: {self.db_host}")
        print(f"  Port: {self.db_port}")
        print(f"  Database: {self.db_name}")
        print(f"  User: {self.db_user}")
        if hide_sensitive:
            print(f"  Password: {'*' * len(self.db_password)}")
        else:
            print(f"  Password: {self.db_password}")
        
        print("\nLogging:")
        print(f"  Level: {self.log_level}")
        print(f"  Logs Directory: {self.logs_dir}")
        print(f"  Log File Size: {self.log_file_max_size}")
        print(f"  Log Retention: {self.log_file_retention}")
        print(f"  Error Log Size: {self.error_log_max_size}")
        print(f"  Error Retention: {self.error_log_retention}")
        
        print("\nDirectories:")
        print(f"  Data Directory: {self.data_dir}")
        print(f"  Logs Directory: {self.logs_dir}")
        
        print("\nApplication:")
        print(f"  App Name: {self.app_name}")
        print(f"  Debug Mode: {self.debug}")
        
        print("\nSports URLs:")
        print(f"  NFL Base URL: {self.nfl_base_url}")
        print(f"  NBA Base URL: {self.nba_base_url}")
        
        print("=" * 60)


# Global configuration instance
# This will be imported by other modules
config = Config()


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns
    -------
    Config
        The global configuration instance
    """
    return config


if __name__ == '__main__':
    # Demo/test the configuration
    config = Config()
    config.print_config(hide_sensitive=False)
    
    if config.validate_config():
        print("\n✅ Configuration is valid!")
    else:
        print("\n❌ Configuration validation failed!")
