#!/usr/bin/env python3
"""
Test Kicking & Punting Extraction
"""

import sys
import os
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

print('🦵 TESTING KICKING & PUNTING EXTRACTION')
print('=' * 45)

try:
    boxscore_id = '202411030buf'  # Bills vs Dolphins
    print(f'🎯 Testing kicking extraction for: {boxscore_id}')
    
    scraper = FixedNFLBoxscoreScraper()
    
    # Clear existing data for this game first
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            cursor.execute('DELETE FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
            cursor.execute('DELETE FROM nfl.boxscore_officials WHERE boxscore_id = %s', (boxscore_id,))
            db._connection.commit()
            print('🧹 Cleared existing data for this game')
    
    # Run the full scrape with kicking/punting
    success = scraper.scrape_boxscore_details(boxscore_id)
    print(f'📊 Scrape result: {"✅ Success" if success else "❌ Failed"}')
    
    if success:
        # Check what kicking/punting data we got
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                
                # Count players with kicking stats
                cursor.execute('''
                    SELECT COUNT(*) FROM nfl.boxscore_player_stats 
                    WHERE boxscore_id = %s 
                    AND (fg_att > 0 OR xp_att > 0 OR punt_punts > 0)
                ''', (boxscore_id,))
                kicking_players = cursor.fetchone()[0]
                
                print(f'📈 RESULTS:')
                print(f'  🦵 Players with kicking/punting stats: {kicking_players}')
                
                # Show kickers (field goals/extra points)
                if kicking_players > 0:
                    cursor.execute('''
                        SELECT player_name, team, fg_made, fg_att, fg_pct, xp_made, xp_att
                        FROM nfl.boxscore_player_stats 
                        WHERE boxscore_id = %s AND (fg_att > 0 OR xp_att > 0)
                        ORDER BY fg_att DESC, xp_att DESC
                    ''', (boxscore_id,))
                    
                    kickers = cursor.fetchall()
                    if kickers:
                        print(f'🏈 KICKERS:')
                        for name, team, fg_made, fg_att, fg_pct, xp_made, xp_att in kickers:
                            print(f'  • {name} ({team}): {fg_made}/{fg_att} FG ({fg_pct}%), {xp_made}/{xp_att} XP')
                    
                    # Show punters
                    cursor.execute('''
                        SELECT player_name, team, punt_punts, punt_yards, punt_avg, punt_long, punt_in_20
                        FROM nfl.boxscore_player_stats 
                        WHERE boxscore_id = %s AND punt_punts > 0
                        ORDER BY punt_punts DESC
                    ''', (boxscore_id,))
                    
                    punters = cursor.fetchall()
                    if punters:
                        print(f'🦶 PUNTERS:')
                        for name, team, punts, yards, avg, long, in_20 in punters:
                            print(f'  • {name} ({team}): {punts} punts, {yards} yds ({avg} avg), {long} long, {in_20} inside 20')
                
                # Count total players for context
                cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
                total_players = cursor.fetchone()[0]
                print(f'\\n📊 CONTEXT: {total_players} total players in database for this game')
                
                # Show all column names that have kicking/punting data
                cursor.execute('''
                    SELECT player_name, team,
                           fg_made, fg_att, xp_made, xp_att, punt_punts, punt_yards
                    FROM nfl.boxscore_player_stats 
                    WHERE boxscore_id = %s 
                    AND (fg_made > 0 OR fg_att > 0 OR xp_made > 0 OR xp_att > 0 OR punt_punts > 0)
                    ORDER BY fg_att DESC, punt_punts DESC
                ''', (boxscore_id,))
                
                all_kicking = cursor.fetchall()
                print(f'\\n🔍 ALL KICKING/PUNTING DATA:')
                for name, team, fg_made, fg_att, xp_made, xp_att, punts, punt_yds in all_kicking:
                    stats = []
                    if fg_att > 0: stats.append(f'{fg_made}/{fg_att} FG')
                    if xp_att > 0: stats.append(f'{xp_made}/{xp_att} XP')
                    if punts > 0: stats.append(f'{punts} punts ({punt_yds} yds)')
                    print(f'  • {name} ({team}): {" | ".join(stats)}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
