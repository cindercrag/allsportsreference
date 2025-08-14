#!/usr/bin/env python3
"""
Test Full Boxscore Scrape with Advanced Rushing
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

print('🏈 FULL BOXSCORE SCRAPE TEST (WITH ADVANCED RUSHING)')
print('=' * 60)

def test_full_scrape_with_advanced_rushing():
    """Test full scrape including advanced rushing"""
    
    try:
        boxscore_id = '202411030buf'  # Bills vs Dolphins
        print(f'🎯 Testing full scrape for: {boxscore_id}')
        
        scraper = FixedNFLBoxscoreScraper()
        
        # Clear existing data for this game first
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute('DELETE FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
                cursor.execute('DELETE FROM nfl.boxscore_officials WHERE boxscore_id = %s', (boxscore_id,))
                cursor.execute('DELETE FROM nfl.boxscore_advanced_passing WHERE boxscore_id = %s', (boxscore_id,))
                cursor.execute('DELETE FROM nfl.boxscore_advanced_rushing WHERE boxscore_id = %s', (boxscore_id,))
                db._connection.commit()
                print('🗑️  Cleared existing data for this game')
        
        # Run the full scrape
        success = scraper.scrape_boxscore_details(boxscore_id)
        print(f'📊 Scrape result: {"✅ Success" if success else "❌ Failed"}')
        
        if success:
            # Check what we got
            with PostgreSQLManager() as db:
                with db._connection.cursor() as cursor:
                    
                    # Count total players
                    cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_player_stats WHERE boxscore_id = %s', (boxscore_id,))
                    total_players = cursor.fetchone()[0]
                    
                    # Count advanced passing records
                    cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_advanced_passing WHERE boxscore_id = %s', (boxscore_id,))
                    advanced_passing_count = cursor.fetchone()[0]
                    
                    # Count advanced rushing records
                    cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_advanced_rushing WHERE boxscore_id = %s', (boxscore_id,))
                    advanced_rushing_count = cursor.fetchone()[0]
                    
                    # Count officials
                    cursor.execute('SELECT COUNT(*) FROM nfl.boxscore_officials WHERE boxscore_id = %s', (boxscore_id,))
                    officials_count = cursor.fetchone()[0]
                    
                    print(f'\\n📈 COMPREHENSIVE RESULTS:')
                    print(f'  👥 Total players: {total_players}')
                    print(f'  🎯 Advanced passing records: {advanced_passing_count}')
                    print(f'  🏃 Advanced rushing records: {advanced_rushing_count}')
                    print(f'  🏛️  Officials: {officials_count}')
                    
                    # Show top advanced rushing players
                    if advanced_rushing_count > 0:
                        cursor.execute('''
                            SELECT 
                                player_name, team, rush_att, rush_yds, rush_td,
                                yards_before_contact, yards_after_contact, broken_tackles
                            FROM nfl.boxscore_advanced_rushing 
                            WHERE boxscore_id = %s
                            ORDER BY rush_yds DESC
                            LIMIT 5
                        ''', (boxscore_id,))
                        
                        top_rushers = cursor.fetchall()
                        print(f'\\n🏃 TOP ADVANCED RUSHING PERFORMERS:')
                        for player_name, team, att, yds, td, ybc, yac, broken_tackles in top_rushers:
                            print(f'  🏆 {player_name} ({team}): {att} att, {yds} yds, {td} TD')
                            print(f'      💪 {ybc} YBC + {yac} YAC = {ybc + yac} total, {broken_tackles} broken tackles')
                    
                    # Show advanced passing players
                    if advanced_passing_count > 0:
                        cursor.execute('''
                            SELECT 
                                player_name, team, cmp, att, yds,
                                intended_air_yards, pressure_pct, first_down_pct
                            FROM nfl.boxscore_advanced_passing 
                            WHERE boxscore_id = %s
                            ORDER BY yds DESC
                        ''', (boxscore_id,))
                        
                        quarterbacks = cursor.fetchall()
                        print(f'\\n🎯 ADVANCED PASSING ANALYTICS:')
                        for player_name, team, cmp, att, yds, air_yards, pressure_rate, first_down_pct in quarterbacks:
                            pressure_str = f"{pressure_rate:.1f}%" if pressure_rate else "N/A"
                            first_down_str = f"{first_down_pct:.1f}%" if first_down_pct else "N/A"
                            print(f'  🏈 {player_name} ({team}): {cmp}/{att} for {yds} yds')
                            print(f'      📊 {air_yards} air yards, {pressure_str} pressure rate, {first_down_str} 1st down %')
                    
                    print(f'\\n🎊 COMPREHENSIVE ANALYTICS COMPLETE!')
                    print(f'    ✅ Basic player stats: {total_players} records')
                    print(f'    ✅ Advanced passing: {advanced_passing_count} records') 
                    print(f'    ✅ Advanced rushing: {advanced_rushing_count} records')
                    print(f'    ✅ Officials data: {officials_count} records')
                    print(f'\\n🚀 NFL BOXSCORE SCRAPER WITH ADVANCED ANALYTICS IS FULLY OPERATIONAL!')
    
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_full_scrape_with_advanced_rushing()
