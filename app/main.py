#!/usr/bin/env python3
"""
All Sports Reference - Main Application Entry Point

A Python application for scraping and analyzing sports data from reference websites.
Currently supports NFL and NBA data with teams, schedules, and statistics.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import configuration
from config import config
from src.nfl import constants as nfl_constants
from src.nba import constants as nba_constants
from src.utils.common import _todays_date


def setup_logging():
    """
    Configure loguru logging for the application using configuration values.
    """
    # Remove default logger
    logger.remove()
    
    # Get logging configuration
    log_config = config.get_logging_config()
    logs_dir = log_config['logs_dir']
    
    # Ensure logs directory exists
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Add console logger with custom format
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_config['level'],
        colorize=True
    )
    
    # Add file logger for errors and debug info
    # Main application log
    logger.add(
        logs_dir / "allsportsreference.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_config['level'],
        rotation=log_config['log_file_max_size'],
        retention=log_config['log_file_retention'],
        compression="gz",
        enqueue=True
    )
    
    # Error-only log
    logger.add(
        logs_dir / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=log_config['error_log_max_size'],
        retention=log_config['error_log_retention'],
        compression="gz",
        enqueue=True
    )
    
    logger.info("Logging configured successfully")


def main():
    """
    Main entry point for the All Sports Reference application.
    """
    logger.info(f"Starting {config.app_name}")
    
    print("=" * 60)
    print(f"Welcome to {config.app_name}")
    print("=" * 60)
    print(f"Current date: {_todays_date()}")
    print()
    
    logger.debug(f"Application started at {datetime.now()}")
    
    # Display supported sports
    print("Supported Sports:")
    print(f"- {nfl_constants.SPORT_CONFIG['display_name']} ({nfl_constants.SPORT_CONFIG['name'].upper()})")
    print(f"- {nba_constants.SPORT_CONFIG['display_name']} ({nba_constants.SPORT_CONFIG['name'].upper()})")
    print()
    
    logger.info(f"Loaded {len([nfl_constants, nba_constants])} sport configurations")
    
    # Display available functionality
    print("Available features:")
    features = [
        "Team data scraping",
        "Season statistics",
        "Game schedules and results",
        "Player information",
        "Boxscores",
        "Automated CSV export with organized file structure",
        "Column glossaries",
        "PostgreSQL database integration",
        "Comprehensive logging",
        "Environment-based configuration"
    ]
    
    for feature in features:
        print(f"- {feature}")
    print()
    
    # Example usage - you can expand this section
    print("Example URLs configured:")
    print("NFL:")
    print(f"  - Season page: {nfl_constants.get_url('season_page', year=2024)}")
    print(f"  - Patriots schedule: {nfl_constants.get_url('schedule', team='NE', year=2024)}")
    print("NBA:")
    print(f"  - Season page: {nba_constants.get_url('season_page', year=2024)}")
    print(f"  - Lakers schedule: {nba_constants.get_url('schedule', team='LAL', year=2024)}")
    print()
    
    logger.success("Application initialization completed successfully")
    
    # TODO: Add interactive menu or command-line argument parsing
    print("Note: This is a basic entry point. Extend with specific functionality as needed.")
    print(f"📝 Logs are being written to the '{config.logs_dir}' directory")
    print(f"📁 Data will be saved to the '{config.data_dir}' directory")
    print(f"⚙️  Configuration loaded from environment variables")
    
    if config.debug:
        print("\n🐛 Debug mode is enabled")
        config.print_config(hide_sensitive=True)


if __name__ == "__main__":
    try:
        # Validate configuration first
        if not config.validate_config():
            print("❌ Configuration validation failed. Please check your .env file.")
            sys.exit(1)
            
        # Setup logging using configuration
        setup_logging()
        
        # Run main application
        main()
        
        logger.info("Application finished successfully")
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.exception(f"Unhandled exception: {e}")
        sys.exit(1)
        logger.info("Application finished successfully")
    except KeyboardInterrupt:
        logger.warning("Application interrupted by user")
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application failed with error: {e}")
        logger.exception("Full exception details:")
        print(f"An error occurred: {e}")
        sys.exit(1)