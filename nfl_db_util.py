#!/usr/bin/env python3
"""
NFL Database Utility Script

This script provides command-line utilities for managing the NFL database:
- Create tables from Pydantic models
- Load current season data
- Query and export data
- Database maintenance operations
"""

import argparse
import sys
import logging
from typing import Optional

from app.src.nfl.teams import Teams
from app.src.nfl.database import (
    PostgreSQLManager, 
    create_nfl_teams_table, 
    insert_nfl_teams,
    query_nfl_teams
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_table(drop_existing: bool = False) -> bool:
    """Create the NFL teams table."""
    print("🗄️  Creating NFL teams table...")
    try:
        success = create_nfl_teams_table(drop_if_exists=drop_existing)
        if success:
            print("✅ Table created successfully")
            return True
        else:
            print("❌ Failed to create table")
            return False
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False


def load_season_data(year: str, update_existing: bool = True) -> bool:
    """Load NFL season data into the database."""
    print(f"📊 Loading {year} NFL season data...")
    try:
        # Load teams data
        teams = Teams(year)
        models = teams.to_models()
        print(f"   Loaded {len(models)} teams from website")
        
        # Insert into database
        conflict_mode = "UPDATE" if update_existing else "IGNORE"
        rows_affected = insert_nfl_teams(models, on_conflict=conflict_mode)
        print(f"✅ Successfully processed {rows_affected} team records")
        return True
        
    except Exception as e:
        print(f"❌ Error loading season data: {e}")
        return False


def query_teams(where_clause: Optional[str] = None, format_output: str = "table") -> bool:
    """Query and display team data."""
    print("📋 Querying NFL teams from database...")
    try:
        teams = query_nfl_teams(where_clause or "")
        
        if not teams:
            print("No teams found matching criteria")
            return True
        
        if format_output == "table":
            print(f"\nFound {len(teams)} teams:")
            print("-" * 80)
            print(f"{'Team':<25} {'Abbr':<5} {'Conf':<4} {'W-L':<7} {'PF':<4} {'PA':<4} {'SRS':<6}")
            print("-" * 80)
            
            for team in teams:
                record = f"{team.wins}-{team.losses}"
                print(f"{team.team:<25} {team.abbrev:<5} {team.conference.value:<4} {record:<7} "
                      f"{team.points_for:<4} {team.points_allowed:<4} {team.simple_rating_system:<6.1f}")
        
        elif format_output == "csv":
            print("team,abbrev,conference,wins,losses,points_for,points_allowed,simple_rating_system")
            for team in teams:
                print(f"{team.team},{team.abbrev},{team.conference.value},{team.wins},"
                      f"{team.losses},{team.points_for},{team.points_allowed},{team.simple_rating_system}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error querying teams: {e}")
        return False


def show_schema() -> bool:
    """Show the generated table schema."""
    print("📋 NFL Teams Table Schema:")
    print("=" * 50)
    try:
        from app.src.nfl.models import NFLTeamData
        from app.src.nfl.database import PostgreSQLManager
        schema_sql = PostgreSQLManager.generate_create_table_sql(NFLTeamData, "nfl_teams")
        print(schema_sql)
        return True
    except Exception as e:
        print(f"❌ Error generating schema: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='NFL Database Utility')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create table command
    create_parser = subparsers.add_parser('create-table', help='Create NFL teams table')
    create_parser.add_argument('--drop', action='store_true', 
                              help='Drop existing table if it exists')
    
    # Load data command
    load_parser = subparsers.add_parser('load-data', help='Load NFL season data')
    load_parser.add_argument('year', help='Season year (e.g., 2024)')
    load_parser.add_argument('--no-update', action='store_true',
                            help='Do not update existing records')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query NFL teams')
    query_parser.add_argument('--where', help='WHERE clause for filtering')
    query_parser.add_argument('--format', choices=['table', 'csv'], default='table',
                             help='Output format')
    
    # Schema command
    subparsers.add_parser('schema', help='Show table schema')
    
    # Full setup command
    setup_parser = subparsers.add_parser('setup', help='Full database setup')
    setup_parser.add_argument('year', help='Season year to load')
    setup_parser.add_argument('--drop', action='store_true',
                             help='Drop existing table if it exists')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    success = True
    
    if args.command == 'create-table':
        success = create_table(drop_existing=args.drop)
    
    elif args.command == 'load-data':
        success = load_season_data(args.year, update_existing=not args.no_update)
    
    elif args.command == 'query':
        success = query_teams(args.where, args.format)
    
    elif args.command == 'schema':
        success = show_schema()
    
    elif args.command == 'setup':
        print("🚀 Setting up NFL database...")
        success = create_table(drop_existing=args.drop)
        if success:
            success = load_season_data(args.year)
        if success:
            print("🎉 Database setup completed successfully!")
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
