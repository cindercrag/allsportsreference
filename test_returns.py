#!/usr/bin/env python3
"""
Test Returns Extraction
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

print('🏃 TESTING RETURNS EXTRACTION')
print('=' * 50)

try:
    boxscore_id = '202411030buf'
    print(f'🎯 Testing with boxscore: {boxscore_id}')
    
    scraper = FixedNFLBoxscoreScraper()
    soup = scraper.fetch_boxscore_html(boxscore_id)
    
    if soup:
        print('📄 Successfully fetched HTML')
        
        # Test return extraction
        returns_stats = scraper.extract_returns_data(soup, boxscore_id)
        
        print(f'📊 Extracted {len(returns_stats)} return specialists')
        
        # Show sample data
        if returns_stats:
            print()
            print('🔍 SAMPLE RETURNS DATA:')
            for i, player in enumerate(returns_stats):
                print(f"  Player {i+1}: {player['player_name']} ({player['team']})")
                
                # Show kick return stats
                if player['kick_returns'] > 0:
                    print(f"    Kick Returns: {player['kick_returns']} for {player['kick_return_yards']} yards")
                    print(f"    KR Avg: {player['kick_return_avg']}, TDs: {player['kick_return_td']}, Long: {player['kick_return_long']}")
                
                # Show punt return stats
                if player['punt_returns'] > 0:
                    print(f"    Punt Returns: {player['punt_returns']} for {player['punt_return_yards']} yards")
                    print(f"    PR Avg: {player['punt_return_avg']}, TDs: {player['punt_return_td']}, Long: {player['punt_return_long']}")
                
                print()
        
        # Test save operation (check for existing players first)
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
                existing_players = cursor.fetchone()[0]
                
                print(f'📋 Found {existing_players} existing player records for this game')
                
                if existing_players > 0 and returns_stats:
                    print('💾 Testing returns data save...')
                    success = scraper.save_returns_data(returns_stats)
                    print(f'💾 Save result: {"✅ Success" if success else "❌ Failed"}')
                    
                    if success:
                        # Check updated records
                        cursor.execute('''
                            SELECT player_name, team, kick_returns, kick_return_yards, punt_returns, punt_return_yards
                            FROM nfl.boxscore_player_stats 
                            WHERE boxscore_id = %s AND (kick_returns > 0 OR punt_returns > 0)
                            ORDER BY kick_returns DESC, punt_returns DESC
                        ''', (boxscore_id,))
                        
                        updated_records = cursor.fetchall()
                        print(f'📈 Found {len(updated_records)} players with return stats:')
                        for record in updated_records:
                            name, team, kr, kr_yds, pr, pr_yds = record
                            stats = []
                            if kr > 0: stats.append(f'{kr} KR for {kr_yds} yds')
                            if pr > 0: stats.append(f'{pr} PR for {pr_yds} yds')
                            print(f'  {name} ({team}): {" | ".join(stats)}')
                
                else:
                    print('⚠️  No existing player records found, cannot test returns save')
    
    else:
        print('❌ Failed to fetch HTML')
        
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
