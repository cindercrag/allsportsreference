#!/usr/bin/env python3
"""
Create Advanced Passing Table
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

print('🎯 CREATING ADVANCED PASSING TABLE')
print('=' * 40)

def create_advanced_passing_table():
    """Create the boxscore_advanced_passing table"""
    
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            print('📝 Creating boxscore_advanced_passing table...')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS nfl.boxscore_advanced_passing (
                    id SERIAL PRIMARY KEY,
                    boxscore_id VARCHAR(12) NOT NULL,
                    player_name VARCHAR(100) NOT NULL,
                    team VARCHAR(3) NOT NULL,
                    
                    -- Basic Completion Stats (for reference/validation)
                    cmp INTEGER DEFAULT 0,
                    att INTEGER DEFAULT 0,
                    yds INTEGER DEFAULT 0,
                    
                    -- First Down Stats
                    first_downs INTEGER DEFAULT 0,
                    first_down_pct DECIMAL(5,1) DEFAULT 0.0,
                    
                    -- Air Yards Analysis
                    intended_air_yards INTEGER DEFAULT 0,
                    intended_air_yards_per_att DECIMAL(4,1) DEFAULT 0.0,
                    completed_air_yards INTEGER DEFAULT 0,
                    completed_air_yards_per_cmp DECIMAL(4,1) DEFAULT 0.0,
                    completed_air_yards_per_att DECIMAL(4,1) DEFAULT 0.0,
                    
                    -- Yards After Catch
                    yac INTEGER DEFAULT 0,
                    yac_per_cmp DECIMAL(4,1) DEFAULT 0.0,
                    
                    -- Accuracy Analysis
                    drops INTEGER DEFAULT 0,
                    drop_pct DECIMAL(5,1) DEFAULT 0.0,
                    bad_throws INTEGER DEFAULT 0,
                    bad_throw_pct DECIMAL(5,1) DEFAULT 0.0,
                    
                    -- Pressure Analysis
                    sacks INTEGER DEFAULT 0,
                    blitzes_faced INTEGER DEFAULT 0,
                    hurries INTEGER DEFAULT 0,
                    hits INTEGER DEFAULT 0,
                    pressures INTEGER DEFAULT 0,
                    pressure_pct DECIMAL(5,1) DEFAULT 0.0,
                    
                    -- Mobility
                    scrambles INTEGER DEFAULT 0,
                    scramble_yards_per_scramble DECIMAL(4,1) DEFAULT 0.0,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Indexes for efficient querying
                    UNIQUE(boxscore_id, player_name, team)
                )
            ''')
            
            # Create indexes
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_adv_passing_boxscore_id 
                ON nfl.boxscore_advanced_passing(boxscore_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_adv_passing_player_team 
                ON nfl.boxscore_advanced_passing(player_name, team)
            ''')
            
            db._connection.commit()
            print('✅ Successfully created boxscore_advanced_passing table!')
            
            # Verify table structure
            cursor.execute('''
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'nfl' AND table_name = 'boxscore_advanced_passing'
                ORDER BY ordinal_position
            ''')
            
            columns = cursor.fetchall()
            print(f'\\n🔍 VERIFICATION: {len(columns)} columns created:')
            
            # Group columns by category
            basic_cols = []
            air_yards_cols = []
            accuracy_cols = []
            pressure_cols = []
            other_cols = []
            
            for col_name, data_type in columns:
                if col_name in ['id', 'boxscore_id', 'player_name', 'team', 'cmp', 'att', 'yds', 'created_at']:
                    basic_cols.append(f'{col_name} ({data_type})')
                elif 'air_yards' in col_name or col_name.startswith('yac'):
                    air_yards_cols.append(f'{col_name} ({data_type})')
                elif col_name in ['drops', 'drop_pct', 'bad_throws', 'bad_throw_pct']:
                    accuracy_cols.append(f'{col_name} ({data_type})')
                elif col_name in ['sacks', 'blitzes_faced', 'hurries', 'hits', 'pressures', 'pressure_pct']:
                    pressure_cols.append(f'{col_name} ({data_type})')
                else:
                    other_cols.append(f'{col_name} ({data_type})')
            
            print('\\n📊 BASIC COLUMNS:')
            for col in basic_cols:
                print(f'  • {col}')
            
            print('\\n🎯 AIR YARDS & YAC:')
            for col in air_yards_cols:
                print(f'  • {col}')
            
            print('\\n🎪 ACCURACY METRICS:')
            for col in accuracy_cols:
                print(f'  • {col}')
            
            print('\\n💥 PRESSURE METRICS:')
            for col in pressure_cols:
                print(f'  • {col}')
            
            print('\\n📈 OTHER METRICS:')
            for col in other_cols:
                print(f'  • {col}')

if __name__ == '__main__':
    try:
        create_advanced_passing_table()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
