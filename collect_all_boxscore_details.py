#!/usr/bin/env python3
"""
Collect ALL boxscore details for the 2024 season using the fixed scraper.
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

from fixed_boxscore_scraper import FixedNFLBoxscoreScraper
from src.nfl.database import PostgreSQLManager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def main():
    """Collect detailed boxscore data for ALL games"""
    if len(sys.argv) > 1:
        season = int(sys.argv[1])
    else:
        season = 2024
    
    logger.info("🏈 COMPREHENSIVE NFL Boxscore Collection")
    logger.info("=" * 60)
    logger.info(f"📅 Processing season: {season}")
    
    scraper = FixedNFLBoxscoreScraper()
    
    try:
        # Create database tables
        scraper.create_database_tables()
        
        # Get ALL available boxscore IDs for the season (remove limit to process all games)
        boxscore_ids = scraper.get_available_boxscore_ids(limit=None, season=season)  # Process ALL games
        
        if not boxscore_ids:
            logger.warning("⚠️  No boxscore IDs found that need scraping")
            return
        
        logger.info(f"📋 Found {len(boxscore_ids)} boxscores to scrape")
        
        # Scrape each boxscore
        successful_scrapes = 0
        failed_scrapes = 0
        
        # Process each boxscore with delay
        for i, boxscore_id in enumerate(boxscore_ids, 1):
            logger.info(f"🎯 Progress: {i}/{len(boxscore_ids)} - {boxscore_id}")
            
            try:
                success = scraper.scrape_boxscore_details(boxscore_id)
                if success:
                    successful_scrapes += 1
                    logger.info(f"✅ Success: {boxscore_id}")
                else:
                    failed_scrapes += 1
                    logger.warning(f"❌ Failed: {boxscore_id}")
                    
            except Exception as e:
                failed_scrapes += 1
                logger.error(f"❌ Error processing {boxscore_id}: {e}")
            
            # Add delay between requests to be respectful to the server
            if i < len(boxscore_ids):  # Don't delay after the last item
                delay = 30 + random.uniform(0, 5)  # 30-35 second random delay
                logger.info(f"⏱️ Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
        
        logger.info("=" * 60)
        logger.info(f"🎯 Collection completed!")
        logger.info(f"✅ Successful: {successful_scrapes}/{len(boxscore_ids)} games")
        logger.info(f"❌ Failed: {failed_scrapes}/{len(boxscore_ids)} games")
        
        # Show final comprehensive results
        logger.info("\n📊 FINAL DATABASE SUMMARY:")
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                # Player stats
                cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_player_stats")
                player_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT boxscore_id) FROM nfl.boxscore_player_stats")
                player_games = cursor.fetchone()[0]
                
                # Team stats
                cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_team_stats")
                team_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT boxscore_id) FROM nfl.boxscore_team_stats")
                team_games = cursor.fetchone()[0]
                
                # Scoring events
                cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_scoring")
                scoring_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT boxscore_id) FROM nfl.boxscore_scoring")
                scoring_games = cursor.fetchone()[0]
                
                logger.info(f"   👥 Player stats: {player_count} records across {player_games} games")
                logger.info(f"   🏟️ Team stats: {team_count} records across {team_games} games")
                logger.info(f"   🏆 Scoring events: {scoring_count} records across {scoring_games} games")
                
                # Show sample player data
                cursor.execute("""
                    SELECT boxscore_id, player_name, team, pass_yds, rush_yds, rec_yds
                    FROM nfl.boxscore_player_stats 
                    WHERE pass_yds > 100 OR rush_yds > 50 OR rec_yds > 50
                    ORDER BY pass_yds DESC NULLS LAST, rush_yds DESC NULLS LAST
                    LIMIT 5
                """)
                player_samples = cursor.fetchall()
                
                if player_samples:
                    logger.info("\n🌟 Sample high-performing players:")
                    for boxscore_id, name, team, pass_yds, rush_yds, rec_yds in player_samples:
                        stats = []
                        if pass_yds and pass_yds > 0:
                            stats.append(f"{pass_yds} pass yds")
                        if rush_yds and rush_yds > 0:
                            stats.append(f"{rush_yds} rush yds")
                        if rec_yds and rec_yds > 0:
                            stats.append(f"{rec_yds} rec yds")
                        logger.info(f"   {name} ({team}) - {', '.join(stats)} - {boxscore_id}")
                    
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
