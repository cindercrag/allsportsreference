#!/usr/bin/env python3
"""
Complete Enhanced Scraper Test
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

print('🏈 COMPLETE ENHANCED SCRAPER TEST')
print('=' * 60)

try:
    boxscore_id = '202411030buf'
    print(f'🎯 Testing complete scrape for: {boxscore_id}')
    
    scraper = FixedNFLBoxscoreScraper()
    
    # Clear existing data for this game first
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            cursor.execute('DELETE FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
            cursor.execute('DELETE FROM nfl.boxscore_officials WHERE boxscore_id = %s', (boxscore_id,))
            db._connection.commit()
            print('🗑️ Cleared existing data for this game')
    
    # Run the complete enhanced scrape
    success = scraper.scrape_boxscore_details(boxscore_id)
    print(f'📊 Scrape result: {"✅ Success" if success else "❌ Failed"}')
    
    if success:
        # Check comprehensive results
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                # Count total players
                cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
                total_players = cursor.fetchone()[0]
                
                # Count by stat type
                cursor.execute('''
                    SELECT 
                        COUNT(CASE WHEN pass_att > 0 OR rush_att > 0 OR rec_rec > 0 THEN 1 END) as offense_players,
                        COUNT(CASE WHEN def_tackles > 0 OR def_sacks > 0 OR def_int > 0 THEN 1 END) as defense_players,
                        COUNT(CASE WHEN kick_returns > 0 OR punt_returns > 0 THEN 1 END) as return_players
                    FROM nfl.boxscore_player_stats 
                    WHERE boxscore_id = %s
                ''', (boxscore_id,))
                
                offense_players, defense_players, return_players = cursor.fetchone()
                
                # Count officials
                cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_officials WHERE boxscore_id = %s', (boxscore_id,))
                officials_count = cursor.fetchone()[0]
                
                print(f'\n📈 COMPREHENSIVE RESULTS:')
                print(f'  👥 Total players: {total_players}')
                print(f'  🏈 Offensive players: {offense_players}')
                print(f'  🛡️ Defensive players: {defense_players}')
                print(f'  🏃 Return specialists: {return_players}')
                print(f'  🏛️ Officials: {officials_count}')
                
                # Show sample players from each category
                print(f'\n🏈 TOP OFFENSIVE PLAYERS:')
                cursor.execute('''
                    SELECT player_name, team, pass_yds, rush_yds, rec_yds
                    FROM nfl.boxscore_player_stats 
                    WHERE boxscore_id = %s AND (pass_yds > 0 OR rush_yds > 0 OR rec_yds > 0)
                    ORDER BY pass_yds DESC NULLS LAST, rush_yds DESC NULLS LAST
                    LIMIT 3
                ''', (boxscore_id,))
                
                for player in cursor.fetchall():
                    name, team, pass_yds, rush_yds, rec_yds = player
                    stats = []
                    if pass_yds: stats.append(f'{pass_yds} pass yds')
                    if rush_yds: stats.append(f'{rush_yds} rush yds')
                    if rec_yds: stats.append(f'{rec_yds} rec yds')
                    print(f'  {name} ({team}): {" | ".join(stats)}')
                
                print(f'\n🛡️ TOP DEFENSIVE PLAYERS:')
                cursor.execute('''
                    SELECT player_name, team, def_tackles, def_sacks, def_int
                    FROM nfl.boxscore_player_stats 
                    WHERE boxscore_id = %s AND (def_tackles > 0 OR def_sacks > 0 OR def_int > 0)
                    ORDER BY def_tackles DESC, def_sacks DESC
                    LIMIT 3
                ''', (boxscore_id,))
                
                for player in cursor.fetchall():
                    name, team, tackles, sacks, ints = player
                    stats = []
                    if tackles > 0: stats.append(f'{tackles} tackles')
                    if sacks > 0: stats.append(f'{sacks} sacks')
                    if ints > 0: stats.append(f'{ints} INTs')
                    print(f'  {name} ({team}): {" | ".join(stats)}')
                
                print(f'\n🏃 RETURN SPECIALISTS:')
                cursor.execute('''
                    SELECT player_name, team, kick_returns, kick_return_yards, punt_returns, punt_return_yards
                    FROM nfl.boxscore_player_stats 
                    WHERE boxscore_id = %s AND (kick_returns > 0 OR punt_returns > 0)
                    ORDER BY kick_returns DESC, punt_returns DESC
                ''', (boxscore_id,))
                
                for player in cursor.fetchall():
                    name, team, kr, kr_yds, pr, pr_yds = player
                    stats = []
                    if kr > 0: stats.append(f'{kr} KR for {kr_yds} yds')
                    if pr > 0: stats.append(f'{pr} PR for {pr_yds} yds')
                    print(f'  {name} ({team}): {" | ".join(stats)}')
                
                print(f'\n🏛️ GAME OFFICIALS:')
                cursor.execute('''
                    SELECT position, name FROM nfl.boxscore_officials 
                    WHERE boxscore_id = %s ORDER BY position
                ''', (boxscore_id,))
                
                for position, name in cursor.fetchall():
                    print(f'  {position}: {name}')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
