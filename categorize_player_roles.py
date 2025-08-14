#!/usr/bin/env python3
"""
Categorize Player Roles
Updates the player_role column based on player statistics
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

print('🏷️ CATEGORIZING PLAYER ROLES')
print('=' * 40)

def categorize_players():
    """Categorize players based on their stats"""
    
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            print('📊 Analyzing player statistics...')
            
            # Get all players with their stats
            cursor.execute('''
                SELECT 
                    id,
                    player_name,
                    team,
                    -- Offense stats
                    COALESCE(pass_att, 0) as pass_att,
                    COALESCE(rush_att, 0) as rush_att, 
                    COALESCE(rec_rec, 0) as rec_rec,
                    -- Defense stats
                    COALESCE(def_tackles, 0) as def_tackles,
                    COALESCE(def_sacks, 0) as def_sacks,
                    COALESCE(def_int, 0) as def_int,
                    COALESCE(def_pd, 0) as def_pd,
                    COALESCE(def_ff, 0) as def_ff,
                    COALESCE(def_fr, 0) as def_fr,
                    -- Return stats
                    COALESCE(kick_returns, 0) as kick_returns,
                    COALESCE(punt_returns, 0) as punt_returns,
                    -- Kicking/Punting stats
                    COALESCE(fg_att, 0) as fg_att,
                    COALESCE(xp_att, 0) as xp_att,
                    COALESCE(punt_punts, 0) as punt_punts
                FROM nfl.boxscore_player_stats
                WHERE player_role = 'unknown'
            ''')
            
            players = cursor.fetchall()
            print(f'📈 Found {len(players)} players to categorize')
            
            # Counters for each category
            counts = {
                'offense': 0,
                'defense': 0, 
                'special_teams': 0,
                'mixed': 0,
                'unknown': 0
            }
            
            # Process each player
            for player in players:
                (player_id, name, team, pass_att, rush_att, rec_rec, 
                 def_tackles, def_sacks, def_int, def_pd, def_ff, def_fr,
                 kick_returns, punt_returns, fg_att, xp_att, punt_punts) = player
                
                # Check what types of stats they have
                has_offense = (pass_att > 0 or rush_att > 0 or rec_rec > 0)
                has_defense = (def_tackles > 0 or def_sacks > 0 or def_int > 0 or 
                              def_pd > 0 or def_ff > 0 or def_fr > 0)
                has_returns = (kick_returns > 0 or punt_returns > 0)
                has_kicking = (fg_att > 0 or xp_att > 0 or punt_punts > 0)
                
                # Determine role category
                if (has_offense + has_defense + has_returns + has_kicking) > 1:
                    role = 'mixed'
                elif has_offense:
                    role = 'offense'
                elif has_defense:
                    role = 'defense'
                elif has_returns or has_kicking:
                    role = 'special_teams'
                else:
                    role = 'unknown'
                
                # Update the player's role
                cursor.execute('''
                    UPDATE nfl.boxscore_player_stats 
                    SET player_role = %s 
                    WHERE id = %s
                ''', (role, player_id))
                
                counts[role] += 1
            
            # Commit all updates
            db._connection.commit()
            
            print('✅ Successfully categorized all players!')
            print()
            print('📊 CATEGORIZATION RESULTS:')
            for role, count in counts.items():
                if count > 0:
                    print(f'  🏷️ {role}: {count} players')
            
            # Show some examples from each category
            print()
            print('🔍 SAMPLE PLAYERS BY CATEGORY:')
            
            for role in ['offense', 'defense', 'special_teams', 'mixed']:
                if counts[role] > 0:
                    cursor.execute('''
                        SELECT player_name, team
                        FROM nfl.boxscore_player_stats 
                        WHERE player_role = %s
                        LIMIT 3
                    ''', (role,))
                    
                    examples = cursor.fetchall()
                    print(f'  📋 {role.upper()}:')
                    for name, team in examples:
                        print(f'    • {name} ({team})')

if __name__ == '__main__':
    try:
        categorize_players()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
