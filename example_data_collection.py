#!/usr/bin/env python3
"""
Example script showing how to collect NFL data and store it in the database
with proper boxscore_id linking.

This script demonstrates:
1. Loading NFL schedule data with boxscore IDs
2. Converting to proper database format
3. Inserting into PostgreSQL with unique key constraints
4. Querying the data back

Usage:
    python example_data_collection.py                    # Collect KAN 2023 data
    python example_data_collection.py --team NE --year 2024  # Collect specific team/year
"""

import sys
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.database import PostgreSQLManager, insert_game_logs
from src.nfl.schedule import Schedule
from src.nfl.models import NFLGameLogData
import argparse


def setup_logging():
    """Configure logging for the example script."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def collect_team_data(team_abbrev: str, year: int) -> list:
    """
    Collect schedule data for a team and convert to database format.
    
    Parameters
    ----------
    team_abbrev : str
        Team abbreviation (e.g., 'KAN', 'NE')
    year : int
        Season year
        
    Returns
    -------
    list
        List of game log dictionaries ready for database insertion
    """
    logger.info(f"🏈 Collecting {team_abbrev} schedule data for {year}")
    
    try:
        # Create Schedule instance and retrieve data
        schedule = Schedule(team_abbrev, year)
        
        # Get regular season games only (filter out playoffs)
        regular_season = schedule.get_regular_season_games()
        
        logger.info(f"📊 Found {len(regular_season)} regular season games")
        
        if not regular_season:
            logger.warning("No regular season data found")
            return []
        
        # Show some statistics
        games_with_boxscore = [game for game in regular_season if game.get('Boxscore_ID')]
        logger.info(f"🔗 Games with boxscore IDs: {len(games_with_boxscore)}")
        
        # Show first game as example
        if regular_season:
            first_game = regular_season[0]
            logger.info(f"📝 Example game: Week {first_game.get('Week')} vs {first_game.get('Opponent')} - Boxscore ID: {first_game.get('Boxscore_ID', 'N/A')}")
        
        return regular_season
        
    except Exception as e:
        logger.error(f"Failed to collect data for {team_abbrev} {year}: {e}")
        return []


def insert_to_database(game_logs: list, team_abbrev: str, year: int) -> bool:
    """
    Insert game log data into the database.
    
    Parameters
    ----------
    game_logs : list
        List of game log dictionaries
    team_abbrev : str
        Team abbreviation
    year : int
        Season year
        
    Returns
    -------
    bool
        True if successful
    """
    if not game_logs:
        logger.warning("No game logs to insert")
        return False
    
    logger.info(f"💾 Inserting {len(game_logs)} games for {team_abbrev} {year} into database")
    
    try:
        # Filter out games without boxscore_id
        valid_games = [game for game in game_logs if game.get('Boxscore_ID')]
        
        if len(valid_games) != len(game_logs):
            logger.warning(f"⚠️  Filtered out {len(game_logs) - len(valid_games)} games without boxscore_id")
        
        if not valid_games:
            logger.warning("No valid games with boxscore_id to insert")
            return False
        
        # Convert field names to match database schema
        db_ready_games = []
        for game in valid_games:
            # Create a mapping of CSV fields to database columns
            field_mapping = {
                'Boxscore_ID': 'boxscore_id',
                'Boxscore_URL': 'boxscore_url', 
                'Boxscore_Date': 'boxscore_date',
                'Boxscore_Game_Number': 'boxscore_game_number',
                'Boxscore_Home_Team': 'boxscore_home_team',
                'Week': 'week',
                'Game': 'game_num',
                'Date': 'date', 
                'Day': 'day_of_week',
                'Location': 'location',
                'Opponent': 'opponent',
                'Result': 'result',
                'Team': 'team',
                'Season': 'season',
                'Team_Score': 'team_score',
                'Opp_Score': 'opp_score',
                'Pass_Cmp': 'pass_cmp',
                'Pass_Att': 'pass_att',
                'Pass_Cmp_Pct': 'pass_cmp_pct',
                'Pass_Yds': 'pass_yds',
                'Pass_TD': 'pass_td',
                'Pass_Rate': 'pass_rate',
                'Pass_Sk': 'pass_sk',
                'Pass_Sk_Yds': 'pass_sk_yds',
                'Rush_Att': 'rush_att',
                'Rush_Yds': 'rush_yds',
                'Rush_TD': 'rush_td',
                'Rush_YPC': 'rush_ypc',
                'Tot_Plays': 'tot_plays',
                'Tot_Yds': 'tot_yds',
                'Tot_YPP': 'tot_ypp',
                'TO_Fumble': 'to_fumble',
                'TO_Int': 'to_int',
                'Penalty_Count': 'penalty_count',
                'penalties_yds': 'penalty_yds',  # Map the lowercase field
                'Third_Down_Success': 'third_down_success',
                'Third_Down_Att': 'third_down_att',
                'Fourth_Down_Success': 'fourth_down_success',
                'Fourth_Down_Att': 'fourth_down_att',
                'Time_of_Possession': 'time_of_possession'
            }
            
            # Create database-ready game record
            db_game = {}
            for csv_field, db_field in field_mapping.items():
                if csv_field in game:
                    db_game[db_field] = game[csv_field]
            
            # Only add games that have the required fields
            if db_game.get('boxscore_id') and db_game.get('team') and db_game.get('season'):
                db_ready_games.append(db_game)
        
        # Insert using the database function
        success = insert_game_logs(db_ready_games)
        
        if success:
            logger.info(f"✅ Successfully inserted {len(db_ready_games)} games")
            return True
        else:
            logger.error("❌ Failed to insert games")
            return False
            
    except Exception as e:
        logger.error(f"Failed to insert data: {e}")
        return False


def query_inserted_data(team_abbrev: str, year: int):
    """
    Query and display the inserted data.
    
    Parameters
    ----------
    team_abbrev : str
        Team abbreviation
    year : int
        Season year
    """
    logger.info(f"🔍 Querying inserted data for {team_abbrev} {year}")
    
    try:
        with PostgreSQLManager() as db:
            # Query game count
            count_result = db.fetch_one(
                "SELECT COUNT(*) FROM nfl.game_logs WHERE team = %s AND season = %s",
                (team_abbrev, year)
            )
            
            if count_result:
                game_count = count_result[0]
                logger.info(f"📊 Found {game_count} games in database")
            
            # Query some sample data
            sample_result = db.fetch_all(
                """
                SELECT week, date, opponent, result, team_score, opp_score, boxscore_id
                FROM nfl.game_logs 
                WHERE team = %s AND season = %s 
                ORDER BY date
                LIMIT 3
                """,
                (team_abbrev, year)
            )
            
            if sample_result:
                logger.info("🎮 Sample games:")
                for row in sample_result:
                    week, date, opponent, result, team_score, opp_score, boxscore_id = row
                    logger.info(f"   Week {week}: {date} vs {opponent} ({result} {team_score}-{opp_score}) [ID: {boxscore_id}]")
            
            # Query boxscore_id statistics
            boxscore_result = db.fetch_one(
                """
                SELECT 
                    COUNT(*) as total_games,
                    COUNT(boxscore_id) as games_with_boxscore_id,
                    COUNT(DISTINCT boxscore_home_team) as unique_home_teams
                FROM nfl.game_logs 
                WHERE team = %s AND season = %s
                """,
                (team_abbrev, year)
            )
            
            if boxscore_result:
                total, with_boxscore, unique_homes = boxscore_result
                logger.info(f"🔗 Boxscore linking: {with_boxscore}/{total} games have boxscore_id")
                logger.info(f"🏠 Unique home teams encountered: {unique_homes}")
                
    except Exception as e:
        logger.error(f"Failed to query data: {e}")


def main():
    """Main function for the data collection example."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Collect NFL data and store in database with boxscore linking",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--team',
        type=str,
        default='KAN',
        help='Team abbreviation (default: KAN)'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        default=2023,
        help='Season year (default: 2023)'
    )
    
    args = parser.parse_args()
    
    logger.info("🏈 NFL Data Collection & Database Storage Example")
    logger.info("=" * 55)
    
    # Step 1: Collect data
    game_logs = collect_team_data(args.team, args.year)
    
    if not game_logs:
        logger.error("No data collected, exiting")
        sys.exit(1)
    
    # Step 2: Insert into database
    success = insert_to_database(game_logs, args.team, args.year)
    
    if not success:
        logger.error("Failed to insert data, exiting")
        sys.exit(1)
    
    # Step 3: Query and verify
    query_inserted_data(args.team, args.year)
    
    logger.info("🎯 Example completed successfully!")
    logger.info("💡 You can now query the database using:")
    logger.info(f"   SELECT * FROM nfl.game_logs WHERE team = '{args.team}' AND season = {args.year};")
    logger.info("   SELECT * FROM nfl.game_summary WHERE season = 2024;")


if __name__ == "__main__":
    main()
