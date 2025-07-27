#!/usr/bin/env python3
"""
Database Demo - Shows how to load sports data into PostgreSQL.

This script demonstrates:
- Creating sport schemas (nfl, nba)
- Creating season-partitioned tables
- Loading CSV files from organized structure
- Database connection management
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from utils.database import SportsDatabase, load_csv_files, create_database_config
import pandas as pd

def demo_database_setup():
    """Demonstrate database setup and data loading."""
    
    print("🗄️  Sports Database Demo")
    print("=" * 50)
    
    # Note: This demo shows the functionality without requiring an actual PostgreSQL connection
    print("This demo shows database functionality. To use with real PostgreSQL:")
    print("1. Install PostgreSQL")
    print("2. Create database 'sportsdb'")
    print("3. Update connection parameters")
    print()
    
    # Show configuration
    print("1. Database Configuration:")
    config = create_database_config()
    for key, value in config.items():
        if key == 'password':
            print(f"   {key}: {'*' * len(str(value))}")
        else:
            print(f"   {key}: {value}")
    print()
    
    # Show how to create database instance
    print("2. Database Instance Creation:")
    print("   db = SportsDatabase(host='localhost', database='sportsdb')")
    print()
    
    # Show schema creation
    print("3. Schema Creation Examples:")
    print("   db.create_schema('nfl')  # Creates nfl schema")
    print("   db.create_schema('nba')  # Creates nba schema")
    print()
    
    # Show table creation
    print("4. Partitioned Table Creation:")
    print("   Sample column definitions for schedule table:")
    schedule_columns = {
        'season': 'INTEGER',
        'week': 'INTEGER', 
        'date': 'DATE',
        'team': 'VARCHAR(10)',
        'opponent': 'VARCHAR(10)',
        'home_away': 'VARCHAR(1)',
        'result': 'VARCHAR(20)'
    }
    
    for col, dtype in schedule_columns.items():
        print(f"     {col}: {dtype}")
    print()
    print("   db.create_partitioned_table('nfl', 'schedule', schedule_columns)")
    print("   db.create_season_partition('nfl', 'schedule', 2024)")
    print()
    
    # Show data loading
    print("5. CSV Loading Examples:")
    print("   # Load single file:")
    print("   db.load_csv_to_table('data/nfl/2024/teams/NE/NE_2024_schedule.csv',")
    print("                        sport='nfl', table_name='schedule', season=2024)")
    print()
    print("   # Load all organized files:")
    print("   load_csv_files('data')")
    print()
    
    # Show expected database structure
    print("6. Expected Database Structure:")
    print("   Database: sportsdb")
    print("   ├── Schema: nfl")
    print("   │   ├── Table: schedule (partitioned by season)")
    print("   │   │   ├── schedule_2024 (partition)")
    print("   │   │   └── schedule_2025 (partition)")
    print("   │   └── Table: roster (partitioned by season)")
    print("   │       ├── roster_2024 (partition)")
    print("   │       └── roster_2025 (partition)")
    print("   └── Schema: nba")
    print("       ├── Table: schedule (partitioned by season)")
    print("       └── Table: roster (partitioned by season)")
    print()
    
    # Show benefits
    print("7. Benefits of This Structure:")
    print("   ✅ Sport isolation with schemas")
    print("   ✅ Season-based partitioning for performance")
    print("   ✅ Automatic table creation from CSV structure")
    print("   ✅ Bulk loading of organized file structure")
    print("   ✅ Type inference from pandas DataFrames")
    print()
    
    # Show sample queries
    print("8. Sample SQL Queries:")
    print("   -- Get all NFL 2024 schedule data")
    print("   SELECT * FROM nfl.schedule WHERE season = 2024;")
    print()
    print("   -- Get Patriots home games")
    print("   SELECT * FROM nfl.schedule WHERE team = 'NE' AND home_away = '';")
    print()
    print("   -- Get all NBA Lakers data")
    print("   SELECT * FROM nba.schedule WHERE team = 'LAL';")
    print()
    
    # Show file mapping
    print("9. File to Table Mapping:")
    if os.path.exists('data'):
        for root, dirs, files in os.walk('data'):
            for file in files:
                if file.endswith('.csv'):
                    file_path = os.path.join(root, file)
                    path_parts = os.path.relpath(file_path, 'data').split(os.sep)
                    
                    if len(path_parts) >= 3:
                        sport = path_parts[0]
                        season = path_parts[1]
                        filename_parts = file.replace('.csv', '').split('_')
                        if len(filename_parts) >= 3:
                            table_name = '_'.join(filename_parts[2:])
                        else:
                            table_name = filename_parts[-1] if filename_parts else 'unknown'
                        
                        print(f"   {file_path}")
                        print(f"     → {sport}.{table_name}_{season}")
    else:
        print("   No data directory found. Run export examples first.")
    
    print()
    print("✅ Database demo complete!")

if __name__ == "__main__":
    demo_database_setup()
