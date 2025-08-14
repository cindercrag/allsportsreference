#!/usr/bin/env python3
"""
Test Advanced Rushing Data Extraction
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

print('🏃 TESTING ADVANCED RUSHING EXTRACTION')
print('=' * 50)

def test_advanced_rushing():
    """Test advanced rushing data extraction"""
    
    try:
        boxscore_id = '202411030buf'  # Bills vs Dolphins game
        print(f'🎯 Testing advanced rushing for: {boxscore_id}')
        
        scraper = FixedNFLBoxscoreScraper()
        
        # Clear existing advanced rushing data for this game
        with PostgreSQLManager() as db:
            with db._connection.cursor() as cursor:
                cursor.execute('DELETE FROM nfl.boxscore_advanced_rushing WHERE boxscore_id = %s', (boxscore_id,))
                db._connection.commit()
                print('🗑️  Cleared existing advanced rushing data for this game')
        
        # Get the HTML and extract advanced rushing data
        soup = scraper.fetch_boxscore_html(boxscore_id)
        if not soup:
            print('❌ Failed to fetch HTML')
            return
        
        # Extract and save advanced rushing data
        advanced_rushing_stats = scraper.extract_advanced_rushing_data(soup, boxscore_id)
        print(f'📊 Extracted {len(advanced_rushing_stats)} advanced rushing records')
        
        if advanced_rushing_stats:
            # Save the data
            save_success = scraper.save_advanced_rushing_data(advanced_rushing_stats)
            print(f'💾 Save result: {"✅ Success" if save_success else "❌ Failed"}')
            
            if save_success:
                # Verify what we got
                with PostgreSQLManager() as db:
                    with db._connection.cursor() as cursor:
                        cursor.execute('''
                            SELECT 
                                player_name, team, rush_att, rush_yds, rush_td,
                                rush_first_downs, yards_before_contact, yards_after_contact,
                                broken_tackles, att_per_broken_tackle
                            FROM nfl.boxscore_advanced_rushing 
                            WHERE boxscore_id = %s
                            ORDER BY rush_yds DESC
                        ''', (boxscore_id,))
                        
                        results = cursor.fetchall()
                        print(f'\\n🏆 ADVANCED RUSHING RESULTS ({len(results)} players):')
                        print('=' * 80)
                        
                        for player_name, team, att, yds, td, first_downs, ybc, yac, broken_tackles, att_per_br in results:
                            efficiency = f"{att_per_br}" if att_per_br else "N/A"
                            print(f'🏃 {player_name:<18} ({team}): {att:>2} att, {yds:>3} yds, {td} TD')
                            print(f'    🎯 {first_downs} 1st downs | YBC: {ybc:>2} | YAC: {yac:>2} | {broken_tackles} broken tackles (1 per {efficiency} att)')
                            print()
                        
                        # Compare with basic rushing stats to validate
                        cursor.execute('''
                            SELECT player_name, team, rush_att, rush_yds, rush_td
                            FROM nfl.boxscore_player_stats 
                            WHERE boxscore_id = %s AND rush_att > 0
                            ORDER BY rush_yds DESC
                        ''', (boxscore_id,))
                        
                        basic_rushing = cursor.fetchall()
                        print(f'\\n📋 BASIC RUSHING COMPARISON ({len(basic_rushing)} players):')
                        print('=' * 60)
                        
                        for player_name, team, att, yds, td in basic_rushing:
                            print(f'  {player_name:<18} ({team}): {att:>2} att, {yds:>3} yds, {td} TD')
                        
                        # Validation check
                        print(f'\\n🔍 VALIDATION:')
                        if len(results) == len(basic_rushing):
                            print('  ✅ Player count matches between advanced and basic rushing')
                        else:
                            print(f'  ⚠️  Player count mismatch: {len(results)} advanced vs {len(basic_rushing)} basic')
                        
                        # Check if rush attempts match
                        validation_errors = 0
                        for advanced_player in results:
                            adv_name, adv_team, adv_att, adv_yds, adv_td = advanced_player[:5]
                            
                            # Find matching basic player
                            basic_match = None
                            for basic_player in basic_rushing:
                                basic_name, basic_team, basic_att, basic_yds, basic_td = basic_player
                                if basic_name == adv_name and basic_team == adv_team:
                                    basic_match = (basic_att, basic_yds, basic_td)
                                    break
                            
                            if basic_match:
                                basic_att, basic_yds, basic_td = basic_match
                                if adv_att == basic_att and adv_yds == basic_yds and adv_td == basic_td:
                                    print(f'  ✅ {adv_name}: Stats match perfectly')
                                else:
                                    print(f'  ❌ {adv_name}: MISMATCH - Adv({adv_att}/{adv_yds}/{adv_td}) vs Basic({basic_att}/{basic_yds}/{basic_td})')
                                    validation_errors += 1
                            else:
                                print(f'  ⚠️  {adv_name}: Not found in basic rushing')
                                validation_errors += 1
                        
                        if validation_errors == 0:
                            print('\\n🎉 PERFECT VALIDATION! All advanced rushing stats match basic stats')
                        else:
                            print(f'\\n⚠️  {validation_errors} validation errors found')
            
        else:
            print('📭 No advanced rushing data found')
    
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_advanced_rushing()
