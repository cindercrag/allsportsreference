#!/usr/bin/env python3
"""
Add Advanced Rushing Columns
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

print('🏃 ADDING ADVANCED RUSHING COLUMNS')
print('=' * 40)

def add_advanced_rushing_columns():
    """Add advanced rushing columns to boxscore_player_stats"""
    
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            print('📝 Adding advanced rushing columns...')
            
            # Advanced Rushing columns based on table analysis
            # ['Player', 'Tm', 'Att', 'Yds', 'TD', '1D', 'YBC', 'YBC/Att', 'YAC', 'YAC/Att', 'BrkTkl', 'Att/Br']
            rushing_columns = [
                'rush_first_downs INTEGER DEFAULT 0',
                'rush_yds_before_contact INTEGER DEFAULT 0', 
                'rush_yds_before_contact_per_att DECIMAL(4,1) DEFAULT 0.0',
                'rush_yds_after_contact INTEGER DEFAULT 0',
                'rush_yds_after_contact_per_att DECIMAL(4,1) DEFAULT 0.0',
                'rush_broken_tackles INTEGER DEFAULT 0',
                'rush_att_per_broken_tackle DECIMAL(4,1) DEFAULT 0.0'
            ]
            
            for column in rushing_columns:
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
            print('\\n✅ Successfully added all advanced rushing columns!')
            
            # Verify columns were added
            cursor.execute('''
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_schema = 'nfl' AND table_name = 'boxscore_player_stats'
                AND column_name LIKE 'rush_%'
                ORDER BY column_name
            ''')
            
            rushing_columns = cursor.fetchall()
            print(f'\\n🔍 VERIFICATION: {len(rushing_columns)} rushing columns now available:')
            
            basic_rushing = []
            advanced_rushing = []
            
            for col_name, data_type in rushing_columns:
                if col_name in ['rush_att', 'rush_yds', 'rush_td', 'rush_long']:
                    basic_rushing.append(f'{col_name} ({data_type})')
                else:
                    advanced_rushing.append(f'{col_name} ({data_type})')
            
            print('\\n📊 BASIC RUSHING COLUMNS:')
            for col in basic_rushing:
                print(f'  • {col}')
            
            print('\\n🏃 ADVANCED RUSHING COLUMNS:')
            for col in advanced_rushing:
                print(f'  • {col}')
            
            print('\\n💡 ADVANCED RUSHING METRICS EXPLAINED:')
            print('  • rush_first_downs: First downs earned via rushing')
            print('  • rush_yds_before_contact: Yards gained before first defender contact')
            print('  • rush_yds_after_contact: Yards gained after contact with defender')
            print('  • rush_broken_tackles: Number of tackles broken on rushing plays')
            print('  • rush_att_per_broken_tackle: How many attempts per broken tackle')

if __name__ == '__main__':
    try:
        add_advanced_rushing_columns()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
