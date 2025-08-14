#!/usr/bin/env python3
"""
Export all teams' data from the database to CSV files.
This creates individual CSV files for each team's schedule data.

Usage:
    python export_all_teams_csv.py 2024
"""

import sys
import os
from pathlib import Path
from loguru import logger
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.database import PostgreSQLManager


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def export_team_csv(team_code: str, year: int, output_dir: Path) -> bool:
    """
    Export a single team's data to CSV.
    
    Parameters
    ----------
    team_code : str
        Team abbreviation (e.g., 'KAN', 'ATL')
    year : int
        Season year
    output_dir : Path
        Directory to save CSV files
        
    Returns
    -------
    bool
        True if successful
    """
    try:
        with PostgreSQLManager() as db:
            cursor = db._connection.cursor()
            
            # Get all games for this team
            cursor.execute("""
                SELECT 
                    week, date, day_of_week, location, opponent, result,
                    team_score, opp_score, 
                    pass_cmp, pass_att, pass_cmp_pct, pass_yds, pass_td, pass_rate,
                    pass_sk, pass_sk_yds, rush_att, rush_yds, rush_td, rush_ypc,
                    tot_plays, tot_yds, tot_ypp, to_fumble, to_int,
                    penalty_count, penalty_yds, third_down_success, third_down_att,
                    fourth_down_success, fourth_down_att, time_of_possession,
                    boxscore_id, season, team
                FROM nfl.game_logs
                WHERE team = %s AND season = %s
                ORDER BY CAST(week AS INTEGER)
            """, (team_code, year))
            
            games = cursor.fetchall()
            
            if not games:
                logger.warning(f"No games found for {team_code} {year}")
                return False
            
            # Convert to DataFrame
            columns = [
                'Week', 'Date', 'Day', 'Location', 'Opponent', 'Result',
                'Team_Score', 'Opp_Score', 
                'Pass_Cmp', 'Pass_Att', 'Pass_Cmp_Pct', 'Pass_Yds', 'Pass_TD', 'Pass_Rate',
                'Pass_Sk', 'Pass_Sk_Yds', 'Rush_Att', 'Rush_Yds', 'Rush_TD', 'Rush_YPC',
                'Tot_Plays', 'Tot_Yds', 'Tot_YPP', 'TO_Fumble', 'TO_Int',
                'Penalty_Count', 'Penalty_Yds', 'Third_Down_Success', 'Third_Down_Att',
                'Fourth_Down_Success', 'Fourth_Down_Att', 'Time_of_Possession',
                'Boxscore_ID', 'Season', 'Team'
            ]
            
            df = pd.DataFrame(games, columns=columns)
            
            # Create team directory
            team_dir = output_dir / team_code.lower()
            team_dir.mkdir(parents=True, exist_ok=True)
            
            # Export full schedule
            schedule_file = team_dir / f"{year}_{team_code.lower()}_schedule.csv"
            df.to_csv(schedule_file, index=False)
            
            # Export regular season only (weeks 1-18, excluding week 0)
            try:
                regular_season = df[df['Week'].astype(str).str.isdigit() & (df['Week'].astype(int) >= 1)]
                if len(regular_season) > 0:
                    regular_file = team_dir / f"{year}_{team_code.lower()}_regular_season.csv"
                    regular_season.to_csv(regular_file, index=False)
            except Exception:
                # If week conversion fails, just use all data
                regular_file = team_dir / f"{year}_{team_code.lower()}_regular_season.csv"
                df.to_csv(regular_file, index=False)
            
            logger.info(f"✅ {team_code}: {len(df)} games → {schedule_file.name}")
            return True
            
    except Exception as e:
        logger.error(f"❌ {team_code}: Failed to export - {e}")
        return False


def main():
    """Main function to export all teams."""
    if len(sys.argv) != 2:
        print("Usage: python export_all_teams_csv.py <year>")
        sys.exit(1)
    
    year = int(sys.argv[1])
    setup_logging()
    
    logger.info(f"🚀 Exporting all teams' CSV files for {year} season")
    logger.info("=" * 60)
    
    # Create output directory
    output_dir = Path(f"data/nfl/{year}/teams")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all teams from database
    try:
        with PostgreSQLManager() as db:
            cursor = db._connection.cursor()
            cursor.execute("""
                SELECT DISTINCT team, COUNT(*) as games
                FROM nfl.game_logs 
                WHERE season = %s
                GROUP BY team
                ORDER BY team
            """, (year,))
            teams = cursor.fetchall()
            
        logger.info(f"📋 Found {len(teams)} teams in database")
        
    except Exception as e:
        logger.error(f"❌ Failed to get teams from database: {e}")
        sys.exit(1)
    
    # Export each team
    successful = []
    failed = []
    
    for i, (team_code, game_count) in enumerate(teams, 1):
        logger.info(f"🎯 Progress: {i}/{len(teams)} - Exporting {team_code} ({game_count} games)")
        
        if export_team_csv(team_code, year, output_dir):
            successful.append(team_code)
        else:
            failed.append(team_code)
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"🎉 Export completed!")
    logger.info(f"✅ Successful: {len(successful)} teams")
    logger.info(f"❌ Failed: {len(failed)} teams")
    
    if successful:
        logger.info(f"✅ Success list: {', '.join(successful)}")
    
    if failed:
        logger.warning(f"❌ Failed list: {', '.join(failed)}")
    
    # Show final directory structure
    logger.info(f"\\n📁 CSV files created in: {output_dir}")
    try:
        team_dirs = [d.name.upper() for d in output_dir.iterdir() if d.is_dir()]
        logger.info(f"📂 Team directories: {', '.join(sorted(team_dirs))}")
        
        # Count total CSV files
        csv_files = list(output_dir.glob("*/*.csv"))
        logger.info(f"📄 Total CSV files: {len(csv_files)}")
        
    except Exception as e:
        logger.error(f"Failed to list directories: {e}")


if __name__ == "__main__":
    main()
