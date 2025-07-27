#!/usr/bin/env python3
"""
All Sports Reference - Main Application Entry Point

A Python application for scraping and analyzing sports data from reference websites.
Currently supports NFL and NBA data with teams, schedules, and statistics.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.nfl import constants as nfl_constants
from src.nba import constants as nba_constants
from src.utils.common import _todays_date


def main():
    """
    Main entry point for the All Sports Reference application.
    """
    print("=" * 60)
    print("Welcome to All Sports Reference")
    print("=" * 60)
    print(f"Current date: {_todays_date()}")
    print()
    
    # Display supported sports
    print("Supported Sports:")
    print(f"- {nfl_constants.SPORT_CONFIG['display_name']} ({nfl_constants.SPORT_CONFIG['name'].upper()})")
    print(f"- {nba_constants.SPORT_CONFIG['display_name']} ({nba_constants.SPORT_CONFIG['name'].upper()})")
    print()
    
    # Display available functionality
    print("Available features:")
    print("- Team data scraping")
    print("- Season statistics")
    print("- Game schedules and results")
    print("- Player information")
    print("- Boxscores")
    print("- Automated CSV export with organized file structure")
    print("- Column glossaries")
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
    
    # TODO: Add interactive menu or command-line argument parsing
    print("Note: This is a basic entry point. Extend with specific functionality as needed.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)