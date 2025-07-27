#!/usr/bin/env python3
"""
Example usage of the automated export system for NFL data scraping.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'src'))

from utils.common import (
    export_dataframe_to_csv, 
    export_multiple_dataframes,
    create_export_summary,
    generate_export_filename
)
import pandas as pd

def demonstrate_export_automation():
    """Demonstrate the automated export functionality."""
    
    print("🏈 NFL Data Export Automation Demo")
    print("=" * 50)
    
    # Sample data that would come from scraping
    patriots_schedule = pd.DataFrame({
        'week': [1, 2, 3, 4],
        'date': ['2024-09-08', '2024-09-15', '2024-09-22', '2024-09-29'],
        'opponent': ['CIN', 'SEA', 'NYJ', 'SF'],
        'home_away': ['@', '', '@', ''],
        'result': ['W 16-10', 'W 23-20', 'L 24-3', 'W 30-13']
    })
    
    patriots_roster = pd.DataFrame({
        'player': ['Mac Jones', 'Rhamondre Stevenson', 'DeVante Parker'],
        'position': ['QB', 'RB', 'WR'],
        'number': [10, 38, 1],
        'height': ['6-3', '6-0', '6-3'],
        'weight': [214, 227, 209]
    })
    
    cowboys_schedule = pd.DataFrame({
        'week': [1, 2, 3, 4],
        'date': ['2024-09-08', '2024-09-15', '2024-09-22', '2024-09-29'],
        'opponent': ['CLE', 'NO', 'ARI', 'NE'],
        'home_away': ['', '@', '', '@'],
        'result': ['W 33-17', 'W 44-19', 'W 28-16', 'L 13-30']
    })
    
    # 1. Export individual team data
    print("1. Exporting Patriots data...")
    patriots_files = export_multiple_dataframes({
        'schedule': patriots_schedule,
        'roster': patriots_roster
    }, sport='nfl', season=2024, team='NE')
    
    print("2. Exporting Cowboys data...")
    cowboys_files = export_multiple_dataframes({
        'schedule': cowboys_schedule
    }, sport='nfl', season=2024, team='DAL')
    
    # 3. Create summaries
    print("\n3. Creating export summaries...")
    patriots_summary = create_export_summary(patriots_files, 'nfl', 2024, 'NE')
    cowboys_summary = create_export_summary(cowboys_files, 'nfl', 2024, 'DAL')
    
    # 4. Show what was created
    print("\n4. Directory structure created:")
    os.system("find data -type f | sort")
    
    # 5. Example of different export types
    print("\n5. Example filename patterns:")
    examples = [
        ('nfl', 'schedule', 2024, 'NE', None),
        ('nfl', 'boxscores', 2024, None, 1),
        ('nfl', 'season_stats', 2024, None, None),
        ('nfl', 'draft', 2024, None, None),
        ('nba', 'schedule', 2024, 'LAL', None),
    ]
    
    for sport, data_type, season, team, week in examples:
        filename = generate_export_filename(sport, data_type, season, team, week)
        print(f"   {sport.upper()} {data_type}: {filename}")
    
    print(f"\n✅ Demo complete! Check the 'data' directory for organized exports.")

if __name__ == "__main__":
    demonstrate_export_automation()
