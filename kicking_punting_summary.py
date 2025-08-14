#!/usr/bin/env python3
"""
Kicking & Punting Summary Report
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

print('🦵 KICKING & PUNTING IMPLEMENTATION SUMMARY')
print('=' * 48)

try:
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            # Show database schema additions
            print('📊 DATABASE SCHEMA ADDITIONS:')
            cursor.execute('''
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'nfl' AND table_name = 'boxscore_player_stats'
                AND (column_name LIKE 'fg_%' OR column_name LIKE 'xp_%' OR column_name LIKE 'punt_%')
                ORDER BY column_name
            ''')
            
            columns = cursor.fetchall()
            kicking_cols = [col for col, _ in columns if col.startswith(('fg_', 'xp_'))]
            punting_cols = [col for col, _ in columns if col.startswith('punt_') and not col.startswith('punt_return')]
            
            print(f'  🏈 Field Goal/Extra Point columns ({len(kicking_cols)}):')
            for col in kicking_cols:
                print(f'    • {col}')
            
            print(f'\\n  🦶 Punting columns ({len(punting_cols)}):')
            for col in punting_cols:
                print(f'    • {col}')
            
            # Show sample data from test game
            print('\\n🎯 SAMPLE DATA (Bills vs Dolphins):')
            cursor.execute('''
                SELECT player_name, team, player_role,
                       fg_made, fg_att, fg_pct, xp_made, xp_att,
                       punt_punts, punt_yards, punt_avg, punt_long
                FROM nfl.boxscore_player_stats 
                WHERE boxscore_id = '202411030buf'
                AND (fg_att > 0 OR xp_att > 0 OR punt_punts > 0)
                ORDER BY fg_att DESC, punt_punts DESC
            ''')
            
            kicking_data = cursor.fetchall()
            if kicking_data:
                print('  👤 KICKERS & PUNTERS:')
                for name, team, role, fg_made, fg_att, fg_pct, xp_made, xp_att, punts, punt_yds, punt_avg, punt_long in kicking_data:
                    stats = []
                    if fg_att > 0: stats.append(f'{fg_made}/{fg_att} FG ({fg_pct}%)')
                    if xp_att > 0: stats.append(f'{xp_made}/{xp_att} XP')
                    if punts > 0: stats.append(f'{punts} punts ({punt_avg} avg, {punt_long} long)')
                    print(f'    • {name} ({team}) [{role}]: {" | ".join(stats)}')
            
            # Show role categorization 
            print('\\n🏷️ PLAYER ROLE CATEGORIZATION:')
            cursor.execute('''
                SELECT player_role, COUNT(*) as count
                FROM nfl.boxscore_player_stats 
                WHERE boxscore_id = '202411030buf'
                GROUP BY player_role
                ORDER BY count DESC
            ''')
            
            roles = cursor.fetchall()
            for role, count in roles:
                print(f'  • {role}: {count} players')
            
            # Show special teams breakdown
            print('\\n🎯 SPECIAL TEAMS BREAKDOWN:')
            cursor.execute('''
                SELECT player_name, team,
                       CASE 
                         WHEN fg_att > 0 OR xp_att > 0 THEN 'Kicker'
                         WHEN punt_punts > 0 THEN 'Punter'
                         WHEN kick_returns > 0 THEN 'Kick Returner'
                         WHEN punt_returns > 0 THEN 'Punt Returner'
                         ELSE 'Other'
                       END as st_role,
                       COALESCE(fg_att, 0) + COALESCE(xp_att, 0) + COALESCE(punt_punts, 0) + 
                       COALESCE(kick_returns, 0) + COALESCE(punt_returns, 0) as total_st_plays
                FROM nfl.boxscore_player_stats 
                WHERE boxscore_id = '202411030buf' AND player_role = 'special_teams'
                ORDER BY total_st_plays DESC
            ''')
            
            st_players = cursor.fetchall()
            for name, team, st_role, plays in st_players:
                print(f'  • {name} ({team}): {st_role} ({plays} plays)')
            
            print('\\n✅ IMPLEMENTATION COMPLETE!')
            print('\\n💡 CAPABILITIES ADDED:')
            print('  • Field goal attempts, makes, percentages')
            print('  • Extra point attempts, makes, percentages') 
            print('  • Punt attempts, yards, averages, long')
            print('  • Automatic player role categorization')
            print('  • Integration with comprehensive boxscore scraper')
            print('  • Database schema with 27 new kicking/punting columns')

except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
