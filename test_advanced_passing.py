#!/usr/bin/env python3
"""
Test Advanced Passing Extraction
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

print('🎯 TESTING ADVANCED PASSING EXTRACTION')
print('=' * 45)

try:
    boxscore_id = '202411030buf'  # Bills vs Dolphins
    print(f'🎯 Testing advanced passing extraction for: {boxscore_id}')
    
    scraper = FixedNFLBoxscoreScraper()
    
    # Clear existing data for this game first
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            cursor.execute('DELETE FROM nfl.boxscore_advanced_passing WHERE boxscore_id = %s', (boxscore_id,))
            cursor.execute('DELETE FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
            cursor.execute('DELETE FROM nfl.boxscore_officials WHERE boxscore_id = %s', (boxscore_id,))
            db._connection.commit()
            print('🧹 Cleared existing data for this game')
    
    # Run the full scrape with advanced passing
    success = scraper.scrape_boxscore_details(boxscore_id)
    print(f'📊 Scrape result: {"✅ Success" if success else "❌ Failed"}')
    
    if success:
        # Check what advanced passing data we got
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                
                # Count advanced passing records
                cursor.execute('''
                    SELECT COUNT(*) FROM nfl.boxscore_advanced_passing 
                    WHERE boxscore_id = %s
                ''', (boxscore_id,))
                adv_passing_count = cursor.fetchone()[0]
                
                print(f'📈 RESULTS:')
                print(f'  🎯 Advanced passing records: {adv_passing_count}')
                
                # Show advanced passing data
                if adv_passing_count > 0:
                    cursor.execute('''
                        SELECT player_name, team, cmp, att, yds,
                               first_downs, first_down_pct,
                               intended_air_yards, completed_air_yards, yac,
                               drops, drop_pct, bad_throws, bad_throw_pct,
                               pressures, pressure_pct,
                               scrambles, scramble_yards_per_scramble
                        FROM nfl.boxscore_advanced_passing 
                        WHERE boxscore_id = %s
                        ORDER BY att DESC
                    ''', (boxscore_id,))
                    
                    advanced_records = cursor.fetchall()
                    print(f'\\n🎯 ADVANCED PASSING DATA:')
                    for (name, team, cmp, att, yds, first_downs, first_down_pct,
                         iay, cay, yac, drops, drop_pct, bad_throws, bad_throw_pct,
                         pressures, pressure_pct, scrambles, scramble_yds) in advanced_records:
                        
                        print(f'\\n  📊 {name} ({team}):')
                        print(f'    • Basic: {cmp}/{att} for {yds} yards')
                        print(f'    • First Downs: {first_downs} ({first_down_pct}%)')
                        print(f'    • Air Yards: {iay} intended, {cay} completed, {yac} YAC')
                        print(f'    • Accuracy: {drops} drops ({drop_pct}%), {bad_throws} bad throws ({bad_throw_pct}%)')
                        print(f'    • Pressure: {pressures} pressures ({pressure_pct}%)')
                        if scrambles > 0:
                            print(f'    • Mobility: {scrambles} scrambles ({scramble_yds} yds/scramble)')
                
                # Compare with basic passing stats
                print(f'\\n🔍 COMPARISON WITH BASIC STATS:')
                cursor.execute('''
                    SELECT p.player_name, p.team, p.pass_cmp, p.pass_att, p.pass_yds,
                           a.cmp, a.att, a.yds
                    FROM nfl.boxscore_player_stats p
                    LEFT JOIN nfl.boxscore_advanced_passing a 
                        ON p.boxscore_id = a.boxscore_id 
                        AND p.player_name = a.player_name 
                        AND p.team = a.team
                    WHERE p.boxscore_id = %s AND p.pass_att > 0
                    ORDER BY p.pass_att DESC
                ''', (boxscore_id,))
                
                comparison = cursor.fetchall()
                for name, team, basic_cmp, basic_att, basic_yds, adv_cmp, adv_att, adv_yds in comparison:
                    match_status = "✅ Match" if (basic_cmp == adv_cmp and basic_att == adv_att and basic_yds == adv_yds) else "⚠️  Mismatch"
                    print(f'  • {name} ({team}): Basic {basic_cmp}/{basic_att}/{basic_yds} vs Advanced {adv_cmp}/{adv_att}/{adv_yds} {match_status}')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
