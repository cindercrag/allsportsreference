#!/usr/bin/env python3
"""
Add Kicking & Punting Columns
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

print('🦵 ADDING KICKING & PUNTING COLUMNS')
print('=' * 40)

def add_kicking_punting_columns():
    """Add kicking and punting columns to boxscore_player_stats"""
    
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            print('📝 Adding kicking columns...')
            
            # Field Goal columns
            kicking_columns = [
                'fg_made INTEGER DEFAULT 0',
                'fg_att INTEGER DEFAULT 0', 
                'fg_pct DECIMAL(5,1) DEFAULT 0.0',
                'fg_long INTEGER DEFAULT 0',
                'fg_1_19_made INTEGER DEFAULT 0',
                'fg_1_19_att INTEGER DEFAULT 0',
                'fg_20_29_made INTEGER DEFAULT 0', 
                'fg_20_29_att INTEGER DEFAULT 0',
                'fg_30_39_made INTEGER DEFAULT 0',
                'fg_30_39_att INTEGER DEFAULT 0', 
                'fg_40_49_made INTEGER DEFAULT 0',
                'fg_40_49_att INTEGER DEFAULT 0',
                'fg_50_plus_made INTEGER DEFAULT 0',
                'fg_50_plus_att INTEGER DEFAULT 0',
                'xp_made INTEGER DEFAULT 0',
                'xp_att INTEGER DEFAULT 0',
                'xp_pct DECIMAL(5,1) DEFAULT 0.0'
            ]
            
            for column in kicking_columns:
                col_name = column.split()[0]
                try:
                    cursor.execute(f'''
                        ALTER TABLE nfl.boxscore_player_stats 
                        ADD COLUMN IF NOT EXISTS {column}
                    ''')
                    print(f'  ✅ Added: {col_name}')
                except Exception as e:
                    print(f'  ⚠️  {col_name}: {e}')
            
            print('\\n📝 Adding punting columns...')
            
            # Punting columns
            punting_columns = [
                'punt_punts INTEGER DEFAULT 0',
                'punt_yards INTEGER DEFAULT 0',
                'punt_long INTEGER DEFAULT 0',
                'punt_avg DECIMAL(4,1) DEFAULT 0.0',
                'punt_net_avg DECIMAL(4,1) DEFAULT 0.0',
                'punt_in_20 INTEGER DEFAULT 0',
                'punt_in_20_pct DECIMAL(5,1) DEFAULT 0.0',
                'punt_touchbacks INTEGER DEFAULT 0',
                'punt_touchback_pct DECIMAL(5,1) DEFAULT 0.0',
                'punt_blocked INTEGER DEFAULT 0'
            ]
            
            for column in punting_columns:
                col_name = column.split()[0]
                try:
                    cursor.execute(f'''
                        ALTER TABLE nfl.boxscore_player_stats 
                        ADD COLUMN IF NOT EXISTS {column}
                    ''')
                    print(f'  ✅ Added: {col_name}')
                except Exception as e:
                    print(f'  ⚠️  {col_name}: {e}')
            
            db._connection.commit()
            print('\\n✅ Successfully added all kicking & punting columns!')
            
            # Verify columns were added
            cursor.execute('''
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'nfl' AND table_name = 'boxscore_player_stats'
                AND (column_name LIKE 'fg_%' OR column_name LIKE 'xp_%' OR column_name LIKE 'punt_%')
                ORDER BY column_name
            ''')
            
            new_columns = cursor.fetchall()
            print(f'\\n🔍 VERIFICATION: {len(new_columns)} kicking/punting columns now available:')
            for col_name, in new_columns:
                print(f'  • {col_name}')

if __name__ == '__main__':
    try:
        add_kicking_punting_columns()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
