#!/usr/bin/env python3
"""
Add Player Role Column
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

print('🏷️ ADDING PLAYER_ROLE COLUMN TO DATABASE')
print('=' * 50)

try:
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            # Add player_role column
            print('📝 Adding player_role column...')
            cursor.execute('''
                ALTER TABLE nfl.boxscore_player_stats 
                ADD COLUMN IF NOT EXISTS player_role VARCHAR(20) DEFAULT 'unknown'
            ''')
            
            db._connection.commit()
            print('✅ Successfully added player_role column')
            
            # Verify the column was added
            cursor.execute('''
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'nfl' AND table_name = 'boxscore_player_stats'
                AND column_name = 'player_role'
            ''')
            
            result = cursor.fetchone()
            if result:
                col_name, data_type, default_val = result
                print(f'🔍 VERIFICATION: {col_name} ({data_type}) DEFAULT {default_val}')
            
            # Show how we'll categorize players
            print()
            print('🏈 PLAYER ROLE CATEGORIES:')
            print('  • "offense" - Players with passing, rushing, or receiving stats')
            print('  • "defense" - Players with tackles, sacks, interceptions, etc.')
            print('  • "special_teams" - Players with only return stats')
            print('  • "mixed" - Players with stats in multiple categories')
            print('  • "unknown" - Players with no measurable stats')
            
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
