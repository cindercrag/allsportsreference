#!/usr/bin/env python3
"""
Create Advanced Rushing Table
Similar to advanced passing but for rushing analytics
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

print('🏃 CREATING ADVANCED RUSHING TABLE')
print('=' * 40)

def create_advanced_rushing_table():
    """Create dedicated table for advanced rushing metrics"""
    
    with PostgreSQLManager() as db:
        with db._connection.cursor() as cursor:
            
            print('📝 Creating nfl.boxscore_advanced_rushing table...')
            
            # Drop table if exists to start fresh
            cursor.execute('DROP TABLE IF EXISTS nfl.boxscore_advanced_rushing CASCADE')
            print('  🗑️  Dropped existing table if present')
            
            # Create advanced rushing table based on analysis
            # Columns: Player, Tm, Att, Yds, TD, 1D, YBC, YBC/Att, YAC, YAC/Att, BrkTkl, Att/Br
            cursor.execute('''
                CREATE TABLE nfl.boxscore_advanced_rushing (
                    id SERIAL PRIMARY KEY,
                    boxscore_id VARCHAR(20) NOT NULL,
                    player_name VARCHAR(100) NOT NULL,
                    team VARCHAR(10) NOT NULL,
                    
                    -- Basic rushing stats (for reference/validation)
                    rush_att INTEGER DEFAULT 0,
                    rush_yds INTEGER DEFAULT 0, 
                    rush_td INTEGER DEFAULT 0,
                    
                    -- Advanced rushing metrics
                    rush_first_downs INTEGER DEFAULT 0,                    -- 1D column
                    yards_before_contact INTEGER DEFAULT 0,               -- YBC column
                    yards_before_contact_per_att DECIMAL(4,1) DEFAULT 0.0, -- YBC/Att column
                    yards_after_contact INTEGER DEFAULT 0,                -- YAC column
                    yards_after_contact_per_att DECIMAL(4,1) DEFAULT 0.0,  -- YAC/Att column
                    broken_tackles INTEGER DEFAULT 0,                     -- BrkTkl column
                    att_per_broken_tackle DECIMAL(4,1) DEFAULT 0.0,       -- Att/Br column
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            print('  ✅ Created table structure')
            
            # Create indexes for performance
            indexes = [
                'CREATE INDEX idx_adv_rushing_boxscore ON nfl.boxscore_advanced_rushing(boxscore_id)',
                'CREATE INDEX idx_adv_rushing_player ON nfl.boxscore_advanced_rushing(player_name)',
                'CREATE INDEX idx_adv_rushing_team ON nfl.boxscore_advanced_rushing(team)',
                'CREATE INDEX idx_adv_rushing_game_player ON nfl.boxscore_advanced_rushing(boxscore_id, player_name)',
                'CREATE INDEX idx_adv_rushing_ybc ON nfl.boxscore_advanced_rushing(yards_before_contact DESC)',
                'CREATE INDEX idx_adv_rushing_yac ON nfl.boxscore_advanced_rushing(yards_after_contact DESC)',
                'CREATE INDEX idx_adv_rushing_broken_tackles ON nfl.boxscore_advanced_rushing(broken_tackles DESC)'
            ]
            
            for idx_sql in indexes:
                cursor.execute(idx_sql)
                idx_name = idx_sql.split()[2]  # Extract index name
                print(f'  📊 Created index: {idx_name}')
            
            # Add unique constraint to prevent duplicates
            cursor.execute('''
                ALTER TABLE nfl.boxscore_advanced_rushing 
                ADD CONSTRAINT unique_adv_rushing_game_player 
                UNIQUE (boxscore_id, player_name, team)
            ''')
            print('  🔒 Added unique constraint')
            
            db._connection.commit()
            print('\\n✅ Successfully created nfl.boxscore_advanced_rushing table!')
            
            # Show table info
            cursor.execute('''
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_schema = 'nfl' AND table_name = 'boxscore_advanced_rushing'
                ORDER BY ordinal_position
            ''')
            
            columns = cursor.fetchall()
            print(f'\\n📋 TABLE SCHEMA ({len(columns)} columns):')
            
            for col_name, data_type, nullable, default in columns:
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                print(f'  • {col_name:<25} {data_type:<15} {nullable_str}{default_str}')
            
            print('\\n💡 ADVANCED RUSHING METRICS EXPLAINED:')
            print('  • rush_first_downs: First downs earned via rushing plays')
            print('  • yards_before_contact: Yards gained before first defender contact')
            print('  • yards_after_contact: Yards gained after contact with defender') 
            print('  • broken_tackles: Number of tackles broken on rushing attempts')
            print('  • att_per_broken_tackle: Average attempts per broken tackle')
            
            print('\\n🎯 READY FOR DATA EXTRACTION!')
            print('    Next step: Add extract_advanced_rushing_data() to scraper')

if __name__ == '__main__':
    try:
        create_advanced_rushing_table()
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
