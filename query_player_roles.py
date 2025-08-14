#!/usr/bin/env python3
"""
Query Players by Role Examples
Demonstrates how to use the new player_role column for data analysis
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

print('🔍 PLAYER ROLE QUERY EXAMPLES')
print('=' * 42)

def show_query_examples():
    """Show examples of useful queries with the player_role column"""
    
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            # Example 1: Top defensive players by tackles
            print('🛡️ TOP DEFENSIVE PLAYERS BY TACKLES:')
            cursor.execute('''
                SELECT player_name, team, def_tackles, def_sacks, def_int
                FROM nfl.boxscore_player_stats 
                WHERE player_role = 'defense' AND def_tackles > 0
                ORDER BY def_tackles DESC, def_sacks DESC
                LIMIT 8
            ''')
            
            defenders = cursor.fetchall()
            for name, team, tackles, sacks, ints in defenders:
                print(f'  • {name} ({team}): {tackles} tackles, {sacks} sacks, {ints} INTs')
            
            print()
            
            # Example 2: Top offensive players by yards
            print('🏈 TOP OFFENSIVE PLAYERS BY TOTAL YARDS:')
            cursor.execute('''
                SELECT player_name, team, 
                       COALESCE(pass_yds, 0) + COALESCE(rush_yds, 0) + COALESCE(rec_yds, 0) as total_yards,
                       COALESCE(pass_yds, 0) as pass_yds,
                       COALESCE(rush_yds, 0) as rush_yds, 
                       COALESCE(rec_yds, 0) as rec_yds
                FROM nfl.boxscore_player_stats 
                WHERE player_role = 'offense'
                ORDER BY total_yards DESC
                LIMIT 8
            ''')
            
            offense = cursor.fetchall()
            for name, team, total, passing, rushing, receiving in offense:
                if total > 0:
                    stats = []
                    if passing > 0: stats.append(f'{passing} pass')
                    if rushing > 0: stats.append(f'{rushing} rush')
                    if receiving > 0: stats.append(f'{receiving} rec')
                    print(f'  • {name} ({team}): {total} total yards ({", ".join(stats)})')
            
            print()
            
            # Example 3: Special teams impact
            print('🎯 SPECIAL TEAMS IMPACT PLAYERS:')
            cursor.execute('''
                SELECT player_name, team,
                       COALESCE(kick_returns, 0) as kick_ret,
                       COALESCE(kick_return_yards, 0) as kick_yds,
                       COALESCE(punt_returns, 0) as punt_ret,
                       COALESCE(punt_return_yards, 0) as punt_yds,
                       COALESCE(kick_return_td, 0) + COALESCE(punt_return_td, 0) as return_tds
                FROM nfl.boxscore_player_stats 
                WHERE player_role IN ('special_teams', 'mixed') 
                  AND (kick_returns > 0 OR punt_returns > 0)
                ORDER BY (kick_return_yards + punt_return_yards) DESC
            ''')
            
            returns = cursor.fetchall()
            for name, team, kick_ret, kick_yds, punt_ret, punt_yds, tds in returns:
                total_yds = kick_yds + punt_yds
                stats = []
                if kick_ret > 0: stats.append(f'{kick_ret} kick ret ({kick_yds} yds)')
                if punt_ret > 0: stats.append(f'{punt_ret} punt ret ({punt_yds} yds)')
                if tds > 0: stats.append(f'{tds} TDs')
                print(f'  • {name} ({team}): {total_yds} total return yards - {", ".join(stats)}')
            
            print()
            
            # Example 4: Team breakdown by position groups
            print('📊 PLAYER DISTRIBUTION BY TEAM AND ROLE:')
            cursor.execute('''
                SELECT team, player_role, COUNT(*) as count
                FROM nfl.boxscore_player_stats 
                WHERE player_role != 'unknown'
                GROUP BY team, player_role
                ORDER BY team, 
                         CASE player_role 
                           WHEN 'offense' THEN 1
                           WHEN 'defense' THEN 2  
                           WHEN 'special_teams' THEN 3
                           WHEN 'mixed' THEN 4
                         END
            ''')
            
            team_breakdown = cursor.fetchall()
            current_team = None
            for team, role, count in team_breakdown:
                if team != current_team:
                    if current_team is not None:
                        print()
                    print(f'  🏟️ {team}:')
                    current_team = team
                print(f'    • {role}: {count} players')
            
            print()
            print('💡 USAGE EXAMPLES:')
            print('  • Filter by role: WHERE player_role = \'defense\'')
            print('  • Exclude certain roles: WHERE player_role NOT IN (\'unknown\', \'special_teams\')')
            print('  • Group analysis: GROUP BY player_role')
            print('  • Mixed role analysis: WHERE player_role = \'mixed\'')

if __name__ == '__main__':
    try:
        show_query_examples()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
