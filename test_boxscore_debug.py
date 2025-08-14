#!/usr/bin/env python3
"""
Test script to debug boxscore extraction for a single game.
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

from nfl_boxscore_scraper import NFLBoxscoreScraper

def main():
    """Test single boxscore extraction"""
    if len(sys.argv) > 1:
        boxscore_id = sys.argv[1]
    else:
        boxscore_id = "202409050kan"  # Test with a specific boxscore
    
    print(f"🔍 Testing boxscore extraction for: {boxscore_id}")
    print("=" * 50)
    
    scraper = NFLBoxscoreScraper()
    
    # Fetch HTML
    soup = scraper.fetch_boxscore_html(boxscore_id)
    if not soup:
        print(f"❌ Failed to fetch HTML for {boxscore_id}")
        return
    
    print("✅ Successfully fetched HTML")
    
    # Check for tables
    print("\n🔍 Looking for tables...")
    player_offense = soup.find('table', {'id': 'player_offense'})
    team_stats = soup.find('table', {'id': 'team_stats'}) 
    scoring = soup.find('table', {'id': 'scoring'})
    
    print(f"  player_offense table: {'✅ Found' if player_offense else '❌ Not found'}")
    print(f"  team_stats table: {'✅ Found' if team_stats else '❌ Not found'}")
    print(f"  scoring table: {'✅ Found' if scoring else '❌ Not found'}")
    
    # List all tables with IDs
    all_tables = soup.find_all('table', {'id': True})
    print(f"\n📊 All tables with IDs found ({len(all_tables)}):")
    for table in all_tables:
        table_id = table.get('id')
        rows = len(table.find_all('tr')) if table.find('tbody') else 0
        print(f"  - {table_id}: {rows} rows")
    
    # Examine player_offense table structure
    if player_offense:
        print(f"\n🔍 player_offense table structure:")
        headers = player_offense.find('thead')
        if headers:
            header_cells = headers.find_all('th')
            header_text = [th.get_text(strip=True) for th in header_cells]
            print(f"  Headers: {header_text}")
        
        tbody = player_offense.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            print(f"  Body rows: {len(rows)}")
            if rows:
                # Show first few rows
                for i, row in enumerate(rows[:3]):
                    cells = row.find_all(['td', 'th'])
                    cell_text = [cell.get_text(strip=True) for cell in cells]
                    print(f"    Row {i}: {cell_text}")

    # Examine team_stats table structure  
    if team_stats:
        print(f"\n🔍 team_stats table structure:")
        headers = team_stats.find('thead')
        if headers:
            header_cells = headers.find_all('th')
            header_text = [th.get_text(strip=True) for th in header_cells]
            print(f"  Headers: {header_text}")
        
        tbody = team_stats.find('tbody')
        if tbody:
            rows = tbody.find_all('tr')
            print(f"  Body rows: {len(rows)}")
            if rows:
                # Show first few rows
                for i, row in enumerate(rows[:3]):
                    cells = row.find_all(['td', 'th'])
                    cell_text = [cell.get_text(strip=True) for cell in cells]
                    print(f"    Row {i}: {cell_text}")

    # Test extraction methods
    print("\n🧪 Testing extraction methods...")
    try:
        player_stats = scraper.extract_player_stats(soup, boxscore_id)
        print(f"  Player stats: {len(player_stats)} records")
        
        team_stats = scraper.extract_team_stats(soup, boxscore_id)
        print(f"  Team stats: {len(team_stats)} records")
        
        scoring_events = scraper.extract_scoring_data(soup, boxscore_id)
        print(f"  Scoring events: {len(scoring_events)} records")
        
        # Show some sample data
        if scoring_events:
            print(f"\n📝 Sample scoring event:")
            event = scoring_events[0]
            print(f"    Quarter: {event.quarter}")
            print(f"    Time: {event.time_remaining}")
            print(f"    Team: {event.team}")
            print(f"    Description: {event.description}")
            print(f"    Score: {event.score_away}-{event.score_home}")
            
    except Exception as e:
        print(f"❌ Error in extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
