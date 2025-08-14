#!/usr/bin/env python3
"""
Run the example data collection script for all NFL teams.
This uses the existing, working example_data_collection.py script.

Usage:
    python collect_all_teams_simple.py 2024
"""

import subprocess
import sys
import time
from loguru import logger


def setup_logging():
    """Configure logging."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )


def main():
    """Main function to collect data for all teams."""
    if len(sys.argv) != 2:
        print("Usage: python collect_all_teams_simple.py <year>")
        sys.exit(1)
    
    year = sys.argv[1]
    setup_logging()
    
    # All NFL team abbreviations
    all_teams = [
        'ATL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'CLT', 'CRD', 'DAL', 'DEN',
        'DET', 'GNB', 'HTX', 'JAX', 'KAN', 'MIA', 'MIN', 'NOR', 'NWE', 'NYG',
        'NYJ', 'OTI', 'PHI', 'PIT', 'RAI', 'RAM', 'RAV', 'SDG', 'SEA', 'SFO',
        'TAM', 'WAS'
    ]
    
    logger.info(f"🚀 Starting data collection for ALL NFL teams - {year} season")
    logger.info(f"📋 Processing {len(all_teams)} teams")
    logger.info("=" * 60)
    
    successful = []
    failed = []
    
    for i, team in enumerate(all_teams, 1):
        logger.info(f"🎯 Progress: {i}/{len(all_teams)} - Processing {team}")
        
        try:
            # Run the existing example script for this team
            result = subprocess.run(
                ['python', 'example_data_collection.py', '--team', team, '--year', year],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                successful.append(team)
                logger.info(f"✅ {team}: Success")
            else:
                failed.append(team)
                logger.error(f"❌ {team}: Failed - {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            failed.append(team)
            logger.error(f"❌ {team}: Timeout")
        except Exception as e:
            failed.append(team)
            logger.error(f"❌ {team}: Error - {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"🎉 Data collection completed!")
    logger.info(f"✅ Successful: {len(successful)} teams")
    logger.info(f"❌ Failed: {len(failed)} teams")
    
    if successful:
        logger.info(f"✅ Success list: {', '.join(successful)}")
    
    if failed:
        logger.warning(f"❌ Failed list: {', '.join(failed)}")
    
    # Show final database status
    try:
        import os
        from pathlib import Path
        from dotenv import load_dotenv
        
        # Load environment variables
        env_path = Path('.').absolute() / '.env'
        load_dotenv(env_path, override=True)
        
        # Add the app directory to the Python path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
        
        from src.nfl.database import PostgreSQLManager
        
        with PostgreSQLManager() as db:
            cursor = db._connection.cursor()
            cursor.execute("""
                SELECT team, COUNT(*) as games
                FROM nfl.game_logs 
                WHERE season = %s
                GROUP BY team
                ORDER BY team
            """, (int(year),))
            results = cursor.fetchall()
            
            logger.info(f"\\n📊 FINAL DATABASE STATUS FOR {year}:")
            logger.info("Team | Games")
            logger.info("-----|------")
            for team, games in results:
                logger.info(f"{team:4} | {games:5}")
            
            logger.info(f"\\n📈 Total: {len(results)} teams with data")
            
    except Exception as e:
        logger.error(f"❌ Failed to show database status: {e}")


if __name__ == "__main__":
    main()
