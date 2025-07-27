#!/usr/bin/env python3
"""
Complete Workflow Example: CSV Export to PostgreSQL

This example shows the complete data pipeline:
1. Generate sample sports data
2. Export to organized CSV structure
3. Load into PostgreSQL with proper schemas and partitioning
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from utils.common import export_multiple_dataframes, create_export_summary
from utils.database import SportsDatabase, load_csv_files
import pandas as pd
from datetime import datetime, timedelta

def generate_sample_data():
    """Generate sample sports data for demonstration."""
    
    print("📊 Generating Sample Sports Data")
    print("=" * 40)
    
    # NFL Sample Data
    patriots_schedule = pd.DataFrame({
        'week': [1, 2, 3, 4, 5],
        'date': ['2024-09-08', '2024-09-15', '2024-09-22', '2024-09-29', '2024-10-06'],
        'opponent': ['CIN', 'SEA', 'NYJ', 'SF', 'MIA'],
        'home_away': ['@', '', '@', '', ''],
        'result': ['W 16-10', 'W 23-20', 'L 24-3', 'W 30-13', 'W 27-17'],
        'points_scored': [16, 23, 3, 30, 27],
        'points_allowed': [10, 20, 24, 13, 17]
    })
    
    cowboys_schedule = pd.DataFrame({
        'week': [1, 2, 3, 4, 5],
        'date': ['2024-09-08', '2024-09-15', '2024-09-22', '2024-09-29', '2024-10-06'],
        'opponent': ['CLE', 'NO', 'ARI', 'NE', 'PIT'],
        'home_away': ['', '@', '', '@', ''],
        'result': ['W 33-17', 'W 44-19', 'W 28-16', 'L 13-30', 'W 20-17'],
        'points_scored': [33, 44, 28, 13, 20],
        'points_allowed': [17, 19, 16, 30, 17]
    })
    
    # NBA Sample Data
    lakers_schedule = pd.DataFrame({
        'date': ['2024-10-15', '2024-10-17', '2024-10-20', '2024-10-22', '2024-10-25'],
        'opponent': ['DEN', 'PHX', 'SAC', 'MIN', 'CLE'],
        'home_away': ['', '@', '', '@', ''],
        'result': ['W 110-103', 'L 109-114', 'W 123-116', 'W 105-99', 'L 108-112'],
        'points_scored': [110, 109, 123, 105, 108],
        'points_allowed': [103, 114, 116, 99, 112]
    })
    
    warriors_schedule = pd.DataFrame({
        'date': ['2024-10-15', '2024-10-17', '2024-10-20', '2024-10-22', '2024-10-25'],
        'opponent': ['POR', 'UTA', 'LAC', 'LAL', 'NOP'],
        'home_away': ['', '', '@', '', '@'],
        'result': ['W 139-104', 'W 123-116', 'L 112-126', 'W 128-121', 'W 124-106'],
        'points_scored': [139, 123, 112, 128, 124],
        'points_allowed': [104, 116, 126, 121, 106]
    })
    
    return {
        'nfl': {
            'NE': {'schedule': patriots_schedule},
            'DAL': {'schedule': cowboys_schedule}
        },
        'nba': {
            'LAL': {'schedule': lakers_schedule},
            'GSW': {'schedule': warriors_schedule}
        }
    }

def export_sample_data():
    """Export sample data to organized CSV structure."""
    
    print("\n📁 Exporting Data to Organized CSV Structure")
    print("=" * 50)
    
    data = generate_sample_data()
    exported_files = {}
    
    for sport, teams in data.items():
        sport_files = {}
        for team, datasets in teams.items():
            team_files = export_multiple_dataframes(
                datasets, sport=sport, season=2024, team=team
            )
            sport_files.update(team_files)
        exported_files[sport] = sport_files
    
    return exported_files

def demonstrate_database_loading():
    """Demonstrate database loading functionality."""
    
    print("\n🗄️  Database Loading Demonstration")
    print("=" * 40)
    
    print("Note: This demonstrates the database loading process.")
    print("To use with real PostgreSQL:")
    print("1. Install PostgreSQL")
    print("2. Run: createdb sportsdb")
    print("3. Run: psql sportsdb < database_setup.sql")
    print("4. Update connection parameters below")
    print()
    
    # Show how you would load data into PostgreSQL
    print("Database loading code:")
    print("```python")
    print("# Create database connection")
    print("db = SportsDatabase(")
    print("    host='localhost',")
    print("    database='sportsdb',")
    print("    user='postgres',")
    print("    password='your_password'")
    print(")")
    print()
    print("# Load all CSV files from organized structure")
    print("loaded_files = db.load_organized_data('data')")
    print()
    print("# Or load individual files")
    print("db.load_csv_to_table(")
    print("    'data/nfl/2024/teams/NE/NE_2024_schedule.csv',")
    print("    sport='nfl',")
    print("    table_name='schedule',")
    print("    season=2024")
    print(")")
    print("```")
    print()
    
    # Show what the database structure would look like
    print("Expected database structure:")
    print("Database: sportsdb")
    print("├── Schema: nfl")
    print("│   └── Table: schedule")
    print("│       └── Partition: schedule_2024")
    print("│           ├── NE vs CIN (Week 1)")
    print("│           ├── NE vs SEA (Week 2)")
    print("│           ├── DAL vs CLE (Week 1)")
    print("│           └── DAL vs NO (Week 2)")
    print("└── Schema: nba")
    print("    └── Table: schedule")
    print("        └── Partition: schedule_2024")
    print("            ├── LAL vs DEN")
    print("            ├── LAL vs PHX")
    print("            ├── GSW vs POR")
    print("            └── GSW vs UTA")

def show_sample_queries():
    """Show sample SQL queries for the loaded data."""
    
    print("\n🔍 Sample SQL Queries")
    print("=" * 25)
    
    queries = [
        ("Get all NFL Patriots games", 
         "SELECT * FROM nfl.schedule WHERE team = 'NE' AND season = 2024;"),
        
        ("Get all home games for Cowboys",
         "SELECT * FROM nfl.schedule WHERE team = 'DAL' AND home_away = '' AND season = 2024;"),
        
        ("Get all Lakers wins",
         "SELECT * FROM nba.schedule WHERE team = 'LAL' AND result LIKE 'W%' AND season = 2024;"),
        
        ("Get games with more than 120 points scored",
         "SELECT * FROM nba.schedule WHERE points_scored > 120 AND season = 2024;"),
        
        ("Get NFL teams by average points scored",
         """SELECT team, AVG(points_scored) as avg_points
