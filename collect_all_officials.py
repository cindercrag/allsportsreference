#!/usr/bin/env python3
"""
Collect officials data for all 2024 NFL games.
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
    """Collect officials data for all 2024 games"""
    season = 2024
    
    logger.info("🏛️ NFL OFFICIALS DATA COLLECTION")
    logger.info("=" * 60)
    logger.info(f"📅 Processing season: {season}")
    
    scraper = FixedNFLBoxscoreScraper()
    
    try:
        # Get all boxscore IDs for 2024 season
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute("""
                    SELECT boxscore_id 
                    FROM nfl.game_logs 
                    WHERE season = %s 
                    ORDER BY date, boxscore_id
                """, (season,))
                
                boxscore_ids = [row[0] for row in cursor.fetchall()]
        
        logger.info(f"📊 Found {len(boxscore_ids)} games to process")
        
        # Check what we already have
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(DISTINCT boxscore_id) FROM nfl.boxscore_officials")
                existing_count = cursor.fetchone()[0]
                
        logger.info(f"📋 Already have officials for {existing_count} games")
        logger.info(f"🎯 Need to process {len(boxscore_ids) - existing_count} games")
        
        # Process each game
        successful_scrapes = 0
        failed_scrapes = 0
        skipped_games = 0
        
        for i, boxscore_id in enumerate(boxscore_ids, 1):
            logger.info(f"🎯 Progress: {i}/{len(boxscore_ids)} - {boxscore_id}")
            
            # Check if we already have officials for this game
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_officials WHERE boxscore_id = %s", (boxscore_id,))
                    existing_officials = cursor.fetchone()[0]
                    
            if existing_officials > 0:
                logger.info(f"⏭️ Skipping {boxscore_id} - already have {existing_officials} officials")
                skipped_games += 1
                continue
            
            try:
                # Fetch page and extract officials
                soup = scraper.fetch_boxscore_html(boxscore_id)
                
                if soup:
                    officials = scraper.extract_officials_data(soup, boxscore_id)
                    
                    if officials:
                        success = scraper.save_officials_data(officials)
                        if success:
                            successful_scrapes += 1
                            logger.info(f"✅ Success: {boxscore_id} - saved {len(officials)} officials")
                        else:
                            failed_scrapes += 1
                            logger.warning(f"❌ Failed to save: {boxscore_id}")
                    else:
                        logger.warning(f"⚠️ No officials found: {boxscore_id}")
                        failed_scrapes += 1
                else:
                    failed_scrapes += 1
                    logger.error(f"❌ Failed to fetch page: {boxscore_id}")
                    
            except Exception as e:
                failed_scrapes += 1
                logger.error(f"❌ Error processing {boxscore_id}: {e}")
            
            # Add delay between requests (10-15 seconds for officials only)
            if i < len(boxscore_ids):
                delay = 10 + random.uniform(0, 5)  # 10-15 second delay
                logger.info(f"⏱️ Waiting {delay:.1f} seconds...")
                time.sleep(delay)
        
        logger.info("=" * 60)
        logger.info(f"🎯 Officials Collection Completed!")
        logger.info(f"✅ Successful: {successful_scrapes}")
        logger.info(f"❌ Failed: {failed_scrapes}")
        logger.info(f"⏭️ Skipped: {skipped_games}")
        
        # Final summary
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM nfl.boxscore_officials")
                total_officials = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(DISTINCT boxscore_id) FROM nfl.boxscore_officials")
                games_with_officials = cursor.fetchone()[0]
                
                logger.info(f"📊 Final totals:")
                logger.info(f"   🏛️ Total officials: {total_officials}")
                logger.info(f"   🎮 Games with officials: {games_with_officials}/{len(boxscore_ids)}")
                
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        raise


if __name__ == "__main__":
    main()
