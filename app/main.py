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
from src.ncaaf import constants as ncaaf_constants
from src.ncaab import constants as ncaab_constants
from src.nhl import constants as nhl_constants
from src.utils.common import _todays_date
from src.nfl.teams import Teams


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
    sports_configs = {
        'NFL': nfl_constants.NFL_CONFIG,
        'NBA': nba_constants.NBA_CONFIG,
        'NCAAF': ncaaf_constants.NCAAF_CONFIG,
        'NCAAB (Men)': {**ncaab_constants.NCAAB_CONFIG, 'display_name': 'NCAA Men\'s Basketball'},
        'NCAAB (Women)': {**ncaab_constants.NCAAB_CONFIG, 'display_name': 'NCAA Women\'s Basketball'},
        'NHL': nhl_constants.NHL_CONFIG
    }
    
    for sport_name, sport_config in sports_configs.items():
        print(f"- {sport_config['display_name']} ({sport_name})")
    print()
    
    logger.info(f"Loaded {len(sports_configs)} sport configurations")
    
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
    print("NCAAF:")
    print(f"  - Season page: {ncaaf_constants.get_url('season_page', year=2024)}")
    print(f"  - Alabama schedule: {ncaaf_constants.get_url('schedule', team='alabama', year=2024)}")
    print("NCAAB (Men's):")
    print(f"  - Season page: {ncaab_constants.get_url('season_page', league='men', year=2024)}")
    print(f"  - Duke schedule: {ncaab_constants.get_url('schedule', team='duke', year=2024)}")
    print(f"  - Basic stats: {ncaab_constants.get_url('basic_stats', league='men', year=2024)}")
    print("NCAAB (Women's):")
    print(f"  - Season page: {ncaab_constants.get_url('season_page', league='women', year=2024)}")
    print(f"  - UConn schedule: {ncaab_constants.get_url('schedule', team='connecticut', year=2024)}")
    print(f"  - Basic stats: {ncaab_constants.get_url('basic_stats', league='women', year=2024)}")
    print("NHL:")
    print(f"  - Season page: {nhl_constants.get_url('season_page', year=2024)}")
    print(f"  - Bruins schedule: {nhl_constants.get_url('schedule', team='BOS', year=2024)}")
    print()
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

    # Example of using Teams class to get NFL teams
    try:
        teams = Teams(2024)
        print("\n🏈 NFL Teams for 2024:")
        print(f"{teams}")
        
        # Demonstrate individual team access by abbreviation
        print("📊 Individual Team Access Examples:")
        print("=" * 50)
        
        # Access specific teams by abbreviation
        eagles = teams.PHI
        bills = teams.BUF
        lions = teams.DET
        chiefs = teams.KAN
        
        print(f"🦅 {eagles.get('Team', eagles.get('Tm', 'Unknown'))} ({eagles['Abbrev']}): {eagles.get('Wins', eagles.get('W', 'N/A'))}-{eagles.get('Losses', eagles.get('L', 'N/A'))} record, {eagles.get('Points For', eagles.get('PF', 'N/A'))} PF, {eagles.get('Points Allowed', eagles.get('PA', 'N/A'))} PA")
        print(f"🦬 {bills.get('Team', bills.get('Tm', 'Unknown'))} ({bills['Abbrev']}): {bills.get('Wins', bills.get('W', 'N/A'))}-{bills.get('Losses', bills.get('L', 'N/A'))} record, {bills.get('Points For', bills.get('PF', 'N/A'))} PF, {bills.get('Points Allowed', bills.get('PA', 'N/A'))} PA")
        print(f"🦁 {lions.get('Team', lions.get('Tm', 'Unknown'))} ({lions['Abbrev']}): {lions.get('Wins', lions.get('W', 'N/A'))}-{lions.get('Losses', lions.get('L', 'N/A'))} record, {lions.get('Points For', lions.get('PF', 'N/A'))} PF, {lions.get('Points Allowed', lions.get('PA', 'N/A'))} PA")
        print(f"👑 {chiefs.get('Team', chiefs.get('Tm', 'Unknown'))} ({chiefs['Abbrev']}): {chiefs.get('Wins', chiefs.get('W', 'N/A'))}-{chiefs.get('Losses', chiefs.get('L', 'N/A'))} record, {chiefs.get('Points For', chiefs.get('PF', 'N/A'))} PF, {chiefs.get('Points Allowed', chiefs.get('PA', 'N/A'))} PA")
        
        print()
        print("🏆 Conference Breakdown:")
        afc_teams = teams.get_teams_by_conference('AFC')
        nfc_teams = teams.get_teams_by_conference('NFC')
        print(f"AFC: {len(afc_teams)} teams | NFC: {len(nfc_teams)} teams")
        print(f"Available abbreviations: {', '.join(sorted(teams.list_abbreviations()))}")
        
        # Demonstrate CSV export functionality
        print()
        print("💾 CSV Export Examples:")
        print("=" * 30)
        
        try:
            # Export all teams
            csv_file = teams.to_csv()
            print(f"✅ All teams exported to: {csv_file}")
            
            # Export by conference
            conf_files = teams.export_by_conference()
            for conf, filename in conf_files.items():
                print(f"✅ {conf} teams exported to: {filename}")
                
            # Show data structure
            df = teams.to_dataframe()
            print(f"📊 Data structure: {df.shape[0]} teams, {df.shape[1]} columns")
            print(f"   Columns: {', '.join(df.columns)}")
            
        except Exception as export_error:
            logger.warning(f"CSV export demonstration failed: {export_error}")
            print(f"⚠️  CSV export demo failed: {export_error}")

    except Exception as e:
        logger.error(f"Failed to load NFL teams: {e}")
        print(f"An error occurred while loading NFL teams: {e}")
        sys.exit(1)


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
        logger.warning("Application interrupted by user")
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application failed with error: {e}")
        logger.exception("Full exception details:")
        print(f"An error occurred: {e}")
        sys.exit(1)