FROM nfl.schedule 
WHERE season = 2024 
GROUP BY team 
ORDER BY avg_points DESC;"""),
        
        ("Get NBA teams by win percentage",
         """SELECT team, 
       COUNT(*) as games_played,
       SUM(CASE WHEN result LIKE 'W%' THEN 1 ELSE 0 END) as wins,
       ROUND(SUM(CASE WHEN result LIKE 'W%' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as win_pct
FROM nba.schedule 
WHERE season = 2024 
GROUP BY team 
ORDER BY win_pct DESC;""")
    ]
    
    for i, (description, query) in enumerate(queries, 1):
        print(f"{i}. {description}:")
        print(f"   {query}")
        print()

def main():
    """Run the complete workflow demonstration."""
    
    print("🏈🏀 Complete Sports Data Pipeline Demo")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Export sample data
    exported_files = export_sample_data()
    
    # Step 2: Show file organization
    print("\n📋 File Organization Summary:")
    print("=" * 35)
    total_files = 0
    for sport, files in exported_files.items():
        print(f"{sport.upper()}: {len(files)} files")
        total_files += len(files)
    print(f"Total: {total_files} files exported")
    
    # Step 3: Demonstrate database loading
    demonstrate_database_loading()
    
    # Step 4: Show sample queries
    show_sample_queries()
    
    print("✅ Complete workflow demonstration finished!")
    print("\nNext steps:")
    print("1. Set up PostgreSQL database")
    print("2. Run database_setup.sql")
    print("3. Update connection parameters")
    print("4. Use load_csv_files('data') to load all data")

if __name__ == "__main__":
    main()
