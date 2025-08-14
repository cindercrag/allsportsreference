#!/usr/bin/env python3
"""
Collect Defense Data for All NFL Games

This script collects defensive statistics for all 2024 NFL games using the enhanced scraper.
It processes games that haven't had defense data collected yet.
"""

import sys
import os
import time
import random
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
script_dir = Path(__file__).parent.absolute()
env_path = script_dir / '.env'
load_dotenv(env_path, override=True)

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from src.nfl.database import PostgreSQLManager
from fixed_boxscore_scraper import FixedNFLBoxscoreScraper
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_games_needing_defense_data(limit=None):
    """Get games that need defense data collection"""
    try:
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                # Find games that exist in game_logs but don't have defense data
                query = """
                    SELECT DISTINCT gl.boxscore_id, gl.date, gl.boxscore_home_team, gl.opponent
                    FROM nfl.game_logs gl
                    WHERE gl.season = 2024 
                    AND NOT EXISTS (
                        SELECT 1 FROM nfl.boxscore_player_stats bps 
                        WHERE bps.boxscore_id = gl.boxscore_id 
                        AND (bps.def_tackles > 0 OR bps.def_sacks > 0 OR bps.def_int > 0)
                    )
                    ORDER BY gl.date
                """
                
                if limit:
                    query += f" LIMIT {limit}"
                
                cursor.execute(query)
                games = cursor.fetchall()
                
                return [(row[0], row[1], row[2], row[3]) for row in games]
                
    except Exception as e:
        logger.error(f"❌ Error getting games needing defense data: {e}")
        return []


def get_defense_data_progress():
    """Get current progress of defense data collection"""
    try:
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                # Total 2024 games
                cursor.execute("SELECT COUNT(*) FROM nfl.game_logs WHERE season = 2024")
                total_games = cursor.fetchone()[0]
                
                # Games with defense data
                cursor.execute("""
                    SELECT COUNT(DISTINCT boxscore_id) 
                    FROM nfl.boxscore_player_stats 
                    WHERE boxscore_id IN (
                        SELECT boxscore_id FROM nfl.game_logs WHERE season = 2024
                    ) AND (def_tackles > 0 OR def_sacks > 0 OR def_int > 0)
                """)
                games_with_defense = cursor.fetchone()[0]
                
                return total_games, games_with_defense
                
    except Exception as e:
        logger.error(f"❌ Error getting defense data progress: {e}")
        return 0, 0


def main():
    logger.info("🛡️ NFL Defense Data Collection")
    logger.info("=" * 50)
    
    # Check current progress
    total_games, games_with_defense = get_defense_data_progress()
    logger.info(f"📊 Defense Data Progress: {games_with_defense}/{total_games} games")
    
    if games_with_defense >= total_games:
        logger.info("✅ All games already have defense data!")
        return
    
    # Get games that need defense data
    games_to_process = get_games_needing_defense_data()
    
    if not games_to_process:
        logger.info("✅ No games found that need defense data collection")
        return
    
    logger.info(f"📋 Found {len(games_to_process)} games needing defense data")
    
    # Initialize scraper
    scraper = FixedNFLBoxscoreScraper()
    
    # Process each game
    successful_count = 0
    failed_count = 0
    
    for i, (boxscore_id, date, home_team, opponent) in enumerate(games_to_process):
        logger.info(f"🎯 Progress: {i+1}/{len(games_to_process)}")
        logger.info(f"🏈 Processing: {opponent} @ {home_team} ({date}) - {boxscore_id}")
        
        try:
            # Scrape the full boxscore (includes defense data)
            success = scraper.scrape_boxscore_details(boxscore_id)
            
            if success:
                successful_count += 1
                logger.info(f"✅ Successfully processed game {i+1}")
                
                # Check how many defensive players we got
                with PostgreSQLManager() as db:
                    with db._connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT COUNT(*) FROM nfl.boxscore_player_stats 
                            WHERE boxscore_id = %s AND (def_tackles > 0 OR def_sacks > 0 OR def_int > 0)
                        """, (boxscore_id,))
                        defense_players = cursor.fetchone()[0]
                        logger.info(f"🛡️ Added {defense_players} defensive players")
            else:
                failed_count += 1
                logger.warning(f"⚠️ Failed to process game {i+1}")
            
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Error processing {boxscore_id}: {e}")
        
        # Respectful delay between requests (10-15 seconds)
        if i < len(games_to_process) - 1:
            delay = random.uniform(10, 15)
            logger.info(f"⏱️ Waiting {delay:.1f} seconds before next request...")
            time.sleep(delay)
    
    # Final summary
    logger.info("\n" + "=" * 50)
    logger.info("🏁 DEFENSE DATA COLLECTION COMPLETE")
    logger.info(f"✅ Successful: {successful_count}")
    logger.info(f"❌ Failed: {failed_count}")
    logger.info(f"📊 Total processed: {successful_count + failed_count}")
    
    # Final progress check
    total_games, games_with_defense = get_defense_data_progress()
    completion_rate = (games_with_defense / total_games * 100) if total_games > 0 else 0
    logger.info(f"🎯 Final Progress: {games_with_defense}/{total_games} games ({completion_rate:.1f}%)")


if __name__ == "__main__":
    main()
