#!/usr/bin/env python3
"""
Collect NFL data for ALL teams in a given season.
This script will gather schedule and game data for every NFL team.

Usage:
    python collect_all_teams.py 2024
    python collect_all_teams.py 2023
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
from src.nfl.teams import Teams
import argparse
import time


def setup_logging():
    """Configure logging for the collection script."""
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
        Team abbreviation (e.g., 'KAN', 'NE', 'PHI')
    year : int
        Season year
        
    Returns
    -------
    list
        List of NFLGameLogData objects ready for database insertion
    """
    logger.info(f"🏈 Collecting data for {team_abbrev} {year} season...")
    
    try:
        # Create schedule object and get data
        schedule = Schedule(team_abbrev, year)
        raw_data = schedule.get_regular_season_games()
        
        if not raw_data:
            logger.warning(f"No schedule data found for {team_abbrev} {year}")
            return []
        
        # Convert to database models
        game_logs = []
        for game_data in raw_data:
            try:
                # Create NFLGameLogData from the schedule data
                game_log = NFLGameLogData(
                    season=year,
                    team=team_abbrev,
                    week=game_data.get('Week', 0),
                    day=game_data.get('Day', ''),
                    date=game_data.get('Date', ''),
                    boxscore_id=game_data.get('boxscore_id', ''),
                    result=game_data.get('Result', ''),
                    overtime=game_data.get('OT', ''),
                    record=game_data.get('Record', ''),
                    location=game_data.get('Location', ''),
                    opponent=game_data.get('Opponent', ''),
                    team_score=game_data.get('Team_Score', 0),
                    opponent_score=game_data.get('Opp_Score', 0),
                    first_downs_offense=game_data.get('1stD_Off', 0),
                    total_yards_offense=game_data.get('TotYd_Off', 0),
                    passing_yards_offense=game_data.get('PassY_Off', 0),
                    rushing_yards_offense=game_data.get('RushY_Off', 0),
                    turnovers_offense=game_data.get('TO_Off', 0),
                    first_downs_defense=game_data.get('1stD_Def', 0),
                    total_yards_defense=game_data.get('TotYd_Def', 0),
                    passing_yards_defense=game_data.get('PassY_Def', 0),
                    rushing_yards_defense=game_data.get('RushY_Def', 0),
                    turnovers_defense=game_data.get('TO_Def', 0),
                    expected_points_offense=game_data.get('Exp_Pts_Off', 0.0),
                    expected_points_defense=game_data.get('Exp_Pts_Def', 0.0),
                    expected_points_special_teams=game_data.get('Exp_Pts_ST', 0.0)
                )
                game_logs.append(game_log)
            except Exception as e:
                logger.warning(f"Failed to convert game data for {team_abbrev}: {e}")
                continue
        
        logger.info(f"✅ Converted {len(game_logs)} games for {team_abbrev}")
        return game_logs
        
    except Exception as e:
        logger.error(f"❌ Failed to collect data for {team_abbrev} {year}: {e}")
        return []


def main():
    """Main function to collect data for all NFL teams."""
    parser = argparse.ArgumentParser(description='Collect NFL data for all teams')
    parser.add_argument('year', type=int, help='Season year (e.g., 2024)')
    parser.add_argument('--delay', type=float, default=2.0, 
                       help='Delay between team requests in seconds (default: 2.0)')
    
    args = parser.parse_args()
    
    setup_logging()
    
    logger.info(f"🚀 Starting data collection for ALL NFL teams - {args.year} season")
    logger.info("=" * 60)
    
    # Get all NFL teams
    try:
        teams_data = Teams(year=args.year)
        all_teams = teams_data.list_abbreviations()
        logger.info(f"📋 Found {len(all_teams)} teams to process")
        logger.info(f"📝 Teams: {', '.join(sorted(all_teams))}")
    except Exception as e:
        logger.error(f"❌ Failed to get team list: {e}")
        sys.exit(1)
    
    # Collect data for each team
    all_game_logs = []
    successful_teams = []
    failed_teams = []
    
    for i, team_abbrev in enumerate(sorted(all_teams), 1):
        logger.info(f"🎯 Progress: {i}/{len(all_teams)} - Processing {team_abbrev}")
        
        try:
            team_logs = collect_team_data(team_abbrev, args.year)
            if team_logs:
                all_game_logs.extend(team_logs)
                successful_teams.append(team_abbrev)
                logger.info(f"✅ {team_abbrev}: {len(team_logs)} games collected")
            else:
                failed_teams.append(team_abbrev)
                logger.warning(f"⚠️  {team_abbrev}: No data collected")
                
        except Exception as e:
            failed_teams.append(team_abbrev)
            logger.error(f"❌ {team_abbrev}: Failed - {e}")
        
        # Add delay between requests to be respectful
        if i < len(all_teams):
            logger.debug(f"⏱️  Waiting {args.delay}s before next team...")
            time.sleep(args.delay)
    
    # Store all data in database
    logger.info("=" * 60)
    logger.info(f"💾 Storing data in database...")
    logger.info(f"📊 Total games collected: {len(all_game_logs)}")
    logger.info(f"✅ Successful teams: {len(successful_teams)}")
    logger.info(f"❌ Failed teams: {len(failed_teams)}")
    
    if failed_teams:
        logger.warning(f"⚠️  Failed teams: {', '.join(failed_teams)}")
    
    if all_game_logs:
        try:
            with PostgreSQLManager() as db:
                # Insert all game logs
                insert_game_logs(db._connection, all_game_logs)
                logger.info("✅ All data successfully stored in database!")
                
                # Show summary
                cursor = db._connection.cursor()
                cursor.execute("""
                    SELECT team, COUNT(*) as games
                    FROM nfl.game_logs 
                    WHERE season = %s
                    GROUP BY team
                    ORDER BY team
                """, (args.year,))
                results = cursor.fetchall()
                
                logger.info(f"\\n📊 DATABASE SUMMARY FOR {args.year}:")
                logger.info("Team | Games")
                logger.info("-----|------")
                for team, games in results:
                    logger.info(f"{team:4} | {games:5}")
                    
        except Exception as e:
            logger.error(f"❌ Database insertion failed: {e}")
            sys.exit(1)
    else:
        logger.error("❌ No data collected - nothing to store")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("🎉 Data collection completed successfully!")


if __name__ == "__main__":
    main()